const path = require('path');
const fs = require('fs');
const crypto = require('crypto');
require('dotenv').config({ path: path.join(__dirname, '.env') });

const express = require('express');
const cors = require('cors');
const multer = require('multer');
const { S3Client, PutObjectCommand, DeleteObjectCommand, GetObjectCommand, ListObjectsV2Command } = require('@aws-sdk/client-s3');
const { DynamoDBClient } = require('@aws-sdk/client-dynamodb');
const {
    DynamoDBDocumentClient, GetCommand, PutCommand, UpdateCommand, DeleteCommand, QueryCommand, BatchWriteCommand
} = require('@aws-sdk/lib-dynamodb');

const app = express();
app.use(cors());
app.use(express.json());

// ==========================================
// Role based access (see use case diagram): each role reaches a different set of pages.
//   Data Admin              -> upload page only (login, upload dataset, check load errors)
//   Executive / Data Analyst -> dashboard + AI agent
// Page content is unchanged; only which pages/APIs a role may open.
// ==========================================
const ANALYST_ACCESS = {
    home: '/dashboard.html',
    pages: ['/dashboard.html', '/agent.html'],
    api: ['/dashboard', '/dashboard-data', '/chat', '/ai']
};
const ROLE_ACCESS = {
    'Data Admin': {
        home: '/inventory.html',
        pages: ['/inventory.html'],
        api: ['/upload', '/uploads', '/file-content', '/delete']
    },
    'Executive': ANALYST_ACCESS,
    'Data Analyst': ANALYST_ACCESS
};
const ROLE_ALIAS = { 'Admin': 'Data Admin' }; // role written by the first deploy's seed user
const ALWAYS_API = ['/me'];

// DynamoDB items are typed by hand, so tolerate stray spaces and letter case in the role value
const normalizeRole = (role) => String(role || '').trim().replace(/\s+/g, ' ').toLowerCase();
const ROLE_LOOKUP = new Map(Object.entries(ROLE_ACCESS).map(([k, v]) => [normalizeRole(k), v]));
Object.entries(ROLE_ALIAS).forEach(([k, v]) => ROLE_LOOKUP.set(normalizeRole(k), ROLE_ACCESS[v]));

function accessFor(role) {
    return ROLE_LOOKUP.get(normalizeRole(role)) || ANALYST_ACCESS;
}
const underPrefix = (p, list) => list.some((x) => p === x || p.startsWith(x + '/'));

// HTML pages: no session -> login page; wrong role -> that role's own home page
app.use(async (req, res, next) => {
    if (req.method !== 'GET') return next();
    const pagePath = req.path === '/dashboard' ? '/dashboard.html' : req.path;
    if (!['/dashboard.html', '/inventory.html', '/agent.html'].includes(pagePath)) return next();
    try {
        const session = await loadSession(req);
        if (!session) return res.redirect('/index.html');
        const access = accessFor(session.role);
        if (!access.pages.includes(pagePath)) return res.redirect(access.home);
        if (req.path !== pagePath) return res.redirect(pagePath);
        next();
    } catch (err) {
        console.error('Page access check error:', err);
        res.status(500).send('ตรวจสอบสิทธิ์ไม่สำเร็จ');
    }
});

// ดึงไฟล์ HTML ในโฟลเดอร์ frontend หรือ public มาแสดงผล
const staticDir = fs.existsSync(path.join(__dirname, 'frontend')) ? 'frontend' : 'public';
app.use(express.static(staticDir));
if (staticDir !== 'public' && fs.existsSync(path.join(__dirname, 'public'))) {
    app.use(express.static('public'));
}

// ==========================================
// ตั้งค่า AWS Clients (รองรับทั้ง Credentials จาก .env และ IAM Role บน EC2)
// ==========================================
const awsConfig = {
    region: process.env.AWS_REGION || 'us-east-1'
};

