# Flow การทำงานและการเชื่อมต่อระบบ AgriChain กับ AWS Cloud เต็มรูปแบบ
> **อัปเดตล่าสุด**: ใช้ค่าคอนฟิกจาก `.env`

เอกสารนี้รวบรวม **Flow การทำงานร่วมกันของทั้ง 4 ฝ่าย** (DWH Admin, Data Engineer, Web Developer, AI Engineer) พร้อมลำดับขั้นตอนการเปิดเซิร์ฟเวอร์, การทดสอบในเครื่อง (Local), และการ Deploy ขึ้น Amazon EC2 จริง

---

## 1. ผังรวมสถาปัตยกรรมระบบ (End-to-End Cloud Architecture)

```mermaid
flowchart TD
    subgraph DWH_Role["1. DWH Admin & Database"]
        RDS[("Amazon RDS (PostgreSQL)<br>Endpoint: &lt;YOUR_RDS_ENDPOINT&gt;<br>Port: 5432 | DB: postgres<br>User: admin_agri<br>(9 ตาราง: 5 Dim + 4 Fact)")]
    end

    subgraph DE_Role["2. Data Engineer (ETL Pipeline)"]
        S3[("Amazon S3 Bucket<br>agri-csv-data-cloud<br>(Raw CSV Data)")]
        ETL["AWS Lambda (Serverless ETL)<br>Event Trigger S3 -> Clean & Transform<br>-> โหลดลง RDS")]
        S3 --> ETL
        ETL --> RDS
    end

    subgraph Server_Role["3. Amazon EC2 (IP: 98.92.78.107)"]
        WebServer["Web Server (Node.js Express)<br>Port: 3000 (server.js)<br>• หน้า Login, Dashboard, Agent<br>• DynamoDB Auth / S3 Proxy"]
        DynamoDB[("Amazon DynamoDB<br>Table: user_login<br>(Key: username)")]
        AIBig["AI Backend (FastAPI)<br>Port: 8000 (app.main:app)<br>• SQL Guardrails & Timeout<br>• Schema Verifier & Chart Spec"]
    end

    subgraph AI_Role["4. AI Engineer (LLM Layer)"]
        LLM["Groq Cloud API<br>(Qwen 3.8-27b)"]
    end

    subgraph User_Client["ผู้ใช้งานทั่วไป (End User)"]
        Client["Web Browser<br>http://98.92.78.107:3000"]
    end

    %% Client Interactions
    Client -->|1. เข้าหน้า Login / Auth| WebServer
    WebServer <-->|ตรวจรหัสผ่าน| DynamoDB
    Client -->|2. อัปโหลด CSV สด| WebServer
    WebServer -->|บันทึกไฟล์| S3
    Client -->|3. ถามคำถามภาษาไทย| WebServer
    WebServer -->|Proxy POST /ask| AIBig

    %% AI Query Flow
    AIBig -->|ส่งคำถาม + Schema Context| LLM
    LLM -->|สร้าง SQL Query| AIBig
    AIBig -->|SQL Guardrail ตรวจสอบความปลอดภัย| AIBig
    AIBig -->|Execute Read-Only SQL (Port 5432)| RDS
    RDS -->|ส่งคืนผลลัพธ์ Rows จริง| AIBig
    AIBig -->|ส่ง Rows ให้สรุปภาษาไทย| LLM
    LLM -->|บทสรุปภาษาไทย| AIBig
    AIBig -->|Answer + SQL + Chart Spec| WebServer
    WebServer -->|เรนเดอร์ UI + กราฟ Chart.js| Client
```

---

## 2. ค่าคอนฟิกปัจจุบันใน `.env` ที่พร้อมใช้งานทันที

