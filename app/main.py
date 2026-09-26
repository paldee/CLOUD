from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from typing import Any

from app.api.routes import router
from app.core.config import settings
from app.services.query_workflow import resolve_database_source_label


app = FastAPI(title=settings.app_name)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "Authorization"],
)
app.include_router(router)


@app.get("/health")
def health_check() -> dict[str, Any]:
    active_model = settings.llm_model
    if not active_model:
        if settings.llm_provider in {"groq", "qwen"}:
            active_model = settings.groq_model

    return {
        "status": "ok",
        "env": settings.app_env,
        "llm_provider": settings.llm_provider,
        "llm_model": active_model or None,
        "database_source": resolve_database_source_label() if settings.database_url else "none",
    }
