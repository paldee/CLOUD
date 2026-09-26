# 🌿 AgriChain — Agricultural Supply Chain Intelligence Platform

> ระบบจัดการห่วงโซ่อุปทานการเกษตรอัจฉริยะ พัฒนาบน AWS Cloud

---

## 💡 ระบบนี้ทำงานอย่างไร?

ผู้ใช้เห็นเพียง **เว็บเดียว** ที่ `http://IP:3000` แต่เบื้องหลังมีสองส่วนทำงานร่วมกัน:

```
ผู้ใช้ (Browser)
     │
     ▼
[Node.js :3000]  ← เว็บทั้งหมด: login, dashboard, upload, หน้า AI
     │
     │  เฉพาะหน้า AI → ส่งคำถามต่อให้
     ▼
[Python FastAPI :8000]  ← "สมอง" AI ที่คิดคำตอบจาก LLM + Database
```

| ส่วน | หน้าที่ | Port |
|------|---------|------|
| `server.js` (Node.js) | Login, Dashboard, Upload CSV, serve หน้าเว็บทุกหน้า | 3000 |
| `app/main.py` (Python) | AI Engine — ประมวลผลคำถาม → SQL → คำตอบ | 8000 |

> **หน้า `agent.html` คือหน้าเว็บปกติ** — แต่เมื่อผู้ใช้ถามคำถาม  
> Node.js จะ "ส่งต่อ" ไปให้ Python AI ตอบ แล้วนำคำตอบกลับมาแสดง

---

## 📁 Project Structure

```
agrichain-app_v1/
├── server.js           # Node.js web server (Port 3000)
├── package.json        # Node.js dependencies
│
├── public/             # หน้าเว็บทั้งหมด
│   ├── index.html      # หน้า Login
│   ├── login.js        # Login → DynamoDB
│   ├── dashboard.html  # หน้า Dashboard + Upload CSV
│   ├── agent.html      # หน้า AI Chat (ติดต่อ Python ผ่าน server.js)
│   └── register.html   # หน้าสมัครสมาชิก
│
├── app/                # Python AI Engine (Port 8000)
│   ├── main.py         # FastAPI entry point
│   ├── agents/         # LLM Agent logic
│   ├── db/             # เชื่อมต่อ Database
│   └── prompts/        # คำสั่งให้ AI
│
├── requirements.txt    # Python packages
├── .env.example        # ตัวอย่าง environment variables
└── Dockerfile
```

---

## 🚀 Deploy บน EC2

### ขั้นตอนที่ 1: Clone และ Setup

```bash
git clone https://github.com/paldee/CLOUD.git
cd CLOUD/1/agrichain-app_v1

# สร้าง .env จาก template
cp .env.example .env
nano .env   # ใส่ AWS credentials จาก AWS Academy
```

### ขั้นตอนที่ 2: ติดตั้ง dependencies

```bash
# Node.js
npm install

# Python
pip install -r requirements.txt
```

### ขั้นตอนที่ 3: รัน (ต้องรันทั้งสองพร้อมกัน)

```bash
# รันเว็บ (Node.js)
node server.js &

# รัน AI engine (Python) — ที่หน้า agent.html ต้องใช้
uvicorn app.main:app --host 0.0.0.0 --port 8000 &
```

> ถ้ายังไม่ต้องการใช้หน้า AI ก็รันแค่ `node server.js` พอ

### ขั้นตอนที่ 4: เข้าใช้งาน

```
http://<EC2_PUBLIC_IP>:3000
```

---

## 👤 บัญชีทดสอบ (ใน DynamoDB)

| Username | Password | Role |
|----------|----------|------|
| `exec01` | `Exec@1234` | Executive |
| `analyst01` | `Analyst@1234` | Data Analyst |
| `admin01` | `Admin@1234` | Data Admin |

---

## ⚠️ หมายเหตุ AWS Academy

AWS Session Token **หมดอายุทุก ~4 ชั่วโมง**  
เมื่อ token หมด ให้ไปที่ AWS Academy → AWS Details → copy credentials ใหม่ใส่ `.env` แล้ว restart `node server.js`