ค่าเหล่านี้ถูกบันทึกไว้ใน [.env](file:///c:/Users/PatnaganK/Downloads/CLOUD/.env) เรียบร้อยแล้ว:

```dotenv
# ==========================================
# 1. ข้อมูลระบบและ Network
# ==========================================
APP_NAME=agri-dw-llm-agent
APP_ENV=cloud
LOG_LEVEL=INFO
PORT=3000

# IP ของ EC2 ปัจจุบัน (หาก Stop/Start เครื่องแล้ว IP เปลี่ยน ให้แก้อัปเดตที่นี่)
EC2_PUBLIC_IP=98.92.78.107
CORS_ORIGINS=http://localhost:3000,http://localhost:5173,http://127.0.0.1:3000,http://127.0.0.1:5173,http://98.92.78.107:3000,http://98.92.78.107:8000

# ==========================================
# 2. LLM Provider (Qwen via Groq)
# ==========================================
LLM_PROVIDER=qwen
GROQ_MODEL=qwen/qwen3.8-27b
GROQ_API_KEY=your_groq_api_key_here

# ==========================================
# 3. Amazon RDS PostgreSQL Connection
# ==========================================
DATABASE_URL=postgresql+psycopg://admin_agri:<YOUR_PASSWORD>@<YOUR_RDS_ENDPOINT>:5432/postgres?sslmode=require
DATABASE_SCHEMA=data_warehouse

# Guardrail Limits
MAX_SQL_ROWS=100
MAX_SQL_SECONDS=15

# ==========================================
# 4. AWS Services (S3, DynamoDB, IAM Keys)
# ==========================================
AWS_REGION=us-east-1
S3_BUCKET_NAME=agri-csv-data-cloud
DYNAMODB_TABLE=user_login
AWS_ACCESS_KEY_ID=your_aws_access_key_id
AWS_SECRET_ACCESS_KEY=your_aws_secret_access_key
```

---

## 3. Flow การทำงานตามหน้าที่ (Role-Based Workflow)

### 3.1 DWH Admin Flow: จัดเตรียมฐานข้อมูล Amazon RDS
1. **เปิด RDS Instance**:
   - ตรวจสอบสถานะของ `agri-dwh-db` บน AWS Console ว่าเป็น **Available**
2. **ตั้งค่า Security Group (`agri-db-sg`)**:
   - ไปที่แท็บ **Connectivity & security** -> **Inbound rules** -> **Edit inbound rules**
   - เพิ่ม Rule: `Type: PostgreSQL (5432)`, `Source: 0.0.0.0/0` (หรือใส่ IP ของ EC2 `98.92.78.107/32` และ IP เครื่องตัวเอง)
3. **รัน Schema บน RDS ผ่าน pgAdmin**:
   - เชื่อมต่อ: `Host: <YOUR_RDS_ENDPOINT>`, `Port: 5432`, `DB: postgres`, `User: admin_agri`, `Pass: <YOUR_PASSWORD>`
   - รัน SQL:
     ```sql
     CREATE SCHEMA IF NOT EXISTS data_warehouse;
     ```
   - นำเข้าตารางจากไฟล์ `schema.sql` จนได้ครบทั้ง 9 ตาราง (5 Dimension + 4 Fact)

---

### 3.2 Data Engineer Flow: ดึงข้อมูลจาก S3 และโหลดลง RDS
1. **รับไฟล์ดิบเข้า S3**:
   - ไฟล์ CSV จะถูกอัปโหลดผ่านเว็บ หรืออัปโหลดตรงไปที่ Bucket `agri-csv-data-cloud`
2. **รันสคริปต์ ETL (Python)**:
   - สคริปต์ใช้ `boto3` ดึงไฟล์จาก S3 และใช้ `psycopg` หรือ `SQLAlchemy` โหลดข้อมูลลง RDS
   - ตัวอย่าง Connection String ในสคริปต์ ETL:
     ```python
     import os
     from sqlalchemy import create_engine

     DB_URL = "postgresql+psycopg://admin_agri:<YOUR_PASSWORD>@<YOUR_RDS_ENDPOINT>:5432/postgres?sslmode=require"
     engine = create_engine(DB_URL)
     ```
3. **ตรวจสอบจำนวนแถวข้อมูล**:
   - ตาราง Fact เช่น `data_warehouse.fact_sales` ต้องมีข้อมูลเพื่อให้ AI สืบคืนยอดขายได้

---

### 3.3 AI Engineer Flow: ตรวจสอบ Schema, ทดสอบ Guardrail & Text-to-SQL
หลังจาก DWH Admin เปิด RDS และสร้างตารางเสร็จแล้ว ให้รันคำสั่งตรวจสอบตามลำดับ:

1. **ตรวจสอบความเข้ากันได้ของ Schema ระหว่าง RDS กับ AI Catalog**:
   ```bash
   .venv\Scripts\python scripts\verify_rds_schema.py
   ```
   *ผลลัพธ์ที่ถูกต้อง*: `RDS schema 'data_warehouse' matches the AI schema catalog.`

2. **ทดสอบความพร้อมของ LLM Provider (Qwen)**:
   ```bash
   .venv\Scripts\python scripts\smoke_test_providers.py
   ```
   *ผลลัพธ์ที่ถูกต้อง*: `Provider smoke test: 1 passed, 0 failed`

3. **รัน Benchmark ข้อสอบภาษาไทย 30 ข้อกับ RDS**:
   ```bash
   .venv\Scripts\python scripts\run_reference_benchmark.py
   ```
   *ผลลัพธ์ที่ถูกต้อง*: `Reference benchmark: 30 passed, 0 failed`

---

### 3.4 Web Developer Flow: ทดสอบในเครื่องก่อนขึ้น EC2
1. **ทดสอบในเครื่องตัวเอง (Local Test)**:
   - กุญแจ AWS Access Key และ Secret Key อยู่ใน `.env` เรียบร้อยแล้ว
   - รัน Express Server:
     ```bash
     node server.js
     ```
   - เข้าหน้าเว็บ `http://localhost:3000/`:
     - ทดสอบหน้า **Login (`index.html`)**: ทดสอบเข้าสู่ระบบผ่าน DynamoDB ด้วย `exec01` / `Exec@1234`
     - ทดสอบหน้า **Upload CSV (`dashboard.html`)**: ลองลากไฟล์ CSV ทดสอบอัปโหลดขึ้น S3
     - ทดสอบหน้า **ผู้ช่วย AI (`agent.html`)**: ลองส่งคำถาม เช่น *"ยอดขายสุทธิทั้งหมดเท่าไร"* เพื่อดูผลลัพธ์และกราฟ

2. **เตรียมไฟล์ส่งขึ้น EC2**:
   - เมื่อทดสอบบนเครื่องผ่านเรียบร้อย ให้ Push โค้ดขึ้น Git:
     ```bash
     git add .
     git commit -m "feat: integrate AgriChain web with AWS RDS and LLM agent"
     git push origin agri-data-warehouse-llm-agent
     ```

---

## 4. ขั้นตอนการ Deploy บน Amazon EC2 (`98.92.78.107`)

### ขั้นตอนที่ 1: SSH เข้า EC2 Server
```bash
ssh -i "agri-key.pem" ubuntu@98.92.78.107
```

### ขั้นตอนที่ 2: ดึงโค้ดและติดตั้ง Dependencies
```bash
# Clone หรือ Pull โค้ดล่าสุด
git clone https://github.com/paldee/CLOUD.git
cd CLOUD

# ติดตั้ง Node.js dependencies
npm install

# ติดตั้ง Python dependencies
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### ขั้นตอนที่ 3: ตรวจสอบไฟล์ `.env` บน EC2
ตรวจดูว่าไฟล์ `.env` บน EC2 มีค่าตรงตามตารางในข้อ 2 ครบถ้วน (โดยเฉพาะ `EC2_PUBLIC_IP=98.92.78.107`)

### ขั้นตอนที่ 4: สตาร์ต Services เป็น Background Daemon
```bash
# 1. รัน AI Backend FastAPI (Port 8000)
nohup uvicorn app.main:app --host 0.0.0.0 --port 8000 > ai.log 2>&1 &

# 2. รัน Web Server Node.js (Port 3000)
nohup node server.js > server.log 2>&1 &
```

### ขั้นตอนที่ 5: ตรวจสอบความพร้อมการทำงาน
```bash
# ตรวจสอบสถานะ AI Backend
curl http://localhost:8000/health
# ควรได้: {"status":"ok","env":"cloud","llm_provider":"groq","database_source":"amazon-rds"}
```

เปิด Browser เข้าใช้งานระบบจริง:
```text
http://98.92.78.107:3000
```

---

## 5. ลำดับขั้นตอนการเปิด Server และการประสานงาน (Execution Checklist)

เมื่อถึงเวลาที่จะเริ่มทำการทดสอบ ให้ปฏิบัติตามลำดับดังนี้:

| ลำดับ | สิ่งที่ต้องทำ | ผู้รับผิดชอบ | จุดตรวจสอบความสำเร็จ |
|---|---|---|---|
| **1** | สตาร์ตเครื่อง **Amazon RDS** (`agri-dwh-db`) ใน AWS Console | DWH Admin | สถานะเป็น `Available` |
| **2** | เช็ค Inbound Rule ของ RDS Security Group ว่าเปิด Port `5432` | DWH Admin | ไม่ติด connection timeout |
| **3** | รัน `schema.sql` สร้าง 9 ตาราง Data Warehouse | DWH Admin | ใน pgAdmin เห็นครบ 9 ตาราง |
| **4** | รันสคริปต์โหลดข้อมูล CSV เข้า RDS | Data Engineer | ในตาราง `fact_sales` มีข้อมูล |
| **5** | รัน `scripts/verify_rds_schema.py` เพื่อเช็คความถูกต้อง | AI Engineer | ขึ้น `matches the AI schema catalog` |
| **6** | สตาร์ตเครื่อง **Amazon EC2** (`98.92.78.107`) | Web Dev / Cloud Admin | สเตตัส EC2 เป็น `Running` |
| **7** | รัน `server.js` (3000) และ `uvicorn` (8000) บน EC2 | Web Dev / AI Engineer | พอร์ต 3000 และ 8000 พร้อมรับคำขอ |
| **8** | เข้าหน้าเว็บผ่าน Browser `http://98.92.78.107:3000` | ทั้งทีม | ล็อกอินผ่าน DynamoDB และถาม AI ได้คำตอบจาก RDS |
