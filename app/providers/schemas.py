from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.agents.state import QueryPlan


class QueryPlanPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    intent: Literal["analytics", "knowledge"]
    sql: str | None = None
    assumptions: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_sql_for_intent(self) -> "QueryPlanPayload":
        if self.intent == "analytics" and not (self.sql or "").strip():
            raise ValueError("Analytics query plans must contain SQL")
        if self.intent == "knowledge" and self.sql is not None:
            raise ValueError("Knowledge query plans must not contain SQL")
        return self

    def to_query_plan(self) -> QueryPlan:
        return QueryPlan(
            intent=self.intent,
            sql=self.sql,
            assumptions=list(self.assumptions),
        )
