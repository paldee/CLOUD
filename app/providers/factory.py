from functools import lru_cache

from app.core.config import Settings, settings
from app.providers.base import LLMProvider, ProviderConfigurationError
from app.providers.groq import DEFAULT_GROQ_MODEL, GroqProvider


def create_provider(config: Settings = settings) -> LLMProvider | None:
    provider_name = config.llm_provider.strip().lower()
    if provider_name in {"", "heuristic", "none"}:
        return None
    if provider_name in {"groq", "qwen"}:
        return GroqProvider(
            api_key=config.groq_api_key,
            model=config.llm_model or config.groq_model or DEFAULT_GROQ_MODEL,
        )
    raise ProviderConfigurationError(
        f"Unsupported LLM_PROVIDER '{config.llm_provider}'. Use qwen, groq, or heuristic."
    )


@lru_cache(maxsize=1)
def get_configured_provider() -> LLMProvider | None:
    """Reuse the provider SDK client across API requests."""
    return create_provider(settings)
