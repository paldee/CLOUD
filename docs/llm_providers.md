# LLM Providers (Qwen 2.5/3.8 via Groq)

ระบบใช้ `LLMProvider` protocol เพื่อแยก Agent Core ออกจาก SDK ของผู้ให้บริการ ปัจจุบันใช้ **Qwen** (ผ่าน Groq API) เป็น Model หลัก โดย Adapter จะคืน typed `QueryPlan` ก่อนที่ SQL จะผ่าน SQLGlot guardrail และถูก execute ด้วย database user บน Amazon RDS


## Groq/Qwen (AI-04)

ตั้งค่าใน PowerShell session:

```powershell
$env:LLM_PROVIDER='groq'
$env:GROQ_MODEL='qwen/qwen3.8-27b'
$env:GROQ_API_KEY='your-key'
```

Adapter ใช้ Groq Python SDK, JSON Object Mode และ Pydantic validation รุ่น Qwen ที่ตรวจสอบจาก
Groq model catalog เมื่อวันที่ 2026-09-21 คือ `qwen/qwen3.8-27b` ห้ามเปลี่ยนเป็น model ID ที่เดาเอง
โดยไม่ตรวจ model catalog หรือ `client.models.list()` ก่อน

Official references:

- [Groq supported models](https://console.groq.com/docs/models)
- [Groq Qwen 3.8 27B](https://console.groq.com/docs/model/qwen/qwen3.8-27b)
- [Groq structured outputs](https://console.groq.com/docs/structured-outputs)

## Optional model override

`LLM_MODEL` ใช้ override provider-specific model ชั่วคราว หากปล่อยว่าง ระบบจะใช้ `GEMINI_MODEL`
หรือ `GROQ_MODEL` ตาม provider ที่เลือก

```powershell
$env:LLM_MODEL=''
```

## Safety boundary

- Provider สร้าง `QueryPlan` แต่ไม่มี database connection และ execute SQL ไม่ได้
- Pydantic ปฏิเสธ payload ที่มี field เกิน schema หรือ analytics plan ที่ไม่มี SQL
- SQLGlot อนุญาตเฉพาะหนึ่ง read-only query จาก schema/table/column allowlist
- Summarizer ได้รับเฉพาะ rows ที่ database คืนมา และ prompt ห้ามสร้างตัวเลขเพิ่ม
- Provider configuration errors หยุด workflow ก่อนเรียกฐานข้อมูล

## Test without API quota

Unit tests ใช้ fake SDK clients จึงไม่เรียก external API:

```powershell
& '.\.venv\Scripts\python.exe' -m pytest -q -p no:cacheprovider
```

## Live provider smoke test

เมื่อใส่ `GOOGLE_API_KEY` และ `GROQ_API_KEY` ใน `.env` แล้ว ให้ทดสอบ provider อย่างละหนึ่ง
request สคริปต์จะแสดงเฉพาะ SQL และผล guardrail โดยไม่แสดง API key และไม่ execute SQL:

```powershell
& '.\.venv\Scripts\python.exe' 'scripts\smoke_test_providers.py'
```

การ benchmark จริงต้องใช้ local PostgreSQL snapshot เดียวกัน, prompts เดียวกัน และคำถาม 30 ข้อ
จาก `tests/benchmarks/text_to_sql_th.json` เพื่อให้เปรียบเทียบสอง provider อย่างยุติธรรม
