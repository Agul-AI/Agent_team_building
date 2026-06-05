# Implementation Progress

## Snapshot

Phase 0, Phase 1, Phase 2, and Phase 3 are implemented locally. Phase 3 adds a manifest-only tool registry and permission layer.

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

## Not started

- LangGraph adapter.
- Tool execution.
- Memory persistence.
- Evaluation harness execution.
- CLI create/run/eval flows.
- API server.
- Deployment and monitoring.

## Next recommended phase

Phase 4: implement the memory layer foundation with local persistence and retention/redaction policies, without adding long-term vector memory yet.