if (process.env.AWS_ACCESS_KEY_ID && process.env.AWS_SECRET_ACCESS_KEY) {
    awsConfig.credentials = {
        accessKeyId: process.env.AWS_ACCESS_KEY_ID.trim(),
        secretAccessKey: process.env.AWS_SECRET_ACCESS_KEY.trim()
    };
    if (process.env.AWS_SESSION_TOKEN) {
        awsConfig.credentials.sessionToken = process.env.AWS_SESSION_TOKEN.trim();
    }
}

const s3Client = new S3Client(awsConfig);
const dbClient = new DynamoDBClient(awsConfig);
const docClient = DynamoDBDocumentClient.from(dbClient, { marshallOptions: { removeUndefinedValues: true } });

const upload = multer({ storage: multer.memoryStorage() });

// ==========================================
// Stateless design: this server runs on several EC2 instances behind the ALB
// (Auto Scaling group), so nothing is kept in process memory.
//   - login + sessions + chat history -> DynamoDB
//   - uploaded file list              -> S3
// ==========================================
const USER_TABLE = process.env.DYNAMODB_TABLE || 'user_login';
const SESSION_TABLE = process.env.SESSION_TABLE || 'user_session';
const CHAT_TABLE = process.env.CHAT_TABLE || 'chat_history';
const AI_BACKEND_URL = process.env.AI_BACKEND_URL || 'http://127.0.0.1:8000';
const CSV_PREFIX = 'csv-uploads/';
const SESSION_COOKIE = 'agri_session';
const SESSION_TTL_SECONDS = 8 * 60 * 60;
// Changes only when the stack is redeployed (frontend clears its cache when it changes)
const DEPLOY_ID = process.env.DEPLOY_ID || 'local';

// ---- password hashing (format shared with lambda/etl: scrypt$N$r$p$saltHex$hashHex)
function hashPassword(password) {
    const salt = crypto.randomBytes(16);
    const hash = crypto.scryptSync(password, salt, 64, { N: 16384, r: 8, p: 1 });
    return `scrypt$16384$8$1$${salt.toString('hex')}$${hash.toString('hex')}`;
}

function verifyPassword(stored, supplied) {
    if (typeof stored !== 'string' || typeof supplied !== 'string') return false;
    if (stored.startsWith('scrypt$')) {
        const [, N, r, p, saltHex, hashHex] = stored.split('$');
        const expected = Buffer.from(hashHex, 'hex');
        const actual = crypto.scryptSync(supplied, Buffer.from(saltHex, 'hex'), expected.length,
            { N: Number(N), r: Number(r), p: Number(p) });
        return crypto.timingSafeEqual(actual, expected);
    }
    // legacy plaintext record (upgraded to a hash on next successful login)
    const digest = (s) => crypto.createHash('sha256').update(s).digest();
    return crypto.timingSafeEqual(digest(stored), digest(supplied));
}

// ---- session helpers
function getCookie(req, name) {
    const part = (req.headers.cookie || '').split(/;\s*/).find((c) => c.startsWith(name + '='));
    return part ? decodeURIComponent(part.slice(name.length + 1)) : null;
}

async function createSession(user) {
    const token = crypto.randomBytes(32).toString('hex');
    await docClient.send(new PutCommand({
        TableName: SESSION_TABLE,
        Item: {
            token,
            username: user.username,
            name: user.name,
            role: user.role,
            createdAt: new Date().toISOString(),
            expiresAt: Math.floor(Date.now() / 1000) + SESSION_TTL_SECONDS // DynamoDB TTL attribute
        }
    }));
    return token;
}

async function loadSession(req) {
    const token = getCookie(req, SESSION_COOKIE);
    if (!token) return null;
    const { Item } = await docClient.send(new GetCommand({ TableName: SESSION_TABLE, Key: { token } }));
    // TTL deletion can lag by hours, so also check expiry here
    if (!Item || Item.expiresAt < Math.floor(Date.now() / 1000)) return null;
    return Item;
}

