# Implementation Progress

## Snapshot

Phase 0 through Phase 9 hardening are implemented locally. Phase 9 adds deterministic regression trace snapshots and replay-oriented JSONL run-log persistence.

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

Add checked-in golden snapshots and an intentional approval/update workflow before introducing real LLM/tool execution.
