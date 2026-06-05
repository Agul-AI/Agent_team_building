"""LLM adapters.

The deterministic adapter remains the default. The OpenAI Responses adapter is a
strict opt-in provider path and never sends tools or executes tool calls.
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from abc import ABC, abstractmethod
from typing import Any, Protocol

from team_factory.llm.config import LLMAdapterConfig, LLMProvider
from team_factory.llm.models import LLMRequest, LLMResponse


class LLMAdapterError(RuntimeError):
    """Raised when an LLM adapter cannot complete a request."""


class _Opener(Protocol):
    def open(self, request: urllib.request.Request, timeout: float): ...


class LLMAdapter(ABC):
    """Provider-neutral LLM adapter interface."""

    @abstractmethod
    def generate(self, request: LLMRequest) -> LLMResponse:
        """Generate text from a provider-neutral request."""


class DeterministicLLMAdapter(LLMAdapter):
    """Deterministic test adapter used by default."""

    def __init__(self, config: LLMAdapterConfig | None = None) -> None:
        self.config = config or LLMAdapterConfig()

    def generate(self, request: LLMRequest) -> LLMResponse:
        text = (
            "[deterministic-llm] "
            f"instructions={request.instructions or 'none'} | prompt={request.prompt}"
        )
        return LLMResponse(
            provider=LLMProvider.DETERMINISTIC.value,
            model=self.config.model,
            text=text,
            raw_response={"deterministic": True},
            usage={"input_chars": len(request.prompt), "output_chars": len(text)},
        )


class OpenAIResponsesLLMAdapter(LLMAdapter):
    """Strict opt-in OpenAI Responses API adapter.

    This adapter sends plain text generation requests only. It sets `tools` to an
    empty list and does not expose function/tool calling in this phase.
    """

    def __init__(
        self,
        config: LLMAdapterConfig,
        *,
        opener: _Opener | None = None,
    ) -> None:
        if config.provider != LLMProvider.OPENAI_RESPONSES:
            raise LLMAdapterError("OpenAIResponsesLLMAdapter requires openai_responses config")
        api_key = config.api_key
        if not api_key:
            raise LLMAdapterError(f"missing API key in environment variable {config.api_key_env}")
        self.config = config
        self._api_key = api_key
        self._opener = opener or urllib.request.build_opener()

    def generate(self, request: LLMRequest) -> LLMResponse:
        payload = self._build_payload(request)
        http_request = urllib.request.Request(
            url=f"{self.config.base_url.rstrip('/')}/responses",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self._api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with self._opener.open(http_request, timeout=self.config.timeout_seconds) as response:
                response_body = response.read().decode("utf-8")
                raw = json.loads(response_body)
                request_id = response.headers.get("x-request-id")
        except urllib.error.HTTPError as exc:
            error_body = exc.read().decode("utf-8", errors="replace")
            raise LLMAdapterError(f"OpenAI Responses API error {exc.code}: {error_body}") from exc
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
            raise LLMAdapterError(f"OpenAI Responses API request failed: {exc}") from exc

        return LLMResponse(
            provider=LLMProvider.OPENAI_RESPONSES.value,
            model=str(raw.get("model", self.config.model)),
            text=_extract_response_text(raw),
            raw_response=raw,
            request_id=request_id,
            usage=raw.get("usage"),
        )

    def _build_payload(self, request: LLMRequest) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "model": self.config.model,
            "input": request.prompt,
            "tools": [],
            "tool_choice": "none",
            "parallel_tool_calls": False,
        }
        if request.instructions:
            payload["instructions"] = request.instructions
        if self.config.max_output_tokens is not None:
            payload["max_output_tokens"] = self.config.max_output_tokens
        if self.config.temperature is not None:
            payload["temperature"] = self.config.temperature
        return payload


def build_llm_adapter(config: LLMAdapterConfig) -> LLMAdapter:
    """Construct an adapter for a config."""

    if config.provider == LLMProvider.DETERMINISTIC:
        return DeterministicLLMAdapter(config)
    if config.provider == LLMProvider.OPENAI_RESPONSES:
        return OpenAIResponsesLLMAdapter(config)
    raise LLMAdapterError(f"unsupported LLM provider: {config.provider}")


def _extract_response_text(raw: dict[str, Any]) -> str:
    output_text = raw.get("output_text")
    if isinstance(output_text, str):
        return output_text

    chunks: list[str] = []
    output = raw.get("output", [])
    if isinstance(output, list):
        for item in output:
            if not isinstance(item, dict):
                continue
            content = item.get("content", [])
            if not isinstance(content, list):
                continue
            for part in content:
                if not isinstance(part, dict):
                    continue
                text = part.get("text")
                if isinstance(text, str):
                    chunks.append(text)
    return "".join(chunks)
