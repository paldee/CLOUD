# AgriChain: Agriculture Data Warehouse AI Assistant

ระบบ AI Assistant สำหรับวิเคราะห์และสืบค้นข้อมูล Data Warehouse ห่วงโซ่อุปทานการเกษตรด้วยภาษาธรรมชาติ รองรับงาน Text-to-SQL, การสรุปผลเป็นภาษาไทย, การสร้างตารางข้อมูลและกราฟวิเคราะห์ (Chart.js) โดยเชื่อมต่อกับ **Amazon RDS PostgreSQL** และขับเคลื่อนด้วยโมเดล **Qwen (via Groq API)** ภายใต้การควบคุมความปลอดภัยด้วย Deterministic SQL Guardrails

![System Architecture](assets/cloud_archetec_lastversion.png)

---

## ภาพรวมสถาปัตยกรรมระบบ

ระบบออกแบบตามหลัก Separation of Concerns โดยแยกส่วน LLM Boundary, Security Guardrails, และ Data Warehouse Execution ออกจากกันอย่างเด็ดขาด:

```mermaid
flowchart TD
    UI["Frontend Web UI (HTML5 / CSS / JS)"] -->|POST /api/v1/query| API["FastAPI Backend on Amazon EC2"]
    API --> PLAN["LLM Query Planner (Qwen / Groq)"]
    PLAN --> GUARD["SQL AST Guardrails (SQLGlot)"]
    GUARD -->|Rejected| API
    GUARD -->|Validated SELECT| RDS[("Amazon RDS PostgreSQL (Data Warehouse)")]
    RDS --> SUMMARY["Answer Summarizer & Chart Builder"]
    SUMMARY --> API
    API --> UI
    UI -.->|Login & CSV Upload| NODE["Express Server (DynamoDB & S3)"]
```

![Frontend Preview](assets/frontend_preview.png)

---

## ความสามารถหลักของระบบ

1. **Natural Language to SQL (Text-to-SQL)**:
   - แปลงคำถามภาษาไทยเป็นคำสั่ง PostgreSQL สำหรับ Star Schema ของ Data Warehouse
   - สรุปผลลัพธ์เป็นภาษาไทยที่เข้าใจง่าย พร้อมระบุที่มาและสมมติฐาน (Assumptions)
2. **Deterministic SQL Guardrails (ความปลอดภัยสูงสุด)**:
   - ตรวจสอบ Abstract Syntax Tree (AST) ด้วย SQLGlot ก่อนส่งไปยังฐานข้อมูล
   - อนุญาตเฉพาะคำสั่ง `SELECT` แบบ Read-only เท่านั้น (ปฏิเสธ `INSERT`, `UPDATE`, `DELETE`, `DROP`, `ALTER`, `TRUNCATE`)
   - ควบคุม Schema, Table และ Column ด้วย Allowlist (`data_warehouse.*`)
   - ปฏิเสธการรัน Multiple Statements และ `SELECT *`
   - บังคับ `LIMIT` อัตโนมัติ (ไม่เกิน 100 แถว) และกำหนด Query Timeout ป้องกันฐานข้อมูลค้าง
3. **Data Visualization & Interactive Table**:
   - ตรวจจับชุดข้อมูลและสร้างกราฟวิเคราะห์อัตโนมัติ (Bar Chart, Line Chart)
   - แสดงผลตารางข้อมูลพร้อมปุ่มส่งออก / คัดลอกข้อมูล
4. **AgriChain Web Portal ครบวงจร**:
   - ระบบเข้าสู่ระบบ (Authentication) ผ่าน AWS DynamoDB
   - ศูนย์อัปโหลดข้อมูล (Data Ingestion) สู่ Amazon S3
   - หน้าผู้ช่วย AI สอบถามข้อมูลห่วงโซ่อุปทาน
5. **ระบบสลับ 2 ภาษาแบบไดนามิก (Dynamic Bilingual TH / EN)**:
   - ขับเคลื่อนด้วยไลบรารี **i18next** พร้อม Local UMD bundle (`frontend/i18next.min.js`) รองรับการทำงานแบบ Offline ไม่ต้องพึ่งพา CDN ภายนอก
   - พจนานุกรมคำศัพท์คู่ขนาน TH ↔ EN ครบถ้วน 100% (67 คำศัพท์หลัก) ครอบคลุมทั้ง เมนูนำทาง, ฟอร์ม, Placeholder, ข้อความทักทายของ AI, สถานะ และกล่องแจ้งเตือน/ยืนยัน
   - สลับภาษาแบบ Real-time ทันทีโดยไม่ต้องรีเฟรชหน้าเว็บ พร้อมระบบจดจำภาษาผ่าน `localStorage` ข้ามทุกหน้าเว็บ
