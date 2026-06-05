# Phase 13: Guarded LLM-Backed Single-Agent Smoke Workflow

Phase 13 adds the first real LLM-backed workflow shape while keeping it deliberately
small and guarded. It is a **single-agent smoke test**, not full agent-team
orchestration. It now supports both:

- `openai_responses`: direct OpenAI API usage with `OPENAI_API_KEY`.
- `codex_exec`: local Codex CLI usage through the user's existing Codex/ChatGPT
  sign-in, with no API key required.

## Implemented

- `run-llm-smoke` CLI command.
- `LLMSmokeRunResult` safe JSON artifact model.
- Single-agent smoke prompt builder with explicit no-tool, no-brokerage, no-trading rules.
- Safe artifact writer for smoke results.
- `codex_exec` provider that runs `codex exec` in an ephemeral, read-only,
  isolated temporary directory with user/project rules ignored.
- Unit tests for prompt safety, artifact shape, CLI guard failures, and mocked CLI success.

## Required gates

A real smoke run always requires all of the following:

1. `TEAM_FACTORY_ENABLE_REAL_LLM=1`
2. `--enable-real-llm`
3. `--acknowledge-no-tools`
4. `--acknowledge-simulation-only`
5. one explicit `--agent-id`

Provider-specific gates:

- `--provider codex_exec`: requires the local `codex` CLI and a valid Codex
  ChatGPT sign-in. It does not require `OPENAI_API_KEY`.
- `--provider openai_responses`: requires `OPENAI_API_KEY` or the configured API
  key environment variable.

If any gate is missing, the command fails before a real provider call.

## What it does

- Loads a checked-in team spec.
- Selects exactly one agent by id.
- Builds a guarded smoke prompt from team purpose, agent role/goal, safety policy,
  prohibited actions, and task text.
- Calls the strict opt-in LLM adapter once.
- Writes a safe JSON artifact if `--out` is provided.

## What it does not do

- No multi-agent orchestration.
- No tool calls.
- No market-data fetching.
- No backtesting.
- No brokerage connections.
- No trade execution.
- No CI/default real-provider execution.

## Recommended example: use Codex quota, no API key

```bash
export TEAM_FACTORY_ENABLE_REAL_LLM=1

~/.venvs/myenv/bin/python scripts/team_factory_cli.py run-llm-smoke \
  team_specs/trading_strategy_research_team.yaml \
  "Research robust long-term trend-following strategies on ETF for simulation only." \
  --agent-id strategy_ideator \
  --provider codex_exec \
  --model gpt-5.5-codex \
  --reasoning-effort medium \
  --enable-real-llm \
  --acknowledge-no-tools \
  --acknowledge-simulation-only \
  --out examples/artifacts/strategy_building_team/llm_smoke_strategy_ideator.json
```

The `codex_exec` provider launches:

- `codex exec`
- `--ephemeral`
- `--sandbox read-only`
- `--config approval_policy="never"`
- `--ignore-user-config`
- `--ignore-rules`
- an isolated empty temporary working directory

This spends Codex usage through the user's existing Codex sign-in, but it is still
not a general autonomous Codex bridge. The factory-level default model id remains
`gpt-5.5-codex`; for this provider it is mapped to the Codex CLI model id
`gpt-5.5` when launching `codex exec`.

## Optional example: use OpenAI API credits

```bash
export TEAM_FACTORY_ENABLE_REAL_LLM=1
export OPENAI_API_KEY=...

~/.venvs/myenv/bin/python scripts/team_factory_cli.py run-llm-smoke \
  team_specs/trading_strategy_research_team.yaml \
  "Research robust long-term trend-following strategies on ETF for simulation only." \
  --agent-id strategy_ideator \
  --provider openai_responses \
  --model gpt-5.5-codex \
  --reasoning-effort medium \
  --enable-real-llm \
  --acknowledge-no-tools \
  --acknowledge-simulation-only \
  --out examples/artifacts/strategy_building_team/llm_smoke_strategy_ideator_api.json
```

## Next recommended phase

Add a deterministic review wrapper around one or more LLM smoke artifacts so users
can compare real-provider output against the spec's expected safety properties
without adding autonomous tools or full orchestration.
