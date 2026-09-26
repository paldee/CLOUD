import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.core.config import settings
from app.db.connection import create_db_engine
from app.db.schema_verifier import compare_schema, inspect_rds_schema


def main() -> int:
    if not settings.database_url:
        print(
            "DATABASE_URL is not configured. Set it in .env before running "
            "the read-only RDS schema comparison."
        )
        return 2

    engine = create_db_engine()
    try:
        actual_schema = inspect_rds_schema(engine, settings.database_schema)
    finally:
        engine.dispose()

    comparison = compare_schema(actual_schema)
    if comparison.matches:
        print(
            f"RDS schema '{settings.database_schema}' matches the AI schema catalog."
        )
        return 0

    print(f"RDS schema '{settings.database_schema}' does not match the AI schema catalog:")
    for mismatch in comparison.mismatches:
        print(f"- {mismatch}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
