# Agent Team Factory

A greenfield, spec-driven platform for designing, configuring, validating, evaluating, and eventually deploying specialized AI agent teams.

Current completed scope: **Phase 0, Phase 1, Phase 2, Phase 3, and Phase 4**.

Implemented now:

- Repository and documentation skeleton.
- Static local planning/progress website under `site/`.
- Minimal Pydantic data models for agent-team specs.
- YAML loading and validation.
- Example specs for scientific discovery, trading strategy research, and travel planning.
- Unit tests for valid and invalid spec validation behavior.
- Deterministic mock orchestrator for sequential workflows.
- Manifest-only tool registry and permission decisions.
- Local SQLite memory foundation with retention and redaction.

Not implemented yet:

- Real LLM orchestration.
- Non-sequential workflow runtime semantics.
- Tool execution.
  - Phase 3 can authorize proposed calls but intentionally does not execute them.
- Runtime memory integration.
- Vector memory and semantic retrieval.
- Evaluation runtime.
- CLI workflows beyond skeleton scripts.
- Deployment.

## Validate locally

```bash
~/.venvs/myenv/bin/python -m pytest
~/.venvs/myenv/bin/python scripts/validate_specs.py team_specs/*.yaml
```

## Run a deterministic mock workflow

The Phase 2 runtime supports sequential workflows only.

```python
from team_factory.specs.loader import load_team_spec
from team_factory.orchestration.compiler import compile_workflow

spec = load_team_spec("team_specs/travel_planning_team.yaml")
workflow = compile_workflow(spec, "plan_trip")
result = workflow.run("Plan a three-day museum-focused trip under $1,500.")
print(result.final_output)
```

## Check a tool authorization decision

The Phase 3 tool layer is manifest-only: it can authorize or block proposed calls, but it does not execute them.

```python
from team_factory.specs.loader import load_team_spec
from team_factory.tools import ToolCallRequest, ToolRegistry

spec = load_team_spec("team_specs/travel_planning_team.yaml")
registry = ToolRegistry.from_team_spec(spec)
request = ToolCallRequest(
    tool_id="web_search",
    agent_id="destination_researcher",
    purpose="Research museum opening hours.",
)
print(registry.authorize(request).status)
```

## Store local memory with redaction

The Phase 4 memory layer is standalone and local. It does not automatically feed agent prompts yet.

```python
from team_factory.memory import MemoryCategory, SQLiteMemoryStore

with SQLiteMemoryStore("local_memory.sqlite3") as store:
    record = store.put(
        category=MemoryCategory.PROJECT,
        key="decision:architecture",
        value={"decision": "Use specs first.", "api_key": "secret"},
        retention_days=365,
    )
    print(record.value)
```

## View the local website

Open this file in a browser:

```text
site/index.html
```

It summarizes the implementation plan and current progress.
