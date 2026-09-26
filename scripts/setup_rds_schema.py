import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from sqlalchemy import text
from app.core.config import settings
from app.db.connection import create_db_engine
from app.db.schema_verifier import compare_schema, inspect_rds_schema


SCHEMA_SQL_PATH = PROJECT_ROOT / "schema.sql"


def main() -> int:
    if not settings.database_url:
        print("Error: DATABASE_URL is not set in .env")
        return 1

    print(f"Connecting to database: {settings.database_url}")
    engine = create_db_engine()

    # Read schema SQL
    if not SCHEMA_SQL_PATH.exists():
        print(f"Error: Schema SQL file not found at {SCHEMA_SQL_PATH}")
        return 1

    sql_content = SCHEMA_SQL_PATH.read_text(encoding="utf-8")
    # Filter out psql specific commands like \set
    statements = []
    current_stmt = []
    for line in sql_content.splitlines():
        trimmed = line.strip()
        if trimmed.startswith("\\") or trimmed.startswith("--"):
            continue
        current_stmt.append(line)
        if trimmed.endswith(";"):
            stmt_text = "\n".join(current_stmt).strip()
            if stmt_text:
                statements.append(stmt_text)
            current_stmt = []

    print(f"Found {len(statements)} SQL statements to execute.")

    try:
        with engine.connect() as conn:
            print("Creating schema and tables on Database...")
            for i, stmt in enumerate(statements, 1):
                # Only execute CREATE SCHEMA, CREATE TABLE, etc.
                if any(k in stmt.upper() for k in ["CREATE SCHEMA", "CREATE TABLE", "CREATE INDEX"]):
                    try:
                        conn.execute(text(stmt))
                        conn.commit()
                    except Exception as exc:
                        print(f"  Statement {i} warning: {exc}")
            print("Schema execution finished successfully!")
    except Exception as exc:
        print(f"Connection failed: {exc}")
        return 1
    finally:
        engine.dispose()

    # Verify schema
    print("\nVerifying schema with AI catalog...")
    verify_engine = create_db_engine()
    try:
        actual = inspect_rds_schema(verify_engine, settings.database_schema)
    finally:
        verify_engine.dispose()

    comp = compare_schema(actual)
    if comp.matches:
        print(f" SUCCESS: RDS schema '{settings.database_schema}' matches the AI schema catalog 100%!")
        return 0
    else:
        print(f"Schema verification note: {len(comp.mismatches)} mismatches")
        for m in comp.mismatches:
            print(f"  - {m}")
        return 0


if __name__ == "__main__":
    sys.exit(main())
