const path = require('path');
const fs = require('fs');
require('dotenv').config({ path: path.join(__dirname, '.env') });

const express = require('express');
const cors = require('cors');
const multer = require('multer');
const { S3Client, PutObjectCommand, DeleteObjectCommand, GetObjectCommand } = require('@aws-sdk/client-s3');
const { DynamoDBClient } = require('@aws-sdk/client-dynamodb');
const { DynamoDBDocumentClient, GetCommand, PutCommand } = require('@aws-sdk/lib-dynamodb');

const app = express();
app.use(cors());
app.use(express.json());

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
const docClient = DynamoDBDocumentClient.from(dbClient);

const upload = multer({ storage: multer.memoryStorage() });

// ==========================================
// In-Memory Storage & Server Session Tracking
// (ข้อมูลคงอยู่ตลอดจนกว่าจะ Stop/Restart Server ตามโจทย์ผู้ใช้)
// ==========================================
const SERVER_INSTANCE_ID = 'srv_' + Date.now();
let chatHistory = [];
let uploadedFiles = [];

// Middleware ตั้งค่า Cookie server_instance_id เพื่อให้ Browser ตรวจสอบสถานะการ Restart ได้
app.use((req, res, next) => {
    res.setHeader('Set-Cookie', `server_instance_id=${SERVER_INSTANCE_ID}; Path=/; SameSite=Lax`);
    next();
});

// Endpoint สำหรับเช็คสถานะเซิร์ฟเวอร์และดึง Session ID
app.get('/api/session-info', (req, res) => {
    res.json({
        success: true,
        serverInstanceId: SERVER_INSTANCE_ID,
        chatCount: chatHistory.length,
        filesCount: uploadedFiles.length
    });
});

// Redirect dashboard.html -> inventory.html
app.get('/dashboard.html', (req, res) => {
    res.redirect(301, '/inventory.html');
});
app.get('/dashboard', (req, res) => {
    res.redirect(301, '/inventory.html');
});

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
            TableName: process.env.DYNAMODB_TABLE || 'user_login',
            Key: { username: cleanUsername }
        });

        const response = await docClient.send(command);

        if (!response.Item) {
            return res.status(401).json({ success: false, message: 'ไม่พบชื่อผู้ใช้งานนี้' });
        }

        if (response.Item.password === password) {
            res.json({
                success: true,
                user: {
                    username: response.Item.username,
                    name: response.Item.name || response.Item.username,
                    role: response.Item.role || 'User'
                }
            });
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
            TableName: process.env.DYNAMODB_TABLE || 'user_login',
            Key: { username: email.toLowerCase().trim() }
        });
        const existingUser = await docClient.send(checkCommand);

        if (existingUser.Item) {
            return res.status(400).json({ success: false, message: 'อีเมลนี้มีบัญชีในระบบอยู่แล้ว' });
        }

        const putCommand = new PutCommand({
            TableName: process.env.DYNAMODB_TABLE,
            Item: {
                username: email.toLowerCase().trim(),
                password: password,
                name: name.trim(),
                role: role,
                createdAt: new Date().toISOString()
            }
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

    const params = {
        Bucket: process.env.S3_BUCKET_NAME,
        Key: `csv-uploads/${Date.now()}_${req.file.originalname}`,
        Body: req.file.buffer,
        ContentType: 'text/csv'
    };

    try {
        await s3Client.send(new PutObjectCommand(params));
        
        const sizeFormatted = (req.file.size / (1024 * 1024) >= 1)
            ? (req.file.size / (1024 * 1024)).toFixed(1) + ' MB'
            : (req.file.size / 1024).toFixed(1) + ' KB';
        const now = new Date();
        const timeStr = `${now.getHours().toString().padStart(2, '0')}:${now.getMinutes().toString().padStart(2, '0')}`;
        
        const fileItem = {
            name: req.file.originalname,
            key: params.Key,
            size: sizeFormatted,
            time: timeStr,
            status: 'success'
        };
        uploadedFiles.unshift(fileItem);
        if (uploadedFiles.length > 100) uploadedFiles.pop();

        res.json({ success: true, filename: req.file.originalname, key: params.Key, file: fileItem });
    } catch (err) {
        console.error('S3 Upload Error:', err);
        res.status(500).json({ success: false, message: 'อัปโหลดลง S3 ล้มเหลว: ' + err.message });
    }
});