// ELB health check (no auth). Reports the local AI agent state without failing on it.
app.get('/healthz', async (req, res) => {
    let ai = 'down';
    try {
        const r = await fetch(`${AI_BACKEND_URL}/health`, { signal: AbortSignal.timeout(2000) });
        ai = r.ok ? 'ok' : 'error';
    } catch (e) { /* AI agent still starting */ }
    res.json({ status: 'ok', ai });
});

// Every /api route except login/register requires a valid DynamoDB-backed session ("Verify Auth")
const PUBLIC_API = new Set(['/login', '/register', '/session-info', '/logout']);
app.use('/api', async (req, res, next) => {
    if (PUBLIC_API.has(req.path)) return next();
    try {
        const session = await loadSession(req);
        if (!session) return res.status(401).json({ success: false, message: 'กรุณาเข้าสู่ระบบ' });
        req.user = session;
        const access = accessFor(session.role);
        if (!underPrefix(req.path, [...ALWAYS_API, ...access.api])) {
            return res.status(403).json({ success: false, message: 'บทบาทของคุณไม่มีสิทธิ์ใช้งานส่วนนี้' });
        }
        next();
    } catch (err) {
        console.error('Session verification error:', err);
        res.status(500).json({ success: false, message: 'ตรวจสอบสิทธิ์ผ่าน DynamoDB ไม่สำเร็จ: ' + err.message });
    }
});

// Endpoint สำหรับเช็คสถานะเซิร์ฟเวอร์ (frontend ล้างแคชเมื่อ deploy ใหม่)
app.get('/api/session-info', (req, res) => {
    res.json({ success: true, serverInstanceId: DEPLOY_ID });
});

app.post('/api/logout', async (req, res) => {
    const token = getCookie(req, SESSION_COOKIE);
    try {
        if (token) await docClient.send(new DeleteCommand({ TableName: SESSION_TABLE, Key: { token } }));
    } catch (err) {
        console.error('Logout error:', err);
    }
    res.setHeader('Set-Cookie', `${SESSION_COOKIE}=; Path=/; HttpOnly; SameSite=Lax; Max-Age=0`);
    res.json({ success: true });
});

app.get('/api/me', (req, res) => {
    res.json({ success: true, user: { username: req.user.username, name: req.user.name, role: req.user.role } });
});

// ---- S3 upload list (replaces the old per-process array)
const formatSize = (bytes) => (bytes / (1024 * 1024) >= 1)
    ? (bytes / (1024 * 1024)).toFixed(1) + ' MB'
    : (bytes / 1024).toFixed(1) + ' KB';

const formatTime = (date) => date.toLocaleTimeString('en-GB',
    { hour: '2-digit', minute: '2-digit', hour12: false, timeZone: 'Asia/Bangkok' });

async function listUploadedFiles() {
    const out = await s3Client.send(new ListObjectsV2Command({
        Bucket: process.env.S3_BUCKET_NAME,
        Prefix: CSV_PREFIX
    }));
    return (out.Contents || [])
        .filter((o) => o.Key.toLowerCase().endsWith('.csv'))
        .sort((a, b) => b.LastModified - a.LastModified)
        .slice(0, 100)
        .map((o) => ({
            name: o.Key.slice(CSV_PREFIX.length).replace(/^\d+_/, ''),
            key: o.Key,
            size: formatSize(o.Size),
            time: formatTime(o.LastModified),
            status: 'success'
        }));
}

// ---- chat history in DynamoDB (partition: username, sort: ts)
async function saveChat(username, record) {
    await docClient.send(new PutCommand({ TableName: CHAT_TABLE, Item: { username, ts: record.id, ...record } }));
}

async function loadChat(username, limit = 100) {
    const out = await docClient.send(new QueryCommand({
        TableName: CHAT_TABLE,
        KeyConditionExpression: 'username = :u',
        ExpressionAttributeValues: { ':u': username },
        ScanIndexForward: false,
        Limit: limit
    }));
    return (out.Items || []).reverse().map(({ username: _u, ts: _t, ...rest }) => rest);
}

