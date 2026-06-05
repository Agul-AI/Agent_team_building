from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

import pytest

from team_factory.llm import (
    DeterministicLLMAdapter,
    LLMAdapterConfig,
    LLMAdapterError,
    LLMProvider,
    LLMRequest,
    OpenAIResponsesLLMAdapter,
    build_llm_adapter,
)


class FakeHeaders(dict):
    def get(self, key: str, default: Any = None) -> Any:
        return super().get(key, default)


@dataclass
class FakeHTTPResponse:
    payload: dict[str, Any]
    headers: FakeHeaders

    def __enter__(self) -> FakeHTTPResponse:
        return self

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> None:
        return None

    def read(self) -> bytes:
        return json.dumps(self.payload).encode("utf-8")


class FakeOpener:
    def __init__(self) -> None:
        self.requests = []

    def open(self, request, timeout: float):
        self.requests.append((request, timeout))
        return FakeHTTPResponse(
            payload={
                "id": "resp_test",
                "model": "gpt-test",
                "output_text": "real provider text",
                "usage": {"input_tokens": 1, "output_tokens": 2},
            },
            headers=FakeHeaders({"x-request-id": "req_test"}),
        )


def test_deterministic_llm_adapter_is_default_and_stable() -> None:
    adapter = DeterministicLLMAdapter()

    response = adapter.generate(LLMRequest(prompt="Hello", instructions="Be concise."))

    assert response.provider == "deterministic"
    assert response.model == "deterministic-mock"
    assert "prompt=Hello" in response.text
    assert response.raw_response == {"deterministic": True}


def test_build_llm_adapter_returns_deterministic_adapter() -> None:
    adapter = build_llm_adapter(LLMAdapterConfig())

    assert isinstance(adapter, DeterministicLLMAdapter)


def test_real_llm_config_requires_explicit_enable(monkeypatch) -> None:
    monkeypatch.setenv("TEAM_FACTORY_ENABLE_REAL_LLM", "1")

    with pytest.raises(ValueError, match="enable_real_llm"):
        LLMAdapterConfig(provider=LLMProvider.OPENAI_RESPONSES, model="gpt-test")


def test_real_llm_config_requires_environment_gate(monkeypatch) -> None:
    monkeypatch.delenv("TEAM_FACTORY_ENABLE_REAL_LLM", raising=False)

    with pytest.raises(ValueError, match="TEAM_FACTORY_ENABLE_REAL_LLM"):
        LLMAdapterConfig(
            provider=LLMProvider.OPENAI_RESPONSES,
            model="gpt-test",
            enable_real_llm=True,
        )


def test_openai_adapter_requires_api_key(monkeypatch) -> None:
    monkeypatch.setenv("TEAM_FACTORY_ENABLE_REAL_LLM", "1")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    config = LLMAdapterConfig(
        provider=LLMProvider.OPENAI_RESPONSES,
        model="gpt-test",
        enable_real_llm=True,
    )

    with pytest.raises(LLMAdapterError, match="missing API key"):
        OpenAIResponsesLLMAdapter(config)


def test_openai_adapter_payload_disables_tools(monkeypatch) -> None:
    monkeypatch.setenv("TEAM_FACTORY_ENABLE_REAL_LLM", "1")
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    opener = FakeOpener()
    config = LLMAdapterConfig(
        provider=LLMProvider.OPENAI_RESPONSES,
        model="gpt-test",
        enable_real_llm=True,
        max_output_tokens=42,
        temperature=0.1,
    )
    adapter = OpenAIResponsesLLMAdapter(config, opener=opener)

    response = adapter.generate(LLMRequest(prompt="Hello", instructions="No tools."))

    assert response.provider == "openai_responses"
    assert response.text == "real provider text"
    assert response.request_id == "req_test"
    assert response.usage == {"input_tokens": 1, "output_tokens": 2}
    request, timeout = opener.requests[0]
    payload = json.loads(request.data.decode("utf-8"))
    assert timeout == 30.0
    assert request.full_url == "https://api.openai.com/v1/responses"
    assert payload == {
        "model": "gpt-test",
        "input": "Hello",
        "instructions": "No tools.",
        "tools": [],
        "tool_choice": "none",
        "parallel_tool_calls": False,
        "max_output_tokens": 42,
        "temperature": 0.1,
    }
    assert request.headers["Authorization"] == "Bearer test-key"