6. **ระบบดูตัวอย่างข้อมูลไฟล์ (CSV Sample Data Preview)**:
   - คลิกดูตัวอย่างข้อมูลภายในไฟล์ CSV ที่อัปโหลดได้ทันที (คลิกที่ชื่อไฟล์โดยตรง หรือคลิกไอคอนเอกสาร 📄)
   - หน้าต่าง Modal สรุปข้อมูลแถวตัวอย่าง, จำนวนแถวทั้งหมด และจำนวนคอลัมน์ พร้อมตาราง Scrollbar แนวนอนและแนวตั้ง
   - ทำงานได้ทันทีผ่าน `FileReader` (0ms Client-side Preview) โดยไม่ต้องรอต่อ S3 และรองรับการดึงข้อมูลจาก Amazon S3 เมื่อเชื่อมต่อ Cloud
   - สถานะตารางเริ่มต้นเป็น Clean Empty State ไม่ทิ้งข้อมูล Mock ตกค้าง พร้อมสำหรับการส่งมอบงานจริง

---

## โครงสร้างโปรเจกต์

```text
CLOUD/
├── app/                     # FastAPI Backend & AI Agent Core
│   ├── agents/              # Query planner, Agent state และ Text-to-SQL logic
│   ├── api/                 # REST API endpoints และ Request/Response schemas
│   ├── core/                # System configuration และ environment settings
│   ├── db/                  # RDS database connection และ Schema Catalog
│   ├── guardrails/          # SQLGlot AST Guardrail validation
│   ├── prompts/             # System prompts และ Text-to-SQL templates
│   ├── providers/           # LLM Providers (Qwen via Groq API)
│   ├── services/            # Query workflow และ Answer generation
│   ├── tools/               # SQL Execution และ Data tools
│   └── visualization/       # Chart.js auto-configuration builder
├── assets/                  # ภาพสถาปัตยกรรมและ UI Preview สำหรับเอกสาร
│   ├── cloud_archetec_lastversion.png
│   └── frontend_preview.png
├── dataset/                 # ชุดข้อมูล Master และ Operational CSV (170k+ แถว)
│   ├── master/              # Crop, Customer, Farmer, Warehouse
│   └── operational/         # Harvest, Inventory, Sales, Shipment
├── docs/                    # คู่มือสถาปัตยกรรม, Cloud Flow และ API Contract
├── frontend/                # Unified Web Application
│   ├── index.html           # หน้าเข้าสู่ระบบ (DynamoDB Auth)
│   ├── dashboard.html       # ศูนย์อัปโหลดข้อมูล (S3 Ingestion & CSV Preview)
│   ├── agent.html           # ผู้ช่วย AI วิเคราะห์ข้อมูลและวาดกราฟ
│   ├── i18next.min.js       # Offline UMD bundle ของ i18next library
│   ├── translations.js      # Unified i18n Translation Engine & Bilingual Dictionary (TH/EN)
│   ├── app.js & login.js    # Client-side controller logic
│   └── styles.css           # Modern Theme Stylesheet
├── scripts/                 # สคริปต์จัดการ Schema และ Benchmark บน RDS
├── tests/                   # Pytest automated test suite (33 tests)
├── .env.example             # ตัวอย่างการตั้งค่า Environment Variables
├── Dockerfile               # Dockerfile สำหรับ Build Deploy ขึ้น Amazon EC2
├── package-handoff.bat      # สคริปต์รวมโปรเจกต์เป็น ZIP สำหรับส่งต่อทีมงาน
├── package.json & server.js # Node.js Express สำหรับ AWS DynamoDB และ S3
├── requirements.txt         # Python runtime dependencies
├── requirements-dev.txt     # Python development & testing dependencies
├── schema.sql               # PostgreSQL Schema Definition สำหรับ Amazon RDS
├── setup.bat                # สคริปต์ติดตั้งระบบอัตโนมัติสำหรับ Windows
└── start.bat                # สคริปต์เริ่มการทำงานระบบพร้อมเปิดเบราว์เซอร์
```

---

## เทคโนโลยีที่ใช้งาน

- **Language & Frameworks**: Python 3.10+, FastAPI, Node.js (Express)
- **AI / LLM Model**: Qwen (`qwen/qwen3.8-27b`) ผ่าน Groq Cloud API
- **Database**: Amazon RDS PostgreSQL 16 (Star Schema: Fact & Dimension)
- **Security & Validation**: SQLGlot, Pydantic v2
- **Cloud Infrastructure**: Amazon EC2, Amazon RDS, Amazon S3, Amazon DynamoDB
- **Frontend & i18n**: HTML5, Modern CSS (Responsive), Vanilla JavaScript, Chart.js, i18next (Internationalization)

---

## วิธีการเริ่มต้นใช้งาน (Quick Start บน Windows)

### 1. การติดตั้งครั้งแรก (First-time Setup)

รันคำสั่งต่อไปนี้จาก Command Prompt เพื่อติดตั้ง Python Virtual Environment และ Dependencies ทั้งหมดโดยอัตโนมัติ:

```bat
setup.bat
```

