from types import SimpleNamespace

import pytest

from app.providers.base import (
    ProviderConfigurationError,
    ProviderError,
    SummarizationRequest,
    TextToSQLRequest,
)
from app.providers.groq import GroqProvider


class FakeGroqCompletions:
    def __init__(self, contents: list[str]) -> None:
        self.contents = contents
        self.calls: list[dict] = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        content = self.contents.pop(0)
        return SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content=content))]
        )


def text_to_sql_request() -> TextToSQLRequest:
    return TextToSQLRequest(
        question="รับซื้อทั้งหมดกี่กิโลกรัม",
        schema_context="TABLE: data_warehouse.fact_harvest",
        system_prompt="system",
        text_to_sql_prompt="schema={schema_context}\nquestion={question}",
    )


def test_groq_generates_typed_query_plan_and_summary() -> None:
    completions = FakeGroqCompletions(
        [
            '{"intent":"analytics","sql":"SELECT SUM(quantity_kg) FROM data_warehouse.fact_harvest","assumptions":[]}',
            "รับซื้อรวม 250 กิโลกรัม",
        ]
    )
    client = SimpleNamespace(
        chat=SimpleNamespace(completions=completions)
    )
    provider = GroqProvider(api_key=None, model="qwen-test", client=client)

    plan = provider.generate_query_plan(text_to_sql_request())
    summary = provider.summarize_query_result(
        SummarizationRequest(
            question="รับซื้อทั้งหมดกี่กิโลกรัม",
            rows=[{"total_harvest_kg": 250}],
        )
    )

    assert plan.intent == "analytics"
    assert plan.sql is not None
    assert summary == "รับซื้อรวม 250 กิโลกรัม"
    assert completions.calls[0]["model"] == "qwen-test"
    assert completions.calls[0]["response_format"] == {"type": "json_object"}
    assert completions.calls[0]["reasoning_effort"] == "none"
    assert "ผลลัพธ์ฐานข้อมูล" in completions.calls[1]["messages"][1]["content"]


def test_groq_requires_key_when_no_client_is_injected() -> None:
    with pytest.raises(ProviderConfigurationError, match="GROQ_API_KEY"):
        GroqProvider(api_key=None)


def test_groq_rejects_non_json_query_plan() -> None:
    completions = FakeGroqCompletions(["not-json", "still-not-json"])
    client = SimpleNamespace(chat=SimpleNamespace(completions=completions))
    provider = GroqProvider(api_key=None, client=client)

    with pytest.raises(ProviderError, match="after 2 attempts"):
        provider.generate_query_plan(text_to_sql_request())

    assert len(completions.calls) == 2


def test_groq_retries_invalid_query_plan_once() -> None:
    completions = FakeGroqCompletions(
        [
            "not-json",
            '{"intent":"analytics","sql":"SELECT SUM(quantity_kg) '
            'FROM data_warehouse.fact_harvest","assumptions":[]}',
        ]
    )
    client = SimpleNamespace(chat=SimpleNamespace(completions=completions))
    provider = GroqProvider(api_key=None, client=client)

    plan = provider.generate_query_plan(text_to_sql_request())

    assert plan.intent == "analytics"
    assert len(completions.calls) == 2
