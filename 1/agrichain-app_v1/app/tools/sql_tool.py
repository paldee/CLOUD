from sqlalchemy import text

from app.core.config import settings
from app.db.connection import SessionLocal
from app.guardrails.sql_guard import require_safe_sql


def run_readonly_query(sql: str) -> list[dict]:
    safe_sql = require_safe_sql(sql)

    if SessionLocal is None:
        return []

    with SessionLocal() as session:
        if session.bind is not None and session.bind.dialect.name == "postgresql":
            timeout_ms = max(settings.max_sql_seconds, 1) * 1000
            session.execute(text(f"SET LOCAL statement_timeout = {timeout_ms}"))

        result = session.execute(text(safe_sql))
        return [dict(row._mapping) for row in result.fetchmany(settings.max_sql_rows)]
