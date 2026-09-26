import json
from collections import Counter
from pathlib import Path

from app.guardrails.sql_guard import validate_and_bound_sql


BENCHMARK_PATH = Path(__file__).parent / "benchmarks" / "text_to_sql_th.json"


def load_cases() -> list[dict]:
    payload = json.loads(BENCHMARK_PATH.read_text(encoding="utf-8"))
    return payload["cases"]


def test_benchmark_has_30_balanced_unique_cases() -> None:
    cases = load_cases()

    assert len(cases) == 30
    assert len({case["id"] for case in cases}) == 30
    assert Counter(case["difficulty"] for case in cases) == {
        "easy": 10,
        "medium": 10,
        "hard": 10,
    }


def test_every_reference_sql_passes_the_application_guardrail() -> None:
    failures: list[str] = []
    for case in load_cases():
        result = validate_and_bound_sql(case["reference_sql"])
        if not result.allowed:
            failures.append(f"{case['id']}: {result.violations}")

    assert failures == []
