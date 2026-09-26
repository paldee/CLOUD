import json
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from sqlalchemy import create_engine, text

from app.core.config import settings
from app.guardrails.sql_guard import validate_and_bound_sql


BENCHMARK_PATH = PROJECT_ROOT / "tests" / "benchmarks" / "text_to_sql_th.json"


def main() -> int:
    if not settings.database_url:
        print("DATABASE_URL is not configured. Copy .env.local.example to .env first.")
        return 2

    payload = json.loads(BENCHMARK_PATH.read_text(encoding="utf-8"))
    engine = create_engine(settings.database_url, pool_pre_ping=True)
    failures: list[str] = []

    try:
        with engine.connect() as connection:
            connection.execute(
                text("SELECT set_config('statement_timeout', :timeout_value, false)"),
                {"timeout_value": f"{max(settings.max_sql_seconds, 1) * 1000}ms"},
            )
            for case in payload["cases"]:
                validation = validate_and_bound_sql(case["reference_sql"])
                if not validation.allowed or validation.sql is None:
                    failures.append(f"{case['id']}: guardrail rejected reference SQL")
                    print(f"FAIL {case['id']} guardrail")
                    continue

                try:
                    rows = connection.execute(text(validation.sql)).fetchmany(
                        settings.max_sql_rows
                    )
                except Exception as exc:
                    failures.append(f"{case['id']}: {type(exc).__name__}: {exc}")
                    print(f"FAIL {case['id']} execution")
                    continue

                print(f"PASS {case['id']} rows={len(rows)}")
    finally:
        engine.dispose()

    print(
        f"\nReference benchmark: {len(payload['cases']) - len(failures)} passed, "
        f"{len(failures)} failed"
    )
    if failures:
        print("Failures:")
        for failure in failures:
            print(f"- {failure}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
