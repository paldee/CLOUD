import pytest

from app.core.config import Settings
from app.providers.base import ProviderConfigurationError
from app.providers.factory import create_provider


def test_heuristic_provider_keeps_local_skeleton_available() -> None:
    config = Settings(_env_file=None, llm_provider="heuristic")

    assert create_provider(config) is None


def test_qwen_provider_alias_uses_groq() -> None:
    config = Settings(
        _env_file=None,
        llm_provider="qwen",
        groq_api_key="mock_key",
    )
    provider = create_provider(config)
    assert provider is not None
    assert provider.name == "groq"


def test_groq_configuration_requires_api_key() -> None:
    config = Settings(
        _env_file=None,
        llm_provider="groq",
        groq_api_key=None,
    )

    with pytest.raises(ProviderConfigurationError, match="GROQ_API_KEY"):
        create_provider(config)


def test_unknown_provider_is_rejected() -> None:
    config = Settings(_env_file=None, llm_provider="unknown")

    with pytest.raises(ProviderConfigurationError, match="Unsupported LLM_PROVIDER"):
        create_provider(config)
