from app.agents.llm_agent import answer_from_context, create_query_plan, summarize_rows
from app.agents.state import AgentResult
from app.core.config import settings
from app.guardrails.sql_guard import validate_and_bound_sql
from app.providers.base import LLMProvider
from app.tools.sql_tool import run_readonly_query
from app.visualization.chart_builder import build_chart_spec


def resolve_database_source_label(database_url: str = "", app_env: str = "") -> str:
    url = (database_url or settings.database_url or "").lower()
    env = (app_env or settings.app_env or "").lower()
    if "rds.amazonaws.com" in url or "amazonaws.com" in url:
        return "amazon-rds"
    if "localhost" in url or "127.0.0.1" in url or env == "local":
        return "local-postgres"
    return "postgresql"


def run_query_workflow(
    question: str,
    user_role: str | None = None,
    provider: LLMProvider | None = None,
) -> AgentResult:
    """Run the fixed MVP workflow; the LLM never executes SQL directly."""
    plan = create_query_plan(
        question=question,
        user_role=user_role,
        provider=provider,
    )

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
            sources=[
                "schema-catalog",
                *([f"llm:{provider.name}"] if provider else []),
            ],
            status="not_configured",
        )

    try:
        rows = run_readonly_query(validation.sql)
    except Exception as exc:
        return AgentResult(
            answer=f"สร้าง SQL สำเร็จและผ่าน Guardrail แล้ว แต่ไม่สามารถเชื่อมต่อฐานข้อมูลได้ (กรุณาตรวจสอบว่า Amazon RDS เปิดใช้งานอยู่)",
            sql=validation.sql,
            sources=[
                resolve_database_source_label(),
                *([f"llm:{provider.name}"] if provider else []),
            ],
            status="database_error",
            guardrail_violations=[f"Database connection error: {exc}"],
        )

    return AgentResult(
        answer=summarize_rows(
            question=question,
            rows=rows,
            user_role=user_role,
            provider=provider,
        ),
        sql=validation.sql,
        sources=[
            resolve_database_source_label(),
            *([f"llm:{provider.name}"] if provider else []),
        ],
        visualization=build_chart_spec(question, rows),
    )