async function clearChat(username) {
    let lastKey;
    do {
        const page = await docClient.send(new QueryCommand({
            TableName: CHAT_TABLE,
            KeyConditionExpression: 'username = :u',
            ExpressionAttributeValues: { ':u': username },
            ProjectionExpression: 'username, ts',
            ExclusiveStartKey: lastKey
        }));
        const items = page.Items || [];
        for (let i = 0; i < items.length; i += 25) {
            await docClient.send(new BatchWriteCommand({
                RequestItems: {
                    [CHAT_TABLE]: items.slice(i, i + 25).map((Key) => ({ DeleteRequest: { Key } }))
                }
            }));
        }
        lastKey = page.LastEvaluatedKey;
    } while (lastKey);
}

// Helper function เปลี่ยน S3 Body Stream เป็น Text
const streamToString = (stream) =>
    new Promise((resolve, reject) => {
        const chunks = [];
        stream.on('data', (chunk) => chunks.push(chunk));
        stream.on('error', reject);
        stream.on('end', () => resolve(Buffer.concat(chunks).toString('utf-8')));
    });

// ==========================================
// API 1: ตรวจสอบ Login จาก DynamoDB
// ==========================================
app.post('/api/login', async (req, res) => {
    const rawUsername = req.body.username || req.body.email;
    const password = req.body.password;

    if (!rawUsername || !password) {
        return res.status(400).json({ success: false, message: 'กรุณากรอกชื่อผู้ใช้งานและรหัสผ่าน' });
    }

    const cleanUsername = rawUsername.toLowerCase().trim();

    try {
        const command = new GetCommand({
            TableName: USER_TABLE,
            Key: { username: cleanUsername }
        });

        const response = await docClient.send(command);

        if (!response.Item) {
            return res.status(401).json({ success: false, message: 'ไม่พบชื่อผู้ใช้งานนี้' });
        }

        if (verifyPassword(response.Item.password, password)) {
            if (!response.Item.password.startsWith('scrypt$')) {
                await docClient.send(new UpdateCommand({
                    TableName: USER_TABLE,
                    Key: { username: cleanUsername },
                    UpdateExpression: 'SET password = :p',
                    ExpressionAttributeValues: { ':p': hashPassword(password) }
                }));
            }

            const user = {
                username: response.Item.username,
                name: response.Item.name || response.Item.username,
                role: response.Item.role || 'User'
            };
            const token = await createSession(user);
            res.setHeader('Set-Cookie',
                `${SESSION_COOKIE}=${token}; Path=/; HttpOnly; SameSite=Lax; Max-Age=${SESSION_TTL_SECONDS}`);
            res.json({ success: true, user });
        } else {
            res.status(401).json({ success: false, message: 'รหัสผ่านไม่ถูกต้อง' });
        }
    } catch (err) {
        console.error('DynamoDB Error:', err);
        res.status(500).json({ success: false, message: 'ไม่สามารถเชื่อมต่อ DynamoDB ได้: ' + err.message });
    }
});

// ==========================================
// API 2: ลงทะเบียนผู้ใช้ใหม่ลง DynamoDB
// ==========================================
app.post('/api/register', async (req, res) => {
    const { email, password, name, role } = req.body;

    if (!email || !password || !name || !role) {
        return res.status(400).json({ success: false, message: 'กรุณากรอกข้อมูลให้ครบถ้วน' });
    }

    try {
        const checkCommand = new GetCommand({
            TableName: USER_TABLE,
            Key: { username: email.toLowerCase().trim() }
        });
        const existingUser = await docClient.send(checkCommand);

        if (existingUser.Item) {
            return res.status(400).json({ success: false, message: 'อีเมลนี้มีบัญชีในระบบอยู่แล้ว' });
        }

        const putCommand = new PutCommand({
            TableName: USER_TABLE,
            Item: {
                username: email.toLowerCase().trim(),
                password: hashPassword(password),
                name: name.trim(),
                role: role,
                createdAt: new Date().toISOString()
            },
            ConditionExpression: 'attribute_not_exists(username)'
        });

        await docClient.send(putCommand);
        res.json({ success: true, message: 'สร้างบัญชีผู้ใช้เรียบร้อยแล้ว' });

    } catch (err) {
        console.error('DynamoDB Register Error:', err);
        res.status(500).json({ success: false, message: 'เกิดข้อผิดพลาดในการสร้างบัญชี: ' + err.message });
    }
});

