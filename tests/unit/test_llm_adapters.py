from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from team_factory.llm import (
    DEFAULT_LLM_MODEL,
    DEFAULT_LLM_REASONING_EFFORT,
    CodexExecLLMAdapter,
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


class FakeCodexRunner:
    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []

    def __call__(
        self,
        args: list[str],
        *,
        input: str,
        text: bool,
        capture_output: bool,
        timeout: float,
        cwd: str,
    ):
        self.calls.append(
            {
                "args": args,
                "input": input,
                "text": text,
                "capture_output": capture_output,
                "timeout": timeout,
                "cwd": cwd,
            }
        )
        output_index = args.index("--output-last-message") + 1
        Path(args[output_index]).write_text("codex provider text\n", encoding="utf-8")
        return SimpleNamespace(returncode=0, stdout="jsonl/log tail", stderr="")


def test_deterministic_llm_adapter_is_default_and_stable() -> None:
    adapter = DeterministicLLMAdapter()

    response = adapter.generate(LLMRequest(prompt="Hello", instructions="Be concise."))

    assert response.provider == "deterministic"
    assert response.model == DEFAULT_LLM_MODEL
    assert "prompt=Hello" in response.text
    assert response.raw_response == {
        "deterministic": True,
        "reasoning_effort": DEFAULT_LLM_REASONING_EFFORT,
    }


def test_build_llm_adapter_returns_deterministic_adapter() -> None:
    adapter = build_llm_adapter(LLMAdapterConfig())

    assert isinstance(adapter, DeterministicLLMAdapter)


def test_default_llm_model_and_reasoning_effort_are_overridable(monkeypatch) -> None:
    monkeypatch.delenv("TEAM_FACTORY_DEFAULT_LLM_MODEL", raising=False)
    monkeypatch.delenv("TEAM_FACTORY_DEFAULT_LLM_REASONING_EFFORT", raising=False)
    assert LLMAdapterConfig().model == DEFAULT_LLM_MODEL
    assert LLMAdapterConfig().reasoning_effort == DEFAULT_LLM_REASONING_EFFORT

    monkeypatch.setenv("TEAM_FACTORY_DEFAULT_LLM_MODEL", "custom-model")
    monkeypatch.setenv("TEAM_FACTORY_DEFAULT_LLM_REASONING_EFFORT", "high")
    assert LLMAdapterConfig().model == "custom-model"
    assert LLMAdapterConfig().reasoning_effort == "high"


def test_invalid_default_reasoning_effort_fails_validation(monkeypatch) -> None:
    monkeypatch.setenv("TEAM_FACTORY_DEFAULT_LLM_MODEL", "custom-codex")
    monkeypatch.setenv("TEAM_FACTORY_DEFAULT_LLM_REASONING_EFFORT", "maximum")

    with pytest.raises(ValueError, match="reasoning_effort"):
        LLMAdapterConfig()


def test_real_llm_config_requires_explicit_enable(monkeypatch) -> None:
    monkeypatch.setenv("TEAM_FACTORY_ENABLE_REAL_LLM", "1")

    with pytest.raises(ValueError, match="enable_real_llm"):
        LLMAdapterConfig(provider=LLMProvider.OPENAI_RESPONSES, model="gpt-test")

    with pytest.raises(ValueError, match="enable_real_llm"):
        LLMAdapterConfig(provider=LLMProvider.CODEX_EXEC, model="gpt-test")


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


def test_codex_exec_adapter_uses_locked_local_codex_command(monkeypatch) -> None:
    monkeypatch.setenv("TEAM_FACTORY_ENABLE_REAL_LLM", "1")
    runner = FakeCodexRunner()
    config = LLMAdapterConfig(
        provider=LLMProvider.CODEX_EXEC,
        model="gpt-5.5-codex",
        enable_real_llm=True,
        codex_bin="/custom/codex",
        timeout_seconds=12.0,
    )
    adapter = CodexExecLLMAdapter(config, runner=runner)

    response = adapter.generate(LLMRequest(prompt="Hello", instructions="No tools."))

    assert response.provider == "codex_exec"
    assert response.model == "gpt-5.5-codex"
    assert response.text == "codex provider text"
    call = runner.calls[0]
    args = call["args"]
    assert args[0] == "/custom/codex"
    assert args[:2] == ["/custom/codex", "exec"]
    assert "--ephemeral" in args
    assert "--ignore-user-config" in args
    assert "--ignore-rules" in args
    assert "--skip-git-repo-check" in args
    assert args[args.index("--sandbox") + 1] == "read-only"
    assert args[args.index("--config") + 1] == 'approval_policy="never"'
    assert args[args.index("--model") + 1] == "gpt-5.5"
    assert args[-1] == "-"
    assert call["cwd"] == args[args.index("--cd") + 1]
    assert call["timeout"] == 12.0
    assert "Do not run shell commands." in call["input"]
    assert "Do not call tools" in call["input"]
    assert "No tools." in call["input"]
    assert response.raw_response["isolated_empty_workdir"] is True
    assert response.raw_response["approval_policy"] == "never"
    assert response.raw_response["factory_model"] == "gpt-5.5-codex"
    assert response.raw_response["codex_cli_model"] == "gpt-5.5"


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
        reasoning_effort="medium",
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
        "reasoning": {"effort": "medium"},
    }
    assert request.headers["Authorization"] == "Bearer test-key"
