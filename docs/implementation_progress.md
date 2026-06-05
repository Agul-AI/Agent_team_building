# Implementation Progress

## Snapshot

Phase 0 through Phase 12 opt-in LLM adapter are implemented locally. Phase 12 adds a deterministic default LLM adapter, a Codex model identifier default, and a strict opt-in OpenAI Responses adapter path.

## Completed

- Greenfield Python project skeleton.
- Main implementation plan saved in `docs/implementation_plan.md`.
- Architecture, schema, safety, evaluation, and deployment docs skeletons.
- Static local website in `site/`.
- Pydantic models for minimal team spec schema.
- YAML loader and validation entry points.
- Example team specs:
  - scientific discovery
  - trading strategy research
  - travel planning
- Unit tests for valid specs and important invalid specs.
- Spec validation helper script.
- Deterministic mock orchestrator for sequential workflows.
- Integration tests for mock workflow compilation and execution.
- Manifest-only tool registry and permission decisions.
- Unit tests for tool allowlists, disabled tools, missing permissions, and approval gates.
- SQLite-backed local memory store.
- Deterministic redaction helper for sensitive-looking keys and secret-like strings.
- Unit tests for memory persistence, retention, deletion, export, and policy lookup.
- Deterministic evaluation harness for declared scenarios.
- Markdown evaluation report generation.
- Unit tests for executable, skipped, empty, and unknown-workflow evaluation reports.
- Mock-compatible execution for critique-revision workflows.
- Mock-compatible execution for supervisor-worker workflows.
- All three example team evaluations now pass structurally in deterministic mock mode.
- Local argparse CLI under `src/team_factory/cli/`.
- Source-checkout CLI wrapper at `scripts/team_factory_cli.py`.
- CLI tests for validation, workflow order, mock runs, tool checks, memory operations, and eval reports.
- Local API skeleton for health, spec validation, workflow order, mock runs, tool checks, and mock evals.
- Structured JSONL audit and compact run observability events.
- API/observability tests.
- Deterministic trace snapshots with stable digests.
- Trace comparison helpers.
- Replay-oriented JSONL run-log persistence.
- CLI support for trace snapshots, trace comparison, and run-log inspection.
- Checked-in golden snapshots for the three example teams.
- `golden-check` and explicit `golden-update --approve` CLI workflow.
- `scripts/ci_regression.sh` deterministic regression suite.
- `.github/workflows/ci.yml` GitHub Actions workflow.
- `scripts/release_check.sh` and `docs/release_checklist.md`.
- Provider-neutral LLM request/response models.
- Deterministic default LLM adapter.
- Default LLM model identifier set to `gpt-5.3-codex`, while provider defaults to deterministic.
- Strict opt-in OpenAI Responses adapter with no tools.
- `llm-generate` CLI command.

## Not started

- LangGraph adapter.
- Tool execution.
- Runtime memory integration.
- Vector memory and semantic retrieval.
- Semantic evaluation scoring, LLM judges, and domain-specific metric computation.
- Interactive team creation wizard.
- Production API framework/auth/RBAC.
- Deployment manifests, metrics backends, dashboards, and distributed tracing.

## Next recommended phase

Add a guarded LLM-backed single-agent smoke workflow that is excluded from CI by default and cannot call tools.
