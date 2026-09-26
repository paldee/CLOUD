# Agent API Contract

Local base URL: `http://localhost:8000`

Interactive backend documentation is available at `/docs` when FastAPI is running.

## Health Check

`GET /health`

```json
{
  "status": "ok",
  "env": "local",
  "llm_provider": "groq",
  "llm_model": "qwen/qwen3.8-27b",
  "database_source": "local-postgres"
}
```

## Ask Agent

`POST /ask`

Request:

```json
{
  "question": "ยอดขายรวมรายเดือนเป็นเท่าไร",
  "user_role": "analyst"
}
```

`question` ต้องมีอย่างน้อยหนึ่งตัวอักษร ส่วน `user_role` ไม่บังคับและส่ง `null` ได้

Response:

```json
{
  "answer": "SQL ผ่าน guardrail แล้ว แต่ยังไม่ได้ตั้งค่า DATABASE_URL",
  "sql": "SELECT ... LIMIT 100",
  "sources": ["schema-catalog"],
  "status": "not_configured",
  "guardrail_violations": [],
  "visualization": null
}
```

`visualization` เป็น chart spec ที่สร้างจากแถวผลลัพธ์จริงโดยไม่ให้ LLM สร้างตัวเลข
และมีค่าเป็น `null` เมื่อผลลัพธ์ไม่เหมาะกับการทำกราฟ เช่น query ที่คืนค่าเดียว

## Status Values

| Status | ความหมาย | UI ที่แนะนำ |
|---|---|---|
| `answered` | ประมวลผลสำเร็จ | แสดงคำตอบตามปกติ |
| `rejected` | SQL ไม่ผ่าน policy | แสดง warning และ violations โดยไม่บอกว่าระบบล่ม |
| `not_configured` | service บางส่วนยังไม่ได้ตั้งค่า | แสดง development/configuration state |

## Errors

- `422` request ไม่ตรง schema เช่น question ว่าง
- `500` backend error ที่ไม่ได้จัดการ
- network error หรือ timeout จะถูก throw จาก browser `fetch`

Frontend ไม่ควรนำค่า `sql` ไป execute เอง ค่า SQL มีไว้เพื่อ audit/debug display เท่านั้น
