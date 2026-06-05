# Phase 10: Checked-In Golden Snapshots and Approval Workflow

Phase 10 adds checked-in golden snapshots for the three example teams and an
explicit approval/update workflow. This creates a stable regression baseline
before adding real LLM calls or actual tool execution.

## Implemented

- `tests/golden_snapshots/` contains deterministic trace snapshots for:
  - scientific discovery team
  - trading strategy research team
  - travel planning team
- `check_golden_snapshots(...)` compares current deterministic traces to checked-in goldens.
- `update_golden_snapshots(...)` writes current traces to the golden directory.
- `golden-check` CLI command validates current behavior against checked-in snapshots.
- `golden-update` CLI command updates snapshots only when `--approve` is explicitly supplied.

## Commands

Check all example goldens:

```bash
~/.venvs/myenv/bin/python scripts/team_factory_cli.py golden-check team_specs/*.yaml
```

Update goldens intentionally:

```bash
~/.venvs/myenv/bin/python scripts/team_factory_cli.py golden-update \
  team_specs/*.yaml \
  --approve
```

Use `golden-update --approve` only when a behavior change is intentional and has
been reviewed. Accidental trace changes should be investigated rather than blindly
accepted.

## Why this matters

The golden snapshots establish a deterministic baseline for:

- workflow ordering
- mock agent summaries
- event sequence shape
- final outputs
- trace digest stability

This gives the project a safety net before introducing sources of nondeterminism
such as LLM calls, external tools, retries, parallelism, or LangGraph checkpoints.

## Still not implemented

- CI enforcement of golden snapshots
- human approval metadata beyond the explicit CLI flag
- golden snapshot review UI
- real LLM/tool replay
- snapshot baselines for future non-mock workflows