// ==========================================
// API 3: อัปโหลด CSV ลง S3 Bucket
// ==========================================
app.post('/api/upload', upload.single('file'), async (req, res) => {
    if (!req.file) return res.status(400).json({ message: 'กรุณาเลือกไฟล์' });

    if (!req.file.originalname.toLowerCase().endsWith('.csv')) {
        return res.status(400).json({ success: false, message: 'รองรับเฉพาะไฟล์ .csv' });
    }

    const params = {
        Bucket: process.env.S3_BUCKET_NAME,
        Key: `${CSV_PREFIX}${Date.now()}_${req.file.originalname}`,
        Body: req.file.buffer,
        ContentType: 'text/csv'
    };

    try {
        // The S3 "Object Created" event (EventBridge) starts the Step Functions ETL automatically
        await s3Client.send(new PutObjectCommand(params));

        const fileItem = {
            name: req.file.originalname,
            key: params.Key,
            size: formatSize(req.file.size),
            time: formatTime(new Date()),
            status: 'success'
        };

        res.json({ success: true, filename: req.file.originalname, key: params.Key, file: fileItem });
    } catch (err) {
        console.error('S3 Upload Error:', err);
        res.status(500).json({ success: false, message: 'อัปโหลดลง S3 ล้มเหลว: ' + err.message });
    }
});

// ดึงรายการไฟล์ที่อัปโหลดไว้ (อ่านจาก S3 โดยตรง)
app.get('/api/uploads', async (req, res) => {
    try {
        res.json({ success: true, files: await listUploadedFiles() });
    } catch (err) {
        console.error('S3 List Error:', err);
        res.status(500).json({ success: false, message: 'ไม่สามารถอ่านรายการไฟล์จาก S3 ได้: ' + err.message });
    }
});

// ==========================================
// API 4: อ่านเนื้อหาไฟล์ CSV จาก S3 มาแสดงผล
// ==========================================
app.get('/api/file-content', async (req, res) => {
    const { key } = req.query;

    if (!key) {
        return res.status(400).json({ success: false, message: 'กรุณาระบุ S3 Key' });
    }

    try {
        const command = new GetObjectCommand({
            Bucket: process.env.S3_BUCKET_NAME,
            Key: key
        });

        const response = await s3Client.send(command);
        const csvContent = await streamToString(response.Body);

        res.setHeader('Content-Type', 'text/csv; charset=utf-8');
        res.send(csvContent);
    } catch (err) {
        console.error('S3 Get Content Error:', err);
        res.status(500).json({ success: false, message: 'ไม่สามารถอ่านข้อมูลไฟล์จาก S3 ได้: ' + err.message });
    }
});

// ==========================================
// API 5: ลบไฟล์ออกจาก S3
// ==========================================
app.delete('/api/delete', async (req, res) => {
    const { key } = req.body;

    if (!key) {
        return res.status(400).json({ success: false, message: 'กรุณาระบุ S3 Key ที่ต้องการลบ' });
    }

    const params = {
        Bucket: process.env.S3_BUCKET_NAME,
        Key: key
    };

    try {
        await s3Client.send(new DeleteObjectCommand(params));
        res.json({ success: true, message: 'ลบไฟล์ออกจาก S3 เรียบร้อยแล้ว' });
    } catch (err) {
        console.error('S3 Delete Error:', err);
        res.status(500).json({ success: false, message: 'ไม่สามารถลบไฟล์จาก S3 ได้: ' + err.message });
    }
});

