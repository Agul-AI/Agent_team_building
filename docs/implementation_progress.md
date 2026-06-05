# Implementation Progress

## Snapshot

Phase 0 and Phase 1 are implemented in this initial repository setup.

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

## Not started

- Runtime orchestration.
- LangGraph adapter.
- Tool execution.
- Memory persistence.
- Evaluation harness execution.
- CLI create/run/eval flows.
- API server.
- Deployment and monitoring.

## Next recommended phase

Phase 2: implement a deterministic mock orchestrator for sequential workflows only, without real LLM calls or tool execution.
