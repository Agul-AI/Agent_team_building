# Phase 12: Strict Opt-In LLM Adapter Layer

Phase 12 introduces the first real LLM adapter path behind deterministic mocks.
The deterministic adapter remains the default, and real providers require explicit
configuration and environment opt-in.

## Implemented

- Provider-neutral `LLMRequest` and `LLMResponse` models.
- `LLMAdapter` interface.
- `DeterministicLLMAdapter` default test adapter.
- `OpenAIResponsesLLMAdapter` strict opt-in adapter.
- `CodexExecLLMAdapter` strict opt-in adapter for local Codex CLI sign-in/quota
  without `OPENAI_API_KEY`.
- CLI command: `llm-generate`.
- Tests for deterministic output, opt-in gates, API-key gate, and OpenAI request payload shape.

## Strict opt-in rules

Real LLM providers require all of the following:

1. `provider=openai_responses` or `provider=codex_exec`
2. `enable_real_llm=True` in config, or `--enable-real-llm` in the CLI
3. environment variable `TEAM_FACTORY_ENABLE_REAL_LLM=1`
4. for `openai_responses`: an API key in the configured env var, default `OPENAI_API_KEY`
5. for `codex_exec`: a working local Codex CLI sign-in

If any gate is missing, the adapter fails before making a network request.

## No autonomous tool execution

The OpenAI Responses adapter sends plain text generation requests only. It sets:

```json
{
  "tools": [],
  "tool_choice": "none",
  "parallel_tool_calls": false
}
```

The adapter does not expose function calling, built-in tools, external tools, or
agent tool execution in this phase.

The `codex_exec` adapter uses `codex exec` in an ephemeral, read-only, isolated
temporary directory with `approval_policy="never"` and ignored user/project
rules. It is intended for smoke-test text generation through Codex quota, not
autonomous tool execution. The factory-level `gpt-5.5-codex` default is mapped
to the Codex CLI's `gpt-5.5` model id for this provider.

## CLI examples

The default model identifier is `gpt-5.5-codex` with `medium` reasoning effort.
The provider remains deterministic by default, so CI and local regression still
avoid network calls. Override the model/reasoning defaults with `--model`,
`--reasoning-effort`, `TEAM_FACTORY_DEFAULT_LLM_MODEL`, or
`TEAM_FACTORY_DEFAULT_LLM_REASONING_EFFORT`.

Deterministic default using the Codex model identifier:

```bash
~/.venvs/myenv/bin/python scripts/team_factory_cli.py llm-generate \
  "Summarize the platform in one sentence." \
  --instructions "Be concise."
```

Real OpenAI Responses adapter, explicit opt-in:

```bash
export TEAM_FACTORY_ENABLE_REAL_LLM=1
export OPENAI_API_KEY=...
~/.venvs/myenv/bin/python scripts/team_factory_cli.py llm-generate \
  "Summarize the platform in one sentence." \
  --provider openai_responses \
  --model gpt-5.5-codex \
  --reasoning-effort medium \
  --enable-real-llm
```

Codex CLI adapter, explicit opt-in, no API key:

```bash
export TEAM_FACTORY_ENABLE_REAL_LLM=1
~/.venvs/myenv/bin/python scripts/team_factory_cli.py llm-generate \
  "Summarize the platform in one sentence." \
  --provider codex_exec \
  --model gpt-5.5-codex \
  --reasoning-effort medium \
  --enable-real-llm
```

## Official API basis

The adapter uses the OpenAI Responses API endpoint:

```text
POST https://api.openai.com/v1/responses
```

with `model`, `input`, optional `instructions`, optional `max_output_tokens`,
`reasoning={"effort":"medium"}` by default, `tools=[]`, and
`tool_choice=none`.

## Still not implemented

- LLM-backed agent runtime integration.
- LLM judging/evaluation.
- Tool/function calling.
- Built-in OpenAI tools.
- Streaming.
- Retry/backoff policies.
- Cost tracking for real API calls.
- Prompt templates beyond raw prompt/instructions.

## Follow-up

The guarded LLM-backed single-agent smoke workflow was added in Phase 13.
