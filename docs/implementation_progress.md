# Implementation Progress

## Snapshot

Phase 0, Phase 1, and Phase 2 are implemented locally. Phase 2 adds a deterministic mock orchestrator for sequential workflows only.

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

## Not started

- LangGraph adapter.
- Tool execution.
- Memory persistence.
- Evaluation harness execution.
- CLI create/run/eval flows.
- API server.
- Deployment and monitoring.

## Next recommended phase

Phase 3: implement the tool registry and permission layer with manifests only, without executing risky tools.