// ==========================================
// API 6: เชื่อมต่อ AI Backend (รองรับทั้ง /api/chat และ /api/ai/ask)
// ==========================================
const handleAIChat = async (req, res) => {
    try {
        const question = req.body.question || req.body.message;
        const user_role = req.body.user_role || 'analyst';

        if (!question) {
            return res.status(400).json({ success: false, message: 'กรุณากรอกคำถาม' });
        }

        const cloudResponse = await fetch(`${AI_BACKEND_URL}/ask`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                question: question,
                user_role: user_role
            })
        });

        if (!cloudResponse.ok) {
            const errorText = await cloudResponse.text();
            throw new Error(`CLOUD Error (${cloudResponse.status}): ${errorText}`);
        }

        const data = await cloudResponse.json();

        const chatRecord = {
            id: Date.now(),
            question: question,
            answer: data.answer || data.reply,
            sql: data.sql,
            sources: data.sources,
            visualization: data.visualization,
            status: data.status,
            timestamp: new Date().toISOString()
        };
        try {
            await saveChat(req.user.username, chatRecord);
        } catch (err) {
            console.error('Chat history save failed (answer still returned):', err.message);
        }

        res.json({
            success: true,
            reply: data.answer,
            answer: data.answer,
            sql: data.sql,
            sources: data.sources,
            visualization: data.visualization,
            status: data.status
        });

    } catch (error) {
        console.error('Proxy to CLOUD error:', error.message);
        res.status(500).json({
            success: false,
            message: 'ไม่สามารถเชื่อมต่อระบบ AI Backend (CLOUD) ได้: ' + error.message,
            reply: 'เกิดข้อผิดพลาดในการเชื่อมต่อกับเซิร์ฟเวอร์ AI (กรุณาตรวจสอบว่า FastAPI ที่ Port 8000 เปิดใช้งานอยู่หรือไม่)'
        });
    }
};

app.post('/api/ai/ask', handleAIChat);
app.post('/api/chat', handleAIChat);

// ดึงประวัติการแชตกับ AI ของผู้ใช้ที่ล็อกอิน (DynamoDB)
app.get('/api/chat/history', async (req, res) => {
    try {
        res.json({ success: true, history: await loadChat(req.user.username) });
    } catch (err) {
        console.error('Chat history load error:', err);
        res.status(500).json({ success: false, message: 'ไม่สามารถอ่านประวัติการคุยได้: ' + err.message });
    }
});

// ล้างประวัติการแชต
app.delete('/api/chat/history', async (req, res) => {
    try {
        await clearChat(req.user.username);
        res.json({ success: true, message: 'ล้างประวัติการคุยเรียบร้อยแล้ว' });
    } catch (err) {
        console.error('Chat history clear error:', err);
        res.status(500).json({ success: false, message: 'ไม่สามารถล้างประวัติการคุยได้: ' + err.message });
    }
});

// ==========================================
// API เพิ่มเติม: ดึงและประมวลผลข้อมูล CSV จาก S3 สำหรับ Dashboard
// ==========================================
app.get('/api/dashboard-data', async (req, res) => {
    try {
        // ค้นหาไฟล์ CSV ล่าสุดใน S3
        const uploadedFiles = await listUploadedFiles();
        if (uploadedFiles.length === 0) {
            return res.status(404).json({ success: false, message: 'ยังไม่มีไฟล์ CSV ในระบบ' });
        }

        const latestFile = uploadedFiles[0]; // ดึงไฟล์ล่าสุด

        // อ่านไฟล์จาก S3
        const command = new GetObjectCommand({
            Bucket: process.env.S3_BUCKET_NAME,
            Key: latestFile.key
        });
        const response = await s3Client.send(command);
        const csvContent = await streamToString(response.Body);

        // แปลงข้อมูล CSV ข้อความให้เป็น JSON Structure เพื่อส่งให้ Dashboard
        const rows = csvContent.split('\n').map(row => row.split(','));
        const headers = rows[0];

        res.json({
            success: true,
            fileName: latestFile.name,
            totalRows: rows.length - 1,
            headers: headers,
            sampleData: rows.slice(1, 10) // ตัวอย่างข้อมูล 10 แถวแรก
        });
    } catch (err) {
        console.error('Dashboard Data Error:', err);
        res.status(500).json({ success: false, message: 'เกิดข้อผิดพลาดในการดึงข้อมูล Dashboard: ' + err.message });
    }
});

