import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.agents.llm_agent import create_query_plan
from app.core.config import settings
from app.guardrails.sql_guard import validate_and_bound_sql
from app.providers.base import LLMProvider, ProviderError
from app.providers.groq import GroqProvider


QUESTION = "ยอดขายสุทธิทั้งหมดเท่าไร"


def configured_providers() -> list[LLMProvider]:
    providers: list[LLMProvider] = []
    if settings.groq_api_key:
        providers.append(
            GroqProvider(
                api_key=settings.groq_api_key,
                model=settings.groq_model,
            )
        )
    return providers


def main() -> int:
    providers = configured_providers()
    if not providers:
        print("No provider API keys are configured in .env")
        return 2

    failures = 0
    for provider in providers:
        try:
            plan = create_query_plan(
                question=QUESTION,
                user_role="analyst",
                provider=provider,
            )
            if plan.intent != "analytics" or not plan.sql:
                print(f"FAIL {provider.name}: provider did not return analytics SQL")
                failures += 1
                continue

            validation = validate_and_bound_sql(plan.sql)
            if not validation.allowed:
                print(
                    f"FAIL {provider.name}: guardrail rejected SQL: "
                    f"{', '.join(validation.violations)}"
                )
                failures += 1
                continue

            print(f"PASS {provider.name}")
            print(f"  SQL: {validation.sql}")
            if plan.assumptions:
                print(f"  assumptions: {plan.assumptions}")
        except ProviderError as exc:
            print(f"FAIL {provider.name}: {exc}")
            failures += 1

    print(f"\nProvider smoke test: {len(providers) - failures} passed, {failures} failed")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
