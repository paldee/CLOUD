from pydantic import BaseModel, Field
from fastapi import APIRouter

from app.services.answer_service import answer_question


router = APIRouter()


class AskRequest(BaseModel):
    question: str = Field(..., min_length=1)
    user_role: str | None = Field(default=None, description="executive, analyst, admin, etc.")


class AskResponse(BaseModel):
    answer: str
    sql: str | None = None
    sources: list[str] = Field(default_factory=list)
    status: str
    guardrail_violations: list[str] = Field(default_factory=list)


@router.post("/ask", response_model=AskResponse)
def ask(request: AskRequest) -> AskResponse:
    result = answer_question(question=request.question, user_role=request.user_role)
    return AskResponse(**result)
