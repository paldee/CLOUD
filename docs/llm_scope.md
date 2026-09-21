# LLM Work Scope

## In scope

- Prompt engineering สำหรับตอบคำถามภาษาไทย
- Text-to-SQL สำหรับ query ข้อมูลจาก Amazon RDS
- RAG สำหรับ data dictionary, dashboard definitions และ business rules
- API endpoint สำหรับ frontend หรือ dashboard เรียกใช้งาน
- Deployment บน Amazon EC2
- Deterministic SQL guardrails และ read-only database access

## Out of scope ตอนนี้

- ETL pipeline จาก CSV ไป RDS
- Dashboard visualization
- Data model migration ของ RDS
- Authentication/authorization เต็มรูปแบบ

## Key questions ที่ต้องเติมภายหลัง

- เลือก orchestration framework หลังทดสอบด้วยโจทย์และชุดคำถามเดียวกัน
- ใช้ LLM provider ตัวไหนเป็น production default
- RDS เป็น PostgreSQL, MySQL หรือ engine อื่น
- ต้องจำกัดสิทธิ์ตาม user role แค่ไหน
- ต้องเก็บ audit log ของคำถาม, SQL และคำตอบหรือไม่