> `setup.bat` จะสร้าง `.venv`, ติดตั้ง dependencies และรัน Unit Tests เพื่อตรวจสอบความสมบูรณ์ของระบบ

### 2. กำหนดค่า Environment Variables

เปิดไฟล์ `.env` และตรวจสอบการตั้งค่า:

```env
# LLM Provider (Qwen ผ่าน Groq API)
LLM_PROVIDER=qwen
GROQ_MODEL=qwen/qwen3.8-27b
GROQ_API_KEY=gsk_...

# Amazon RDS PostgreSQL
DATABASE_URL=postgresql+psycopg://agri_dwh_user:agri_dwh_pass@agri-dwh-dbmaster.cjoywc4cd9ok.us-east-1.rds.amazonaws.com:5432/postgres?sslmode=require
DATABASE_SCHEMA=data_warehouse
```

### 3. เริ่มการทำงานระบบ (Start Application)

รันคำสั่งเดียวเพื่อเปิดใช้งานทั้ง Backend (พอร์ต 8000) และ Frontend (พอร์ต 5173):

```bat
start.bat
```

* **Frontend Web App**: http://localhost:5173
* **FastAPI Backend Swagger**: http://localhost:8000/docs
* **Health Check**: http://localhost:8000/health

---

## การบรรจุไฟล์เพื่อส่งต่อ (Package Handoff)

สำหรับการส่งต่อโปรเจกต์ให้ทีมงานคนอื่น โดยรวมไฟล์การตั้งค่า `.env` แต่คัดแยกโฟลเดอร์ที่ไม่จำเป็น (เช่น `.venv`, `.git`, caches) ออกโดยอัตโนมัติ:

```bat
package-handoff.bat
```

ไฟล์ ZIP จะถูกสร้างไว้ที่โฟลเดอร์ภายนอกในรูปแบบ `CLOUD-handoff-YYYYMMDD-HHMMSS.zip` ผู้รับสามารถแตกไฟล์แล้วรัน `setup.bat` และ `start.bat` ได้ทันที

---

## การทดสอบระบบ (Testing & Verification)

### รัน Unit Tests ทั้งหมด

```powershell
.\.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider
```

ผลการทดสอบ: **33/33 passed (100%)** ครอบคลุม:
- การสกัดและตรวจสอบ SQL AST ผ่าน Guardrails
- การป้องกัน SQL Injection และการปฏิเสธคำสั่งอันตราย
- Schema Catalog และ Table Verification
- Qwen Provider Interface & Query Plan Validation
- Chart Builder และ Data Serialization

### ทดสอบการเชื่อมต่อ LLM (Smoke Test)

```powershell
.\.venv\Scripts\python.exe scripts\smoke_test_providers.py
```

### ตรวจสอบความถูกต้องของ Schema บน RDS

```powershell
.\.venv\Scripts\python.exe scripts\verify_rds_schema.py
```

---

## รายละเอียด REST API

### `GET /health`
ตรวจสอบสถานะระบบและโมเดลที่ใช้งาน:
```json
{
  "status": "ok",
  "env": "local",
  "llm_provider": "qwen",
  "llm_model": "qwen/qwen3.8-27b",
  "database_source": "amazon-rds"
}
```

### `POST /api/v1/query` (หรือ `/ask`)
ส่งคำถามภาษาธรรมชาติเพื่อค้นหาข้อมูล:

**Request Body:**
```json
{
  "question": "ยอดขายแยกตามภูมิภาคในไตรมาสล่าสุดเป็นอย่างไร",
  "user_role": "analyst"
}
```

**Response Body:**
```json
{
  "answer": "ยอดขายรวมในไตรมาสล่าสุดแยกตามภูมิภาค...",
  "sql": "SELECT ... FROM data_warehouse.fact_sales ... LIMIT 100",
  "sources": ["fact_sales", "dim_customer"],
  "status": "answered",
  "guardrail_violations": [],
  "visualization": {
    "type": "bar",
    "title": "ยอดขายแยกตามภูมิภาค",
    "labels": ["ภาคเหนือ", "ภาคกลาง", "ภาคใต้", "ภาคอีสาน"],
    "datasets": [{ "label": "ยอดขาย (บาท)", "data": [1200000, 1850000, 950000, 1400000] }]
  }
}
```

---

## เอกสารอ้างอิงทางเทคนิค

- [docs/rds_cloud_deployment_flow.md](docs/rds_cloud_deployment_flow.md): แผนผังและขั้นตอนการ Deploy บน AWS Cloud เต็มรูปแบบ
- [docs/data_warehouse_context.md](docs/data_warehouse_context.md): รายละเอียดโครงสร้างตาราง Star Schema และ Data Dictionary
- [docs/llm_providers.md](docs/llm_providers.md): การตั้งค่า Qwen (ผ่าน Groq API) และแนวทางการคัดเลือกโมเดล
- [frontend/docs/API_CONTRACT.md](frontend/docs/API_CONTRACT.md): สัญญาระหว่าง Frontend และ Backend API
