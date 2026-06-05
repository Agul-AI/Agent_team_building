"""LLM adapters.

The deterministic adapter remains the default. Real-provider paths are strict
opt-in. The OpenAI Responses adapter never sends tools or executes tool calls.
The Codex exec adapter uses the local Codex CLI in an isolated read-only
noninteractive session so a user can spend Codex/ChatGPT quota without exposing
brokerage, market-data, or tool execution.
"""

from __future__ import annotations

import json
import subprocess
import tempfile
import urllib.error
import urllib.request
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Protocol

from team_factory.llm.config import LLMAdapterConfig, LLMProvider
from team_factory.llm.models import LLMRequest, LLMResponse


class LLMAdapterError(RuntimeError):
    """Raised when an LLM adapter cannot complete a request."""


class _Opener(Protocol):
    def open(self, request: urllib.request.Request, timeout: float): ...


class _CompletedProcess(Protocol):
    returncode: int
    stdout: str
    stderr: str


class _Runner(Protocol):
    def __call__(
        self,
        args: list[str],
        *,
        input: str,
        text: bool,
        capture_output: bool,
        timeout: float,
        cwd: str,
    ) -> _CompletedProcess: ...


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
            raw_response={
                "deterministic": True,
                "reasoning_effort": self.config.reasoning_effort,
            },
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
        if self.config.reasoning_effort is not None:
            payload["reasoning"] = {"effort": self.config.reasoning_effort}
        return payload


class CodexExecLLMAdapter(LLMAdapter):
    """Strict opt-in Codex CLI adapter that uses Codex sign-in/quota.

    This adapter is for local smoke tests only. It launches `codex exec` in a
    temporary empty directory, with an ephemeral session, read-only sandboxing,
    approval policy set to `never`, no project/user rules, and no persisted
    session files. That means it can ask Codex for a text answer using the
    user's existing Codex authentication, but it is not a general orchestration
    or tool-execution bridge.
    """

    def __init__(
        self,
        config: LLMAdapterConfig,
        *,
        runner: _Runner | None = None,
    ) -> None:
        if config.provider != LLMProvider.CODEX_EXEC:
            raise LLMAdapterError("CodexExecLLMAdapter requires codex_exec config")
        self.config = config
        self._runner = runner or subprocess.run

    def generate(self, request: LLMRequest) -> LLMResponse:
        with tempfile.TemporaryDirectory(prefix="team-factory-codex-smoke-") as workdir:
            output_path = Path(workdir) / "last_message.txt"
            prompt = _compose_codex_exec_prompt(request)
            command = self._build_command(workdir, output_path)
            try:
                completed = self._runner(
                    command,
                    input=prompt,
                    text=True,
                    capture_output=True,
                    timeout=self.config.timeout_seconds,
                    cwd=workdir,
                )
            except (OSError, subprocess.SubprocessError, TimeoutError) as exc:
                raise LLMAdapterError(f"Codex exec request failed: {exc}") from exc

            stdout = completed.stdout or ""
            stderr = completed.stderr or ""
            if completed.returncode != 0:
                raise LLMAdapterError(
                    "Codex exec request failed with exit code "
                    f"{completed.returncode}: {stderr or stdout}"
                )

            if output_path.exists():
                text = output_path.read_text(encoding="utf-8").strip()
            else:
                text = stdout.strip()

            return LLMResponse(
                provider=LLMProvider.CODEX_EXEC.value,
                model=self.config.model,
                text=text,
                raw_response={
                    "codex_exec": True,
                    "codex_cli_model": _codex_exec_model(self.config.model),
                    "factory_model": self.config.model,
                    "sandbox": self.config.codex_sandbox,
                    "approval_policy": self.config.codex_approval_policy,
                    "ephemeral": True,
                    "isolated_empty_workdir": True,
                    "ignore_user_config": True,
                    "ignore_rules": True,
                    "stdout_tail": stdout[-4000:],
                    "stderr_tail": stderr[-4000:],
                },
                usage=None,
            )

    def _build_command(self, workdir: str, output_path: Path) -> list[str]:
        codex_model = _codex_exec_model(self.config.model)
        return [
            self.config.codex_bin,
            "exec",
            "--ephemeral",
            "--skip-git-repo-check",
            "--ignore-user-config",
            "--ignore-rules",
            "--sandbox",
            self.config.codex_sandbox,
            "--cd",
            workdir,
            "--model",
            codex_model,
            "--config",
            f'approval_policy="{self.config.codex_approval_policy}"',
            "--output-last-message",
            str(output_path),
            "-",
        ]


def build_llm_adapter(config: LLMAdapterConfig) -> LLMAdapter:
    """Construct an adapter for a config."""

    if config.provider == LLMProvider.DETERMINISTIC:
        return DeterministicLLMAdapter(config)
    if config.provider == LLMProvider.OPENAI_RESPONSES:
        return OpenAIResponsesLLMAdapter(config)
    if config.provider == LLMProvider.CODEX_EXEC:
        return CodexExecLLMAdapter(config)
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


def _compose_codex_exec_prompt(request: LLMRequest) -> str:
    sections = [
        "You are being used as a locked-down text-generation adapter for the "
        "Agent Team Factory.",
        "Return the final answer only.",
        "Do not run shell commands.",
        "Do not inspect files.",
        "Do not call tools, apps, MCP servers, browser, market-data sources, "
        "brokerage services, or external systems.",
    ]
    if request.instructions:
        sections.extend(["", "Adapter instructions:", request.instructions])
    sections.extend(["", "Prompt:", request.prompt])
    return "\n".join(sections)


def _codex_exec_model(model: str) -> str:
    """Map factory-level Codex aliases to Codex CLI model ids."""

    aliases = {
        "gpt-5.5-codex": "gpt-5.5",
    }
    return aliases.get(model, model)
