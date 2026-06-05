# Implementation Progress

## Snapshot

Phase 0, Phase 1, Phase 2, Phase 3, Phase 4, and Phase 5 are implemented locally. Phase 5 adds a deterministic evaluation harness and Markdown scenario reports.

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

## Not started

- LangGraph adapter.
- Tool execution.
- Runtime memory integration.
- Vector memory and semantic retrieval.
- Semantic evaluation scoring, LLM judges, and domain-specific metric computation.
- CLI create/run/eval flows.
- API server.
- Deployment and monitoring.

## Next recommended phase

Phase 6: make example teams more runnable by adding sequential mock-compatible variants or expanding mock runtime support for critique-revision and supervisor-worker workflows.
