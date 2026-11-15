"""Factory function to instantiate the configured LLM provider."""
from __future__ import annotations

from app.core.config import Settings
from app.intelligence.llm.base import BaseLLMProvider
from app.intelligence.llm.mock import MockLLMProvider
from app.intelligence.llm.ollama import OllamaProvider


def get_llm_provider(settings: Settings | None = None) -> BaseLLMProvider:
    """Instantiate and return the configured LLM provider according to settings."""
    if settings is None:
        settings = Settings()

    provider_type = (settings.llm_provider or "ollama").strip().lower()

    if provider_type == "mock":
        return MockLLMProvider()

    if provider_type == "ollama":
        return OllamaProvider(
            base_url=settings.ollama_base_url,
            model=settings.llm_model,
            timeout_seconds=settings.llm_timeout_seconds,
        )

    # Default fallback to Ollama
    return OllamaProvider(
        base_url=settings.ollama_base_url,
        model=settings.llm_model,
        timeout_seconds=settings.llm_timeout_seconds,
    )
