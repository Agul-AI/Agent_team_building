# Agent Team Factory

A greenfield, spec-driven platform for designing, configuring, validating, evaluating, and eventually deploying specialized AI agent teams.

Current completed scope: **Phase 0, Phase 1, and Phase 2**.

Implemented now:

- Repository and documentation skeleton.
- Static local planning/progress website under `site/`.
- Minimal Pydantic data models for agent-team specs.
- YAML loading and validation.
- Example specs for scientific discovery, trading strategy research, and travel planning.
- Unit tests for valid and invalid spec validation behavior.
- Deterministic mock orchestrator for sequential workflows.

Not implemented yet:

- Real LLM orchestration.
- Non-sequential workflow runtime semantics.
- Tool execution.
- Memory persistence.
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

## View the local website

Open this file in a browser:

```text
site/index.html
```

It summarizes the implementation plan and current progress.
