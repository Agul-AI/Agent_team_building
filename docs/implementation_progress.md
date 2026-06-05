# Implementation Progress

## Snapshot

Phase 0, Phase 1, Phase 2, Phase 3, Phase 4, Phase 5, Phase 6, Phase 7, and Phase 8 are implemented locally. Phase 8 adds a local API skeleton and structured JSONL audit/run observability.

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

Harden the platform by adding regression trace snapshots and replay-oriented run-log persistence before introducing real LLM/tool execution.
