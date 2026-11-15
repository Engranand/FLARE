"""Ollama local LLM provider implementation for FLARE M10.5."""
from __future__ import annotations

import json
import logging
import time
from typing import Any

import httpx

from app.intelligence.llm.base import (
    BaseLLMProvider,
    LLMResponse,
    ProviderUnavailableError,
)

logger = logging.getLogger(__name__)


class OllamaProvider(BaseLLMProvider):
    """Local Ollama LLM provider adapter using synchronous HTTP."""

    def __init__(
        self,
        base_url: str = "http://127.0.0.1:11434",
        model: str = "qwen2.5:3b",
        timeout_seconds: float = 30.0,
    ) -> None:
        # Avoid Windows localhost ::1 IPv6 DNS resolution stalls
        normalized_url = base_url.rstrip("/")
        if "localhost" in normalized_url:
            normalized_url = normalized_url.replace("localhost", "127.0.0.1")
        self._base_url = normalized_url
        self._model = model
        self._timeout = timeout_seconds

    @property
    def provider_name(self) -> str:
        return "ollama"

    @property
    def model_name(self) -> str:
        return self._model

    def is_available(self) -> bool:
        """Ping Ollama daemon with a quick 2-second timeout."""
        try:
            with httpx.Client(base_url=self._base_url, timeout=2.0) as client:
                res = client.get("/api/tags")
                if res.status_code == 200:
                    data = res.json()
                    models = [m.get("name") for m in data.get("models", [])]
                    # Check if requested model or base name is loaded
                    base_req = self._model.split(":")[0]
                    return any(
                        self._model in m or base_req in m for m in models if isinstance(m, str)
                    )
                return False
        except Exception as exc:
            logger.debug("Ollama is_available check failed: %s", exc)
            return False

    def generate_sync(
        self,
        prompt: str,
        system_prompt: str | None = None,
        response_format: str | None = None,
        temperature: float = 0.1,
    ) -> LLMResponse:
        """Call Ollama /api/generate synchronously."""
        url = f"{self._base_url}/api/generate"
        payload: dict[str, Any] = {
            "model": self._model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
            },
        }
        if system_prompt:
            payload["system"] = system_prompt
        if response_format == "json":
            payload["format"] = "json"

        start_time = time.perf_counter()
        try:
            with httpx.Client(timeout=self._timeout) as client:
                response = client.post(url, json=payload)
                response.raise_for_status()
                data = response.json()
                duration = time.perf_counter() - start_time
                content = data.get("response", "")
                return LLMResponse(
                    content=content,
                    model=self._model,
                    provider="ollama",
                    duration_seconds=round(duration, 3),
                    raw_metadata={
                        "total_duration": data.get("total_duration"),
                        "eval_count": data.get("eval_count"),
                        "eval_duration": data.get("eval_duration"),
                    },
                )
        except httpx.ConnectError as exc:
            raise ProviderUnavailableError(
                f"Cannot connect to Ollama at {self._base_url}. Ensure daemon is running.",
                provider="ollama",
                original_error=exc,
            ) from exc
        except httpx.TimeoutException as exc:
            raise ProviderUnavailableError(
                f"Ollama request timed out after {self._timeout}s.",
                provider="ollama",
                original_error=exc,
            ) from exc
        except httpx.HTTPStatusError as exc:
            raise ProviderUnavailableError(
                f"Ollama returned HTTP {exc.response.status_code}: {exc.response.text}",
                provider="ollama",
                original_error=exc,
            ) from exc
        except Exception as exc:
            raise ProviderUnavailableError(
                f"Unexpected error communicating with Ollama: {exc}",
                provider="ollama",
                original_error=exc,
            ) from exc
