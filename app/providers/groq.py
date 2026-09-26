import json
from typing import Any

from pydantic import ValidationError

from app.agents.state import QueryPlan
from app.providers.base import (
    ProviderConfigurationError,
    ProviderError,
    SummarizationRequest,
    TextToSQLRequest,
)
from app.providers.prompting import build_summarization_prompt, build_text_to_sql_prompt
from app.providers.schemas import QueryPlanPayload


DEFAULT_GROQ_MODEL = "qwen/qwen3.8-27b"
QUERY_PLAN_ATTEMPTS = 2


class GroqProvider:
    name = "groq"

    def __init__(
        self,
        api_key: str | None,
        model: str = DEFAULT_GROQ_MODEL,
        client: Any | None = None,
    ) -> None:
        if client is None:
            if not api_key:
                raise ProviderConfigurationError("GROQ_API_KEY is required for Groq")
            try:
                from groq import Groq
            except ImportError as exc:
                raise ProviderConfigurationError(
                    "groq is not installed; install requirements.txt"
                ) from exc
            client = Groq(api_key=api_key, max_retries=3, timeout=45.0)

        self.model = model
        self._client = client

    def generate_query_plan(self, request: TextToSQLRequest) -> QueryPlan:
        last_validation_error: Exception | None = None
        try:
            for attempt in range(QUERY_PLAN_ATTEMPTS):
                completion = self._client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": request.system_prompt},
                        {"role": "user", "content": build_text_to_sql_prompt(request)},
                    ],
                    temperature=0,
                    reasoning_effort="none",
                    response_format={"type": "json_object"},
                )
                try:
                    content = self._require_content(completion)
                    payload = QueryPlanPayload.model_validate(json.loads(content))
                    return payload.to_query_plan()
                except (
                    ProviderError,
                    json.JSONDecodeError,
                    ValidationError,
                    ValueError,
                    TypeError,
                ) as exc:
                    last_validation_error = exc
                    if attempt + 1 == QUERY_PLAN_ATTEMPTS:
                        break

            raise ProviderError(
                f"Groq returned an invalid QueryPlan after {QUERY_PLAN_ATTEMPTS} attempts: "
                f"{last_validation_error}"
            )
        except (ProviderError, ProviderConfigurationError):
            raise
        except Exception as exc:
            raise ProviderError(f"Groq request failed: {exc}") from exc

    def summarize_query_result(self, request: SummarizationRequest) -> str:
        try:
            completion = self._client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "คุณเป็นผู้ช่วยสรุปผล Data Warehouse "
                            "และต้องใช้เฉพาะข้อมูลที่ได้รับเท่านั้น"
                        ),
                    },
                    {"role": "user", "content": build_summarization_prompt(request)},
                ],
                temperature=0.1,
                reasoning_effort="none",
            )
            return self._require_content(completion)
        except ProviderError:
            raise
        except Exception as exc:
            raise ProviderError(f"Groq summarization failed: {exc}") from exc

    @staticmethod
    def _require_content(completion: Any) -> str:
        choices = getattr(completion, "choices", None)
        if not choices:
            raise ProviderError("Groq returned no completion choices")
        content = getattr(choices[0].message, "content", None)
        if not isinstance(content, str) or not content.strip():
            raise ProviderError("Groq returned an empty response")
        return content.strip()
