from app.agents.llm_agent import create_query_plan, summarize_rows
from app.agents.state import QueryPlan
from app.providers.base import LLMProvider, SummarizationRequest, TextToSQLRequest


class FakeProvider:
    name = "fake"

    def __init__(self) -> None:
        self.query_request: TextToSQLRequest | None = None
        self.summary_request: SummarizationRequest | None = None

    def generate_query_plan(self, request: TextToSQLRequest) -> QueryPlan:
        self.query_request = request
        return QueryPlan(
            intent="analytics",
            sql="SELECT COUNT(sales_id) AS sale_count FROM data_warehouse.fact_sales",
        )

    def summarize_query_result(self, request: SummarizationRequest) -> str:
        self.summary_request = request
        return f"พบ {request.rows[0]['sale_count']} รายการ"


def test_provider_protocol_and_text_to_sql_request() -> None:
    provider = FakeProvider()

    plan = create_query_plan(
        question="มีรายการขายกี่รายการ",
        user_role="analyst",
        provider=provider,
    )

    assert isinstance(provider, LLMProvider)
    assert plan.intent == "analytics"
    assert provider.query_request is not None
    assert provider.query_request.user_role == "analyst"
    assert "TABLE: data_warehouse.fact_sales" in provider.query_request.schema_context
    assert "{schema_context}" in provider.query_request.text_to_sql_prompt


def test_provider_receives_only_rows_used_for_summary() -> None:
    provider = FakeProvider()
    rows = [{"sale_count": 42}]

    answer = summarize_rows(
        question="มีรายการขายกี่รายการ",
        rows=rows,
        user_role="executive",
        provider=provider,
    )

    assert answer == "พบ 42 รายการ"
    assert provider.summary_request == SummarizationRequest(
        question="มีรายการขายกี่รายการ",
        rows=rows,
        user_role="executive",
    )


def test_resolve_database_source_label() -> None:
    from app.services.query_workflow import resolve_database_source_label

    assert resolve_database_source_label(
        database_url="postgresql+psycopg://agri:pw@agri-dw.c123.ap-southeast-1.rds.amazonaws.com:5432/dw"
    ) == "amazon-rds"
    assert resolve_database_source_label(
        database_url="postgresql+psycopg://agri:pw@localhost:5433/agri_dw_local"
    ) == "local-postgres"
    assert resolve_database_source_label(
        database_url="postgresql+psycopg://agri:pw@127.0.0.1:5432/db"
    ) == "local-postgres"
    assert resolve_database_source_label(
        database_url="postgresql+psycopg://agri:pw@db.internal:5432/db",
        app_env="production",
    ) == "postgresql"
