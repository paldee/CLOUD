from app.agents.llm_agent import answer_from_context, create_query_plan, summarize_rows
from app.agents.state import AgentResult
from app.core.config import settings
from app.guardrails.sql_guard import validate_and_bound_sql
from app.tools.sql_tool import run_readonly_query


def run_query_workflow(question: str, user_role: str | None = None) -> AgentResult:
    """Run the fixed MVP workflow; the LLM never executes SQL directly."""
    plan = create_query_plan(question=question, user_role=user_role)

    if plan.intent == "knowledge":
        return AgentResult(
            answer=answer_from_context(question=question, user_role=user_role),
            sources=["schema-catalog"],
            status="not_configured",
        )

    if not plan.sql:
        return AgentResult(
            answer="Agent ไม่ได้สร้าง SQL จึงหยุดก่อนเรียกฐานข้อมูล",
            status="rejected",
            guardrail_violations=["Analytics plan must contain SQL"],
        )

    validation = validate_and_bound_sql(plan.sql)
    if not validation.allowed or validation.sql is None:
        return AgentResult(
            answer="คำสั่ง SQL ไม่ผ่าน guardrail จึงไม่ได้เรียกฐานข้อมูล",
            sql=plan.sql,
            status="rejected",
            guardrail_violations=list(validation.violations),
        )

    if not settings.database_url:
        return AgentResult(
            answer="SQL ผ่าน guardrail แล้ว แต่ยังไม่ได้ตั้งค่า DATABASE_URL",
            sql=validation.sql,
            sources=["schema-catalog"],
            status="not_configured",
        )

    rows = run_readonly_query(validation.sql)
    return AgentResult(
        answer=summarize_rows(question=question, rows=rows),
        sql=validation.sql,
        sources=["amazon-rds"],
    )
