from dataclasses import dataclass, field
from typing import Literal

from app.visualization.chart_builder import ChartSpec


AgentStatus = Literal["answered", "rejected", "not_configured"]


@dataclass(frozen=True)
class QueryPlan:
    intent: Literal["analytics", "knowledge"]
    sql: str | None = None
    assumptions: list[str] = field(default_factory=list)


@dataclass
class AgentResult:
    answer: str
    sql: str | None = None
    sources: list[str] = field(default_factory=list)
    status: AgentStatus = "answered"
    guardrail_violations: list[str] = field(default_factory=list)
    visualization: ChartSpec | None = None
