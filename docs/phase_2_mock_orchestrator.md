# Phase 2: Deterministic Mock Orchestrator

Phase 2 added a minimal, inspectable runtime for sequential workflows. Phase 6 later extended the same deterministic mock runtime to critique-revision and supervisor-worker workflows.

## Scope

Implemented:

- Compile a validated `TeamSpec` plus workflow id into a `CompiledWorkflow`.
- Support deterministic mock execution for `sequential` workflows.
- Phase 6 extension: support deterministic mock execution for `critique_and_revision` and `supervisor_worker` workflows.
- Emit structured run events:
  - `run_started`
  - `agent_started`
  - `agent_completed`
  - `run_completed`
  - `run_failed`
- Return a structured `RunResult` with agent outputs and final output.
- Reject unsupported workflow types with clear errors.

Not implemented:

- Real LLM calls.
- LangGraph integration.
- Tool execution.
- Memory persistence.
- Human approval runtime.
- Evaluation harness execution.
- Parallel, debate, or custom runtime semantics.
- Real critique/revision loops or true supervisor-worker dispatch.

## Why deterministic first?

A deterministic mock runtime lets the project test spec compilation, event shapes,
agent ordering, and future replay/logging assumptions before introducing LLM or tool
non-determinism.

## Example

```python
from team_factory.specs.loader import load_team_spec
from team_factory.orchestration.compiler import compile_workflow

spec = load_team_spec("team_specs/travel_planning_team.yaml")
workflow = compile_workflow(spec, "plan_trip")
result = workflow.run("Plan a three-day museum-focused trip under $1,500.")
print(result.final_output)
```
