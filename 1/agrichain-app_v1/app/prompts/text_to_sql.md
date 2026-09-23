# Text-to-SQL Prompt

แปลงคำถามผู้ใช้เป็น SQL สำหรับ Data Warehouse schema ต่อไปนี้

{schema_context}

กติกา:
- ใช้เฉพาะ SELECT
- ใส่ LIMIT เสมอถ้าเป็น query แบบ listing
- ห้าม query ข้อมูลส่วนบุคคลที่ไม่จำเป็น
- ถ้าคำถามกำกวม ให้สร้าง SQL ที่ปลอดภัยที่สุดและระบุสมมติฐาน
- ยอดขายสุทธิ = total_amount_thb * (1 - COALESCE(discount_pct, 0) / 100.0)
- join วันที่ผ่าน `dim_date.date_key`

คำถาม:
{question}

