# Phase 13: Guarded LLM-Backed Single-Agent Smoke Workflow

Phase 13 adds the first real LLM-backed workflow shape while keeping it deliberately
small and guarded. It is a **single-agent smoke test**, not full agent-team
orchestration.

## Implemented

- `run-llm-smoke` CLI command.
- `LLMSmokeRunResult` safe JSON artifact model.
- Single-agent smoke prompt builder with explicit no-tool, no-brokerage, no-trading rules.
- Safe artifact writer for smoke results.
- Unit tests for prompt safety, artifact shape, CLI guard failures, and mocked CLI success.

## Required gates

A real smoke run requires all of the following:

1. `TEAM_FACTORY_ENABLE_REAL_LLM=1`
2. `OPENAI_API_KEY` or the configured API key environment variable
3. `--provider openai_responses`
4. `--enable-real-llm`
5. `--acknowledge-no-tools`
6. `--acknowledge-simulation-only`
7. one explicit `--agent-id`

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

## Example

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
  --out examples/artifacts/strategy_building_team/llm_smoke_strategy_ideator.json
```

## Next recommended phase

Add a deterministic review wrapper around one or more LLM smoke artifacts so users
can compare real-provider output against the spec's expected safety properties
without adding autonomous tools or full orchestration.
