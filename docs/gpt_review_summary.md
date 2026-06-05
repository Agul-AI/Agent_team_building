# GPT Review Summary

Date: 2026-06-05
Repository: `Agul-AI/Agent_team_building`
Local path: `/Users/cosdis/Desktop/AI_builder/AI_Team_building`

## Purpose of this file

This file gives a reviewer-oriented summary of what has been built so far, what
is intentionally not built yet, and where GPT should focus review attention.

## Product goal

The repository is a greenfield **Agent Team Factory**: a spec-driven platform for
creating reusable AI-agent teams. The system starts from YAML team specifications,
validates them with Pydantic models, runs deterministic mock workflows, checks
permissions, records observable traces, evaluates scenarios, and only later will
integrate real LLM-backed orchestration and real tool execution.

The architecture deliberately favors deterministic, reviewable foundations before
adding autonomous behavior.

## Completed implementation scope

The current completed scope is Phase 0 through Phase 12.

### Phase 0/1: repository, docs, specs, and validation

- Initialized a Python package under `src/team_factory/`.
- Added architecture and planning docs under `docs/`.
- Defined minimal Pydantic models for team specs in `src/team_factory/specs/`.
- Added YAML loading and validation.
- Added JSON schema output in `docs/team_spec.schema.json`.
- Added example team specs:
  - `team_specs/scientific_discovery_team.yaml`
  - `team_specs/trading_strategy_research_team.yaml`
  - `team_specs/travel_planning_team.yaml`
- Added validation tests in `tests/unit/test_spec_validation.py`.

### Phase 2: deterministic mock orchestrator

- Added a deterministic workflow compiler/runtime under `src/team_factory/orchestration/`.
- Implemented mock sequential workflow runs.
- Preserved deterministic run results for repeatable regression testing.
- Did not add real LLM calls or LangGraph orchestration.

### Phase 3: manifest-only tool registry

- Added tool authorization models and registry under `src/team_factory/tools/`.
- Implemented permission checks, approval requirements, and high-impact/critical
  tool safeguards.
- Tool calls are **not executed**. The registry only approves or rejects proposed
  tool-use requests.

### Phase 4: local memory foundation

- Added SQLite memory storage under `src/team_factory/memory/`.
- Implemented retention dates, deletion, listing, and simple redaction.
- Kept memory standalone; it is not yet integrated into runtime orchestration.

### Phase 5: evaluation harness

- Added deterministic mock evaluation support under `src/team_factory/evaluation/`.
- Added Markdown scenario reports and CLI/script entry points.
- Evaluation remains deterministic and scenario-based, not semantic LLM judging.

### Phase 6: more mock-compatible workflows

- Made critique-revision and supervisor-worker style examples runnable in mock
  mode.
- Expanded tests around example-team runtime behavior.

### Phase 7: CLI flows

- Added `team_factory.cli` and wrapper script `scripts/team_factory_cli.py`.
- Implemented CLI commands for validation, workflow inspection, mock runs, tool
  checks, memory, deterministic evals, trace snapshots, golden snapshots, and
  run-log inspection.

### Phase 8: local API and observability foundation

- Added dependency-light local API skeleton under `src/team_factory/api/`.
- Added structured JSONL audit/run logging under `src/team_factory/observability/`.
- Added wrapper script `scripts/team_factory_api.py`.
- The API is local-development only, not production deployment.

### Phase 9: regression trace snapshots and replay run logs

- Added deterministic trace snapshot construction and comparison.
- Added replay-oriented JSONL run-log persistence.
- Added CLI smoke flows for trace snapshots and run-log listing/getting.

### Phase 10: golden snapshots

- Added checked-in golden trace snapshots under `tests/golden_snapshots/`.
- Added explicit approval/update workflow via `golden-update --approve`.
- Added tests to prevent unintentional snapshot drift.

### Phase 11: CI-ready regression and release checklist

