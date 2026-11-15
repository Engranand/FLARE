"""Mock LLM provider for unit and deterministic integration testing."""
from __future__ import annotations

import json
from typing import Any, Callable

from app.intelligence.llm.base import (
    BaseLLMProvider,
    LLMResponse,
    ProviderUnavailableError,
)


class MockLLMProvider(BaseLLMProvider):
    """Configurable mock provider that returns canned responses or runs custom handlers."""

    def __init__(
        self,
        default_response: str | dict[str, Any] | None = None,
        available: bool = True,
        simulate_error: Exception | None = None,
        handler: Callable[[str, str | None], str | dict[str, Any]] | None = None,
    ) -> None:
        self._default_response = default_response
        self._available = available
        self._simulate_error = simulate_error
        self._handler = handler
        self.invocation_count = 0
        self.last_prompt: str | None = None
        self.last_system_prompt: str | None = None

    @property
    def provider_name(self) -> str:
        return "mock"

    @property
    def model_name(self) -> str:
        return "mock-flare-v1"

    def is_available(self) -> bool:
        return self._available

    def generate_sync(
        self,
        prompt: str,
        system_prompt: str | None = None,
        response_format: str | None = None,
        temperature: float = 0.1,
    ) -> LLMResponse:
        self.invocation_count += 1
        self.last_prompt = prompt
        self.last_system_prompt = system_prompt

        if not self._available:
            raise ProviderUnavailableError("Mock provider configured as offline", provider="mock")

        if self._simulate_error is not None:
            raise self._simulate_error

        if self._handler is not None:
            res = self._handler(prompt, system_prompt)
            content = json.dumps(res) if isinstance(res, dict) else str(res)
            return LLMResponse(
                content=content,
                model="mock-flare-v1",
                provider="mock",
                duration_seconds=0.01,
            )

        if self._default_response is not None:
            content = (
                json.dumps(self._default_response)
                if isinstance(self._default_response, dict)
                else str(self._default_response)
            )
            return LLMResponse(
                content=content,
                model="mock-flare-v1",
                provider="mock",
                duration_seconds=0.01,
            )

        # Default fallback synthesis JSON payload
        default_json = {
            "answer": "Mock synthesized answer grounded in provided evidence.",
            "key_findings": ["Finding 1 from empirical records", "Finding 2 from literature"],
            "scientific_claims": [],
            "uncertainty_and_limitations": ["Limited to BASS-II flight data."],
            "epistemic_status": "SUPPORTED",
        }
        return LLMResponse(
            content=json.dumps(default_json),
            model="mock-flare-v1",
            provider="mock",
            duration_seconds=0.01,
        )
