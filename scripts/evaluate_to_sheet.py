import csv
import json
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.core.config import settings
from app.providers.factory import get_configured_provider
from app.services.query_workflow import run_query_workflow


BENCHMARK_PATH = PROJECT_ROOT / "tests" / "benchmarks" / "text_to_sql_th.json"
OUTPUT_CSV_PATH = PROJECT_ROOT / "evaluation_results.csv"


def main() -> int:
    provider = get_configured_provider()
    provider_name = provider.name if provider else "none"
    model_name = getattr(provider, "model", "default")

    print(f"=== Starting Model Evaluation for Sheet ===")
    print(f"Provider: {provider_name} | Model: {model_name}")
    print(f"Database: {settings.database_url}\n")

    if not BENCHMARK_PATH.exists():
        print(f"Error: {BENCHMARK_PATH} not found.")
        return 1

    benchmark_data = json.loads(BENCHMARK_PATH.read_text(encoding="utf-8"))
    cases = benchmark_data.get("cases", [])

    results = []
    print(f"Running {len(cases)} evaluation cases...")

    for i, case in enumerate(cases, 1):
        cid = case["id"]
        question = case["question"]
        category = case.get("category", "")
        difficulty = case.get("difficulty", "")
        ref_sql = case.get("reference_sql", "")

        print(f"[{i}/{len(cases)}] Evaluating {cid} ({difficulty}) - {question[:30]}...")

        start_time = time.perf_counter()
        try:
            agent_result = run_query_workflow(question=question, provider=provider)
            latency = round(time.perf_counter() - start_time, 2)
            status = agent_result.status
            gen_sql = agent_result.sql or ""
            answer = agent_result.answer or ""
            violations = "; ".join(agent_result.guardrail_violations) if agent_result.guardrail_violations else ""
            has_chart = "Yes" if agent_result.visualization else "No"
            sources = ", ".join(agent_result.sources) if agent_result.sources else ""
        except Exception as exc:
            latency = round(time.perf_counter() - start_time, 2)
            status = "error"
            gen_sql = ""
            answer = str(exc)
            violations = type(exc).__name__
            has_chart = "No"
            sources = ""

        results.append({
            "ID": cid,
            "Difficulty": difficulty,
            "Category": category,
            "Question": question,
            "Reference_SQL": ref_sql,
            "Generated_SQL": gen_sql,
            "Status": status,
            "Guardrail_Violations": violations,
            "Model_Answer": answer,
            "Has_Chart": has_chart,
            "Latency_Seconds": latency,
            "Sources": sources,
            "Provider": provider_name,
            "Model": model_name
        })

    # Export to CSV with UTF-8 BOM for Microsoft Excel compatibility
    fieldnames = [
        "ID", "Difficulty", "Category", "Question",
        "Generated_SQL", "Reference_SQL", "Status",
        "Guardrail_Violations", "Model_Answer", "Has_Chart",
        "Latency_Seconds", "Sources", "Provider", "Model"
    ]

    with open(OUTPUT_CSV_PATH, mode="w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)

    print(f"\n Evaluation complete!")
    print(f"Results exported to: {OUTPUT_CSV_PATH}")
    print(f"Total cases: {len(results)} | Passed: {sum(1 for r in results if r['Status'] == 'answered')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
