from typing import Any
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "agri-dw-llm-agent"
    app_env: str = "local"
    log_level: str = "INFO"
    cors_origins: str = (
        "http://localhost:3000,http://localhost:5173,"
        "http://127.0.0.1:3000,http://127.0.0.1:5173"
    )

    llm_provider: str = "qwen"
    llm_model: str = ""
    groq_model: str = "qwen/qwen3.8-27b"
    openai_api_key: str | None = None
    groq_api_key: str | None = None
    anthropic_api_key: str | None = None

    database_url: str = Field(default="")
    database_schema: str = "data_warehouse"

    @field_validator("database_url", mode="before")
    @classmethod
    def assemble_db_url(cls, v: Any) -> str:
        if not v or not isinstance(v, str):
            return ""
        v = v.strip()
        if not v:
            return ""
        if not (v.startswith("postgresql://") or v.startswith("postgresql+psycopg://") or v.startswith("sqlite")):
            host = v
            port = "5432"
            if ":" in host:
                parts = host.split(":", 1)
                host = parts[0]
                port = parts[1]
            return f"postgresql+psycopg://admin_agri:admin_agri_pass@{host}:{port}/postgres?sslmode=require"
        return v

    max_sql_rows: int = 100
    max_sql_seconds: int = 15

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


settings = Settings()
