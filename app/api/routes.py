from pydantic import BaseModel, Field
from fastapi import APIRouter

from app.services.answer_service import answer_question


router = APIRouter()


class AskRequest(BaseModel):
    question: str = Field(..., min_length=1)
    user_role: str | None = Field(default=None, description="executive, analyst, admin, etc.")


class ChartDatasetResponse(BaseModel):
    label: str
    data: list[float | None]


class ChartResponse(BaseModel):
    type: str
    title: str
    labels: list[str]
    datasets: list[ChartDatasetResponse]
    total_points: int


class AskResponse(BaseModel):
    answer: str
    sql: str | None = None
    sources: list[str] = Field(default_factory=list)
    status: str
    guardrail_violations: list[str] = Field(default_factory=list)
    visualization: ChartResponse | None = None


@router.post("/ask", response_model=AskResponse)
@router.post("/api/v1/query", response_model=AskResponse)
def ask(request: AskRequest) -> AskResponse:
    result = answer_question(question=request.question, user_role=request.user_role)
    return AskResponse(**result)
