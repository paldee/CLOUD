import logging
from dataclasses import asdict

from app.services.query_workflow import run_query_workflow
from app.providers.base import ProviderConfigurationError, ProviderError
from app.providers.factory import get_configured_provider


logger = logging.getLogger(__name__)


def answer_question(question: str, user_role: str | None = None) -> dict:
    try:
        provider = get_configured_provider()
    except ProviderConfigurationError as exc:
        return {
            "answer": f"ยังตั้งค่า LLM provider ไม่ครบ: {exc}",
            "sql": None,
            "sources": [],
            "status": "not_configured",
            "guardrail_violations": [],
        }

    try:
        result = run_query_workflow(
            question=question,
            user_role=user_role,
            provider=provider,
        )
    except ProviderError:
        logger.warning("LLM provider failed while answering a question", exc_info=True)
        return {
            "answer": "LLM provider ประมวลผลไม่สำเร็จ จึงไม่ได้เรียกฐานข้อมูล",
            "sql": None,
            "sources": [f"llm:{provider.name}"] if provider else [],
            "status": "rejected",
            "guardrail_violations": ["LLM provider error"],
        }

    return {
        "answer": result.answer,
        "sql": result.sql,
        "sources": result.sources,
        "status": result.status,
        "guardrail_violations": result.guardrail_violations,
        "visualization": (
            asdict(result.visualization) if result.visualization else None
        ),
    }
