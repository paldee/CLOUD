from pathlib import Path

from app.agents.state import QueryPlan
from app.db.schema_catalog import DATA_WAREHOUSE_SCHEMA, DATABASE_SCHEMA, render_schema_context
from app.providers.base import LLMProvider, SummarizationRequest, TextToSQLRequest
from app.tools.rag_tool import retrieve_context


PROMPT_DIR = Path(__file__).resolve().parents[1] / "prompts"


def load_prompt(name: str) -> str:
    return (PROMPT_DIR / name).read_text(encoding="utf-8")


def create_query_plan(
    question: str,
    user_role: str | None = None,
    provider: LLMProvider | None = None,
) -> QueryPlan:
    """
    Framework-neutral LLM boundary.

    Replace the heuristic with a provider call that returns a typed QueryPlan.
    The workflow must still validate every generated SQL statement afterward.
    """
    schema_context = render_schema_context()
    if provider is not None:
        request = TextToSQLRequest(
            question=question,
            schema_context=schema_context,
            system_prompt=load_prompt("system_prompt.md"),
            text_to_sql_prompt=load_prompt("text_to_sql.md"),
            user_role=user_role,
        )
        return provider.generate_query_plan(request)

    _ = user_role, schema_context, retrieve_context(question)

    if _looks_like_analytics_question(question):
        return QueryPlan(intent="analytics", sql=_build_placeholder_sql(question))

    return QueryPlan(intent="knowledge")


def answer_from_context(question: str, user_role: str | None = None) -> str:
    return (
        "สวัสดีครับ! ผมคือผู้ช่วย AI วิเคราะห์ข้อมูลคลังสินค้าเกษตร (AgriChain) "
        "คุณสามารถสอบถามข้อมูลเชิงวิเคราะห์ เช่น ยอดขายสุทธิรายเดือน, ปริมาณการรับซื้อผลผลิต, "
        "สต็อกคงคลังในแต่ละคลัง หรือแนวโน้มการเติบโตของสินค้าเกษตรได้เลยครับ"
    )


def _looks_like_analytics_question(question: str) -> bool:
    keywords = ["ยอดขาย", "รับซื้อ", "คงคลัง", "จัดส่ง", "warehouse", "sales", "harvest"]
    return any(keyword.lower() in question.lower() for keyword in keywords)


def _build_placeholder_sql(question: str) -> str:
    if "ยอดขาย" in question or "sales" in question.lower():
        return f"""
        SELECT d.year, d.month, SUM(s.total_amount_thb * (1 - COALESCE(s.discount_pct, 0) / 100.0)) AS net_sales_thb
        FROM {DATABASE_SCHEMA}.fact_sales s
        JOIN {DATABASE_SCHEMA}.dim_date d ON d.date_key = s.sale_date_key
        GROUP BY d.year, d.month
        ORDER BY d.year, d.month
        LIMIT 100
        """.strip()

    if "รับซื้อ" in question or "harvest" in question.lower():
        return f"""
        SELECT d.year, d.month, SUM(h.total_amount_thb) AS total_harvest_amount_thb
        FROM {DATABASE_SCHEMA}.fact_harvest h
        JOIN {DATABASE_SCHEMA}.dim_date d ON d.date_key = h.harvest_date_key
        GROUP BY d.year, d.month
        ORDER BY d.year, d.month
        LIMIT 100
        """.strip()

    return f"""
    SELECT COUNT(*) AS row_count
    FROM {DATABASE_SCHEMA}.fact_inventory
    LIMIT 100
    """.strip()


def summarize_rows(
    question: str,
    rows: list[dict],
    user_role: str | None = None,
    provider: LLMProvider | None = None,
) -> str:
    if not rows:
        return "ไม่พบข้อมูลที่ตรงกับเงื่อนไขในฐานข้อมูล (ผลการค้นหาเป็น 0 แถว)"

    if provider is not None:
        try:
            return provider.summarize_query_result(
                SummarizationRequest(
                    question=question,
                    rows=rows,
                    user_role=user_role,
                )
            )
        except Exception:
            pass

    return f"ดึงข้อมูลจากระบบสำเร็จ พบข้อมูลจำนวน {len(rows)} รายการ ได้แสดงผลลัพธ์ลงในกราฟและตารางวิเคราะห์เรียบร้อยแล้วครับ"