// ==========================================
// API 7: ดึงข้อมูลจาก Redshift Data Warehouse พร้อมระบบตัวกรอง (Filters)
// ==========================================
const { Pool } = require('pg');

// Same schema the Lambda ETL loads and the AI agent queries
const DB_SCHEMA = process.env.DB_SCHEMA || process.env.DATABASE_SCHEMA || 'public';
if (!/^[a-z_][a-z0-9_]*$/i.test(DB_SCHEMA)) throw new Error('Invalid DB_SCHEMA: ' + DB_SCHEMA);

// Redshift is private to the VPC; SSL is used but the AWS CA is not pinned (only this pool, not the AWS SDK)
const pool = process.env.DATABASE_URL
    ? new Pool({
        connectionString: process.env.DATABASE_URL
            .replace('postgresql+psycopg://', 'postgresql://')
            .replace(/\?sslmode=require$/, ''),
        ssl: { rejectUnauthorized: false },
        max: 5,
        connectionTimeoutMillis: 5000
    })
    : null;

app.get('/api/dashboard', async (req, res) => {
    if (!pool) {
        return res.status(503).json({ success: false, message: 'ยังไม่ได้ตั้งค่า DATABASE_URL' });
    }
    try {
        // 1. รับค่าตัวกรองจากหน้าเว็บ
        const { date, warehouse, crop } = req.query;

        // 2. ฟังก์ชันสร้างเงื่อนไข WHERE แบบไดนามิก รองรับทุกตัวกรอง
        const buildWhereClause = (dateColumn, tableAlias = '') => {
            let conditions = [];
            const prefix = tableAlias ? `${tableAlias}.` : ''; // ป้องกันชื่อคอลัมน์ซ้ำตอน JOIN ตาราง

            // ตัวกรองที่ 1: หมวดหมู่ผลผลิต
            if (crop && crop !== 'all') {
                const catTh = crop === 'grain' ? 'ธัญพืช' : (crop === 'fruit' ? 'ผลไม้' : 'ผัก');
                conditions.push(`${prefix}crop_sk IN (SELECT crop_sk FROM ${DB_SCHEMA}.dim_crop WHERE category = '${catTh}')`);
            }

            // ตัวกรองที่ 2: คลังสินค้า (ถ้ามีตัวเลือกเพิ่มในอนาคต โค้ดนี้ก็พร้อมทำงาน)
            if (warehouse && warehouse !== 'all' && /^[A-Za-z0-9_-]+$/.test(warehouse)) {
                conditions.push(`${prefix}warehouse_sk IN (SELECT warehouse_sk FROM ${DB_SCHEMA}.dim_warehouse WHERE warehouse_id = '${warehouse}')`);
            }

            // ตัวกรองที่ 3: ช่วงเวลา 
            // :bulb: แก้ไข: จำลองวันที่ปัจจุบันเป็น 2025-12-31 เพื่อให้ตรงกับข้อมูลชุดสุดท้ายที่มีในฐานข้อมูล
            const mockToday = "'2025-12-31'::date";

            if (date === 'month') {
                conditions.push(`${prefix}${dateColumn} IN (SELECT date_key FROM ${DB_SCHEMA}.dim_date WHERE month = EXTRACT(MONTH FROM ${mockToday}) AND year = EXTRACT(YEAR FROM ${mockToday}))`);
            } else if (date === 'quarter') {
                conditions.push(`${prefix}${dateColumn} IN (SELECT date_key FROM ${DB_SCHEMA}.dim_date WHERE quarter = EXTRACT(QUARTER FROM ${mockToday}) AND year = EXTRACT(YEAR FROM ${mockToday}))`);
            } else if (date === 'year') {
                conditions.push(`${prefix}${dateColumn} IN (SELECT date_key FROM ${DB_SCHEMA}.dim_date WHERE year = EXTRACT(YEAR FROM ${mockToday}))`);
            }

            return conditions.length > 0 ? "WHERE " + conditions.join(" AND ") : "";
        };

        // 3. นำเงื่อนไขไปเสียบใน Query ของแต่ละตาราง (Fact Tables)
        const harvestWhere = buildWhereClause('harvest_date_key');
        const harvestWhereAlias = buildWhereClause('harvest_date_key', 'h'); 
        const salesWhere = buildWhereClause('sale_date_key');
        const shipWhere = buildWhereClause('shipment_date_key');

        const harvestKpi = await pool.query(`
            SELECT 
                COALESCE(SUM(total_amount_thb), 0) AS amount, 
                COALESCE(SUM(quantity_kg), 0) / 1000 AS qty_ton, 
                COALESCE(AVG(price_per_kg), 0) AS avg_price 
            FROM ${DB_SCHEMA}.fact_harvest
            ${harvestWhere}
        `);

        const cropQuery = await pool.query(`
            SELECT c.crop_name, COALESCE(SUM(h.quantity_kg), 0) / 1000 AS qty_ton
            FROM ${DB_SCHEMA}.fact_harvest h
            JOIN ${DB_SCHEMA}.dim_crop c ON h.crop_sk = c.crop_sk
            ${harvestWhereAlias} 
            GROUP BY c.crop_name
        `);
        let cropData = {};
        cropQuery.rows.forEach(r => cropData[r.crop_name] = Number(r.qty_ton));

        const salesKpi = await pool.query(`
            SELECT 
                COALESCE(SUM(total_amount_thb), 0) AS amount, 
                COALESCE(SUM(quantity_kg), 0) / 1000 AS qty_ton 
            FROM ${DB_SCHEMA}.fact_sales
            ${salesWhere}
        `);

        const shipKpi = await pool.query(`
            SELECT COALESCE(SUM(shipping_cost_thb), 0) AS shipping 
            FROM ${DB_SCHEMA}.fact_shipment
            ${shipWhere}
        `);

        // 4. ส่งข้อมูลกลับไปให้หน้า Dashboard
        res.json({
            harvest: {
                amount: Number(harvestKpi.rows[0].amount),
                quantity: Number(harvestKpi.rows[0].qty_ton),
                avgPrice: Number(harvestKpi.rows[0].avg_price),
                months: ["ม.ค.", "ก.พ.", "มี.ค.", "เม.ย.", "พ.ค.", "มิ.ย."],
                trend: [0, 0, 0, 0, Number(harvestKpi.rows[0].qty_ton) * 0.4, Number(harvestKpi.rows[0].qty_ton) * 0.6],
                crops: Object.keys(cropData).length > 0 ? cropData : { "ไม่มีข้อมูลในเงื่อนไขนี้": 0 },
                cooperatives: { "สหกรณ์ A": 310, "สหกรณ์ B": 275, "สหกรณ์ C": 220 }
            },
            sales: {
                amount: Number(salesKpi.rows[0].amount),
                quantity: Number(salesKpi.rows[0].qty_ton),
                shipping: Number(shipKpi.rows[0].shipping),
                months: ["ม.ค.", "ก.พ.", "มี.ค.", "เม.ย.", "พ.ค.", "มิ.ย."],
                trend: [0, 0, 0, 0, Number(salesKpi.rows[0].qty_ton) * 0.4, Number(salesKpi.rows[0].qty_ton) * 0.6],
                customers: { "ห้างค้าปลีก": 42, "ตลาดส่งออก": 33, "สหกรณ์เครือข่าย": 25 },
                shipment: {
                    modes: ["รถยนต์", "เรือ"],
                    completed: [62, 24],
                    pending: [15, 8]
                }
            }
        });
    } catch (err) {
        console.error('RDS Database Error:', err);
        res.status(500).json({ success: false, message: 'ไม่สามารถดึงข้อมูลได้: ' + err.message });
    }
});

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
    console.log(`✅ Server รันเรียบร้อยแล้วที่ http://localhost:${PORT}`);
});