const express = require('express');
const cors = require('cors');
const multer = require('multer');
const { S3Client, PutObjectCommand } = require('@aws-sdk/client-s3');
const { DynamoDBClient } = require('@aws-sdk/client-dynamodb');
const { DynamoDBDocumentClient, GetCommand, PutCommand } = require('@aws-sdk/lib-dynamodb');
require('dotenv').config();

const app = express();
app.use(cors());
app.use(express.json());

// ดึงไฟล์ HTML ในโฟลเดอร์ public มาแสดงผล
app.use(express.static('public'));

// ==========================================
// ตั้งค่า AWS Clients (ส่ง Credentials จาก .env เข้าไปตรงๆ)
// ==========================================
const awsConfig = {
    region: process.env.AWS_REGION,
    credentials: {
        accessKeyId: process.env.AWS_ACCESS_KEY_ID,
        secretAccessKey: process.env.AWS_SECRET_ACCESS_KEY,
        sessionToken: process.env.AWS_SESSION_TOKEN // บังคับอ่าน Session Token สำหรับ AWS Academy
    }
};

const s3Client = new S3Client(awsConfig);
const dbClient = new DynamoDBClient(awsConfig);
const docClient = DynamoDBDocumentClient.from(dbClient);

const upload = multer({ storage: multer.memoryStorage() });

// ==========================================
// API 1: ตรวจสอบ Login จาก DynamoDB
// ==========================================
app.post('/api/login', async (req, res) => {
    // รองรับทั้งกรณีที่หน้าบ้านส่ง key ว่า 'username' หรือ 'email'
    const rawUsername = req.body.username || req.body.email;
    const password = req.body.password;

    if (!rawUsername || !password) {
        return res.status(400).json({ success: false, message: 'กรุณากรอกชื่อผู้ใช้งานและรหัสผ่าน' });
    }

    // แปลงเป็นตัวพิมพ์เล็กและตัดช่องว่างหน้า-หลัง ให้ตรงกับข้อมูลใน DynamoDB
    const cleanUsername = rawUsername.toLowerCase().trim();

    try {
        const command = new GetCommand({
            TableName: process.env.DYNAMODB_TABLE,
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
            TableName: process.env.DYNAMODB_TABLE,
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
        res.json({ success: true, filename: req.file.originalname, key: params.Key });
    } catch (err) {
        console.error('S3 Upload Error:', err);
        res.status(500).json({ success: false, message: 'อัปโหลดลง S3 ล้มเหลว: ' + err.message });
    }
});

// ==========================================
// API 4: เชื่อมต่อ AI Backend (รองรับทั้ง /api/chat และ /api/ai/ask)
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

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
    console.log(`✅ Server รันเรียบร้อยแล้วที่ http://localhost:${PORT}`);
});