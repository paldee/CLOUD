# 🌿 AgriChain — Agricultural Supply Chain Intelligence Platform

> ระบบจัดการห่วงโซ่อุปทานการเกษตรอัจฉริยะ พัฒนาบน AWS Cloud  
> **Clone repo นี้เดียวแล้วรันได้ทั้งระบบ**

---

## 🏗️ Architecture

```
Browser → EC2 (Node.js :3000) ─── /api/login  ──→ DynamoDB
                               ─── /api/upload ──→ S3 Bucket
                               ─── /api/chat   ──→ FastAPI AI (:8000)
                                                        ↓
                                              PostgreSQL / Athena
```

## 📁 Project Structure

```
agrichain-app_v1/
├── server.js           # Node.js Express backend (Port 3000)
├── package.json
├── .env.example        # Template สำหรับ environment variables
│
├── public/             # Frontend (HTML/CSS/JS)
│   ├── index.html      # Login page
│   ├── login.js        # Login handler → DynamoDB
│   ├── dashboard.html  # Dashboard
│   ├── agent.html      # AI Agent chat page
│   └── register.html
│
├── app/                # Python FastAPI AI Backend (Port 8000)
│   ├── main.py
│   ├── agents/         # LLM Agent logic
│   ├── api/            # API routes
│   ├── db/             # Database connection
│   ├── services/       # Query workflow
│   └── prompts/        # System prompts
│
├── requirements.txt    # Python dependencies
└── Dockerfile
```

---

## ⚙️ Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | HTML, CSS, Vanilla JS |
| Node.js Backend | Express.js (Port 3000) |
| Auth | AWS DynamoDB |
| File Storage | AWS S3 |
| AI Backend | Python FastAPI + LangGraph (Port 8000) |
| Database | PostgreSQL / AWS Athena |
| Hosting | AWS EC2 |

---

## 🚀 Deploy on EC2 (ทำตามลำดับ)

### 1. Clone repo

```bash
git clone https://github.com/paldee/CLOUD.git
cd CLOUD/1/agrichain-app_v1
```

### 2. ตั้งค่า Environment Variables

```bash
cp .env.example .env
nano .env
# ใส่ AWS credentials จาก AWS Academy → AWS Details
```

### 3. เริ่ม Node.js Web App

```bash
npm install
nohup node server.js > logs/node.log 2>&1 &
# หรือใช้ pm2:
npm install -g pm2
pm2 start server.js --name agrichain-web
```

### 4. เริ่ม Python AI Backend

```bash
pip install -r requirements.txt
nohup uvicorn app.main:app --host 0.0.0.0 --port 8000 > logs/python.log 2>&1 &
# หรือใช้ pm2:
pm2 start "uvicorn app.main:app --host 0.0.0.0 --port 8000" --name agrichain-ai
```

### 5. ตรวจสอบ EC2 Security Group

เปิด Inbound ports:
- `3000` (Node.js Web App)
- `8000` (Python AI Backend)

### 6. เข้าใช้งาน

```
http://<EC2_PUBLIC_IP>:3000
```

---

## 👤 Test Accounts (ใน DynamoDB)

| Username | Password | Role |
|----------|----------|------|
| `exec01` | `Exec@1234` | Executive |
| `analyst01` | `Analyst@1234` | Data Analyst |
| `admin01` | `Admin@1234` | Data Admin |

---

## 🔐 Environment Variables

```env
PORT=3000
AWS_REGION=us-east-1
S3_BUCKET_NAME=agri-csv-data-cloud
DYNAMODB_TABLE=user_login
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...
AWS_SESSION_TOKEN=...    # AWS Academy token (หมดทุก ~4 ชม.)
```

> ⚠️ **ห้าม commit `.env` ขึ้น git เด็ดขาด** — ไฟล์นี้ถูก ignore แล้ว