- Added deterministic regression script: `scripts/ci_regression.sh`.
- Added lightweight release script: `scripts/release_check.sh`.
- Added GitHub Actions workflow: `.github/workflows/ci.yml`.
- Added release checklist: `docs/release_checklist.md`.

### Phase 12: strict opt-in LLM adapter layer

- Added provider-neutral LLM models under `src/team_factory/llm/`:
  - `LLMRequest`
  - `LLMResponse`
  - `LLMAdapterConfig`
  - `LLMProvider`
- Added deterministic default adapter: `DeterministicLLMAdapter`.
- Added real-provider path: `OpenAIResponsesLLMAdapter`.
- Added `llm-generate` CLI command.
- Set the default model identifier to `gpt-5.3-codex`, with optional override
  through `TEAM_FACTORY_DEFAULT_LLM_MODEL` or `--model`.
- Real LLM usage requires all gates:
  1. provider `openai_responses`
  2. config/CLI opt-in: `enable_real_llm=True` or `--enable-real-llm`
  3. environment gate: `TEAM_FACTORY_ENABLE_REAL_LLM=1`
  4. API key from configured env var, default `OPENAI_API_KEY`
- Real LLM requests intentionally send no tools:
  - `tools=[]`
  - `tool_choice="none"`
  - `parallel_tool_calls=false`
- CI and tests use only deterministic mocks; they do not make real LLM calls.

## Current safety posture

The implementation is intentionally conservative:

- No autonomous tool execution exists.
- Real LLM usage is not default and is not used in CI.
- Tool permission checks are manifest-only.
- Golden snapshots and deterministic traces detect runtime drift.
- API server is local-only and dependency-light.
- High-impact/critical tools require explicit approval in spec validation and
  authorization flows.

## What is intentionally not implemented yet

- LLM-backed agent runtime orchestration.
- LangGraph integration.
- Real tool/function execution.
- Built-in OpenAI tool usage.
- Streaming responses.
- LLM-based evaluators/judges.
- Vector memory.
- Runtime memory integration.
- Production deployment services.
- Cost tracking and retry/backoff for real provider calls.

## Important files for review

- `README.md` — current user-facing overview and commands.
- `docs/implementation_plan.md` — phase roadmap and design intent.
- `docs/implementation_progress.md` — current status and next recommended phase.
- `docs/safety.md` — safety constraints and validation posture.
- `docs/phase_12_llm_adapter.md` — latest real-provider adapter details.
- `src/team_factory/specs/models.py` — Pydantic spec schema.
- `src/team_factory/orchestration/` — deterministic mock runtime.
- `src/team_factory/tools/` — permission checks without execution.
- `src/team_factory/memory/` — local SQLite memory foundation.
- `src/team_factory/evaluation/` — deterministic evaluation harness.
- `src/team_factory/observability/` — trace/golden/run-log/audit support.
- `src/team_factory/llm/` — deterministic and strict opt-in LLM adapters.
- `tests/` — unit/integration coverage and golden snapshots.
- `scripts/ci_regression.sh` — CI-ready deterministic regression suite.

## How to validate locally

From the repository root:

```bash
~/.venvs/myenv/bin/python -m pytest
~/.venvs/myenv/bin/python -m ruff check .
scripts/ci_regression.sh
scripts/release_check.sh
```

Expected current result: all tests and regression checks pass.

## Suggested GPT review checklist

1. Confirm the project still defaults to deterministic behavior.
2. Confirm no tool execution path exists outside authorization checks.
3. Confirm real LLM calls require both config and environment opt-in.
4. Confirm golden snapshot updates require explicit approval.
5. Confirm example specs validate and remain understandable.
6. Confirm CLI/API flows match the documented safety boundaries.
7. Confirm next implementation phases preserve deterministic regression coverage.

## Next recommended implementation phase

Add a guarded LLM-backed single-agent smoke workflow that:

- is excluded from CI by default,
- cannot call tools,
- logs prompt/response metadata safely,
- can be run only with explicit real-LLM opt-in,
- preserves deterministic mocks as the default runtime path.
