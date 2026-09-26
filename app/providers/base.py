from dataclasses import dataclass
from typing import Protocol, runtime_checkable

from app.agents.state import QueryPlan


class ProviderError(RuntimeError):
    """Base error raised by an LLM provider adapter."""


class ProviderConfigurationError(ProviderError):
    """Raised when a provider is selected without required configuration."""


@dataclass(frozen=True)
class TextToSQLRequest:
    question: str
    schema_context: str
    system_prompt: str
    text_to_sql_prompt: str
    user_role: str | None = None


@dataclass(frozen=True)
class SummarizationRequest:
    question: str
    rows: list[dict]
    user_role: str | None = None


@runtime_checkable
class LLMProvider(Protocol):
    """Provider-neutral boundary used by the agent workflow."""

    @property
    def name(self) -> str:
        ...

    def generate_query_plan(self, request: TextToSQLRequest) -> QueryPlan:
        """Return a typed plan. SQL is still validated by the workflow."""
        ...

    def summarize_query_result(self, request: SummarizationRequest) -> str:
        """Summarize only the database rows included in the request."""
        ...