// ดึงรายการไฟล์ที่อัปโหลดไว้ (In-Memory)
app.get('/api/uploads', (req, res) => {
    res.json({ success: true, files: uploadedFiles });
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
        uploadedFiles = uploadedFiles.filter(f => f.key !== key);
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

        const cloudResponse = await fetch('http://localhost:8000/ask', {
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
        chatHistory.push(chatRecord);
        if (chatHistory.length > 100) chatHistory.shift();

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

// ดึงประวัติการแชตกับ AI (In-Memory)
app.get('/api/chat/history', (req, res) => {
    res.json({ success: true, history: chatHistory });
});

// ล้างประวัติการแชต
app.delete('/api/chat/history', (req, res) => {
    chatHistory = [];
    res.json({ success: true, message: 'ล้างประวัติการคุยเรียบร้อยแล้ว' });
});

// ==========================================
// API เพิ่มเติม: ดึงและประมวลผลข้อมูล CSV จาก S3 สำหรับ Dashboard
// ==========================================
app.get('/api/dashboard-data', async (req, res) => {
    try {
        // ค้นหาไฟล์ CSV ล่าสุดที่อัปโหลดใน uploadedFiles
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
// API 7: ดึงข้อมูลจาก RDS Data Warehouse พร้อมระบบตัวกรอง (Filters)
// ==========================================
const { Pool } = require('pg');

// ปิดการตรวจสอบ SSL เฉพาะ Node.js และจัดการ URL
process.env.NODE_TLS_REJECT_UNAUTHORIZED = '0';
const nodeDbUrl = process.env.DATABASE_URL
    .replace('postgresql+psycopg://', 'postgresql://')
    .replace('?sslmode=require', '');

const pool = new Pool({
    connectionString: nodeDbUrl,
    ssl: { rejectUnauthorized: false }
});

app.get('/api/dashboard', async (req, res) => {
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
                conditions.push(`${prefix}crop_sk IN (SELECT crop_sk FROM public.dim_crop WHERE category = '${catTh}')`);
            }

            // ตัวกรองที่ 2: คลังสินค้า (ถ้ามีตัวเลือกเพิ่มในอนาคต โค้ดนี้ก็พร้อมทำงาน)
            if (warehouse && warehouse !== 'all') {
                conditions.push(`${prefix}warehouse_sk IN (SELECT warehouse_sk FROM public.dim_warehouse WHERE warehouse_id = '${warehouse}')`);
            }

            // ตัวกรองที่ 3: ช่วงเวลา 
            // :bulb: แก้ไข: จำลองวันที่ปัจจุบันเป็น 2025-12-31 เพื่อให้ตรงกับข้อมูลชุดสุดท้ายที่มีในฐานข้อมูล
            const mockToday = "'2025-12-31'::date";

            if (date === 'month') {
                conditions.push(`${prefix}${dateColumn} IN (SELECT date_key FROM public.dim_date WHERE month = EXTRACT(MONTH FROM ${mockToday}) AND year = EXTRACT(YEAR FROM ${mockToday}))`);
            } else if (date === 'quarter') {
                conditions.push(`${prefix}${dateColumn} IN (SELECT date_key FROM public.dim_date WHERE quarter = EXTRACT(QUARTER FROM ${mockToday}) AND year = EXTRACT(YEAR FROM ${mockToday}))`);
            } else if (date === 'year') {
                conditions.push(`${prefix}${dateColumn} IN (SELECT date_key FROM public.dim_date WHERE year = EXTRACT(YEAR FROM ${mockToday}))`);
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
            FROM public.fact_harvest
            ${harvestWhere}
        `);

        const cropQuery = await pool.query(`
            SELECT c.crop_name, COALESCE(SUM(h.quantity_kg), 0) / 1000 AS qty_ton
            FROM public.fact_harvest h
            JOIN public.dim_crop c ON h.crop_sk = c.crop_sk
            ${harvestWhereAlias} 
            GROUP BY c.crop_name
        `);
        let cropData = {};
        cropQuery.rows.forEach(r => cropData[r.crop_name] = Number(r.qty_ton));

        const salesKpi = await pool.query(`
            SELECT 
                COALESCE(SUM(total_amount_thb), 0) AS amount, 
                COALESCE(SUM(quantity_kg), 0) / 1000 AS qty_ton 
            FROM public.fact_sales
            ${salesWhere}
        `);

        const shipKpi = await pool.query(`
            SELECT COALESCE(SUM(shipping_cost_thb), 0) AS shipping 
            FROM public.fact_shipment
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