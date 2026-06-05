# Agent Team Factory

A greenfield, spec-driven platform for designing, configuring, validating, evaluating, and eventually deploying specialized AI agent teams.

Current scope: **Phase 0 and Phase 1 only**.

Implemented now:

- Repository and documentation skeleton.
- Static local planning/progress website under `site/`.
- Minimal Pydantic data models for agent-team specs.
- YAML loading and validation.
- Example specs for scientific discovery, trading strategy research, and travel planning.
- Unit tests for valid and invalid spec validation behavior.

Not implemented yet:

- Runtime orchestration.
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

## View the local website

Open this file in a browser:

```text
site/index.html
```

It summarizes the implementation plan and current progress.
