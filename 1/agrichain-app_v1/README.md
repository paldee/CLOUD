# 🌿 AgriChain — Agricultural Supply Chain Intelligence Platform

> ระบบจัดการห่วงโซ่อุปทานการเกษตรอัจฉริยะ พัฒนาบน AWS Cloud

## 🏗️ Architecture

```
Browser → EC2 (Node.js/Express) → DynamoDB (Login)
                               → S3 Bucket (CSV Upload)
                               → FastAPI AI Backend (Port 8000)
```

## ⚙️ Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | HTML, CSS, Vanilla JS |
| Backend | Node.js + Express.js |
| Auth | AWS DynamoDB |
| Storage | AWS S3 |
| AI Agent | Python FastAPI (Port 8000) |
| Hosting | AWS EC2 |

## 🚀 Deploy on EC2

### 1. Clone repo
```bash
git clone https://github.com/paldee/CLOUD.git
cd CLOUD/1/agrichain-app_v1
```

### 2. Install dependencies
```bash
npm install
```

### 3. Create `.env` file
```bash
cp .env.example .env
nano .env   # ใส่ AWS credentials จาก AWS Academy
```

### 4. Run server
```bash
# รันแบบ background (ค้างไว้หลัง SSH disconnect)
nohup node server.js > server.log 2>&1 &

# หรือใช้ pm2
npm install -g pm2
pm2 start server.js --name agrichain
pm2 save
```

### 5. Open port 3000 on EC2 Security Group
- Inbound rule: TCP port `3000` จาก `0.0.0.0/0`

### 6. Access the app
```
http://<EC2_PUBLIC_IP>:3000
```

## 👤 Test Accounts (ใน DynamoDB)

| Username | Password | Role |
|----------|----------|------|
| exec01 | Exec@1234 | Executive |
| analyst01 | Analyst@1234 | Data Analyst |
| admin01 | Admin@1234 | Data Admin |

## 📁 Project Structure

```
agrichain-app_v1/
├── server.js          # Express backend
├── login.js           # (legacy root copy)
├── package.json
├── .env.example       # Template สำหรับ environment variables
├── .gitignore
└── public/
    ├── index.html     # Login page
    ├── login.js       # Login handler → DynamoDB
    ├── dashboard.html # Dashboard
    ├── register.html  # Register page
    ├── agent.html     # AI Agent page
    └── front.png
```

## 🔐 Environment Variables

ดู `.env.example` สำหรับตัวแปรที่ต้องกำหนดค่า  
⚠️ **ห้าม commit `.env` ขึ้น git เด็ดขาด**
