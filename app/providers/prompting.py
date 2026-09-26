import json

from app.providers.base import SummarizationRequest, TextToSQLRequest


def build_text_to_sql_prompt(request: TextToSQLRequest) -> str:
    prompt = request.text_to_sql_prompt.replace(
        "{schema_context}", request.schema_context
    ).replace("{question}", request.question)
    return (
        f"{prompt}\n\n"
        "Return only a JSON object with this exact shape:\n"
        '{"intent":"analytics|knowledge","sql":"SELECT ... or null",'
        '"assumptions":["..."]}\n'
        "Use intent=knowledge and sql=null when the question cannot be answered "
        "from the warehouse with SQL."
    )


def build_summarization_prompt(request: SummarizationRequest) -> str:
    rows_json = json.dumps(request.rows, ensure_ascii=False, default=str)
    return (
        "ตอบคำถามเป็นภาษาไทยจากข้อมูลผลลัพธ์ด้านล่างเท่านั้น "
        "ห้ามสร้างตัวเลขหรือข้อเท็จจริงที่ไม่มีในผลลัพธ์ และให้ระบุหน่วยเมื่อทราบ\n"
        "จัดคำตอบให้อ่านง่ายด้วย Markdown แบบง่าย: เริ่มด้วยสรุปสั้น 1-2 ประโยค "
        "จากนั้นใช้หัวข้อสั้นและ bullet เมื่อมีหลายรายการ "
        "ห้ามใช้ตาราง Markdown หรือ code block "
        "และแสดงไม่เกิน 12 bullet เว้นแต่ผู้ใช้ขอรายการทั้งหมดโดยตรง\n"
        f"บทบาทผู้ใช้: {request.user_role or 'ไม่ระบุ'}\n"
        f"คำถาม: {request.question}\n"
        f"ผลลัพธ์ฐานข้อมูล: {rows_json}"
    )
