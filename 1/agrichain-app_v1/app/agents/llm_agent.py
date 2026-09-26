from pathlib import Path

from app.agents.state import QueryPlan
from app.db.schema_catalog import render_schema_context
from app.tools.rag_tool import retrieve_context


PROMPT_DIR = Path(__file__).resolve().parents[1] / "prompts"


def load_prompt(name: str) -> str:
    return (PROMPT_DIR / name).read_text(encoding="utf-8")


def create_query_plan(question: str, user_role: str | None = None) -> QueryPlan:
    """
    Framework-neutral LLM boundary.

    Replace the heuristic with a provider call that returns a typed QueryPlan.
    The workflow must still validate every generated SQL statement afterward.
    """
    _ = user_role, render_schema_context(), retrieve_context(question)

    if _looks_like_analytics_question(question):
        return QueryPlan(intent="analytics", sql=_build_placeholder_sql(question))

    return QueryPlan(intent="knowledge")


def answer_from_context(question: str, user_role: str | None = None) -> str:
    schema_context = render_schema_context()
    rag_context = retrieve_context(question)
    return (
        "ยังไม่ได้ต่อ LLM provider จริงใน skeleton นี้ "
        "แต่ agent ได้เตรียม context สำหรับตอบคำถามแล้ว: "
        f"role={user_role or 'ไม่ระบุ'}, schema_tables={schema_context.count('- ')}, "
        f"rag_context_items={len(rag_context)}"
    )


def _looks_like_analytics_question(question: str) -> bool:
    keywords = ["ยอดขาย", "รับซื้อ", "คงคลัง", "จัดส่ง", "warehouse", "sales", "harvest"]
    return any(keyword.lower() in question.lower() for keyword in keywords)


def _build_placeholder_sql(question: str) -> str:
    if "ยอดขาย" in question or "sales" in question.lower():
        return """
        SELECT d.year, d.month, SUM(s.total_amount_thb * (1 - COALESCE(s.discount_pct, 0) / 100.0)) AS net_sales_thb
        FROM data_warehouse.fact_sales s
        JOIN data_warehouse.dim_date d ON d.date_key = s.sale_date_key
        GROUP BY d.year, d.month
        ORDER BY d.year, d.month
        LIMIT 100
        """.strip()

    if "รับซื้อ" in question or "harvest" in question.lower():
        return """
        SELECT d.year, d.month, SUM(h.total_amount_thb) AS total_harvest_amount_thb
        FROM data_warehouse.fact_harvest h
        JOIN data_warehouse.dim_date d ON d.date_key = h.harvest_date_key
        GROUP BY d.year, d.month
        ORDER BY d.year, d.month
        LIMIT 100
        """.strip()

    return """
    SELECT COUNT(*) AS row_count
    FROM data_warehouse.fact_inventory
    LIMIT 100
    """.strip()


def summarize_rows(question: str, rows: list[dict]) -> str:
    if not rows:
        return "ยังไม่พบข้อมูลจากฐานข้อมูล หรือยังไม่ได้ตั้งค่า DATABASE_URL สำหรับ query จริง"

    return (
        f"คำถาม: {question}\n"
        f"พบผลลัพธ์ {len(rows)} แถว ตัวอย่างแถวแรก: {rows[0]}\n"
        "ขั้นถัดไปควรแทนส่วนนี้ด้วย LLM summarizer เพื่อเล่า insight เป็นภาษาไทย"
    )
