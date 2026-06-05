# Phase 9: Regression Trace Snapshots and Replay-Oriented Run Logs

Phase 9 hardens the deterministic mock platform before any real LLM/tool
execution is introduced. It adds stable trace snapshots and append-only run-log
persistence that can support replay, regression testing, and debugging workflows.

## Implemented

### Deterministic trace snapshots

Implemented in `src/team_factory/observability/traces.py`.

A `RunTraceSnapshot` captures stable run behavior while intentionally omitting
non-deterministic fields such as run ids, event ids, and timestamps.

Snapshot contents include:

- team id/version
- workflow id
- status
- normalized input
- agent order
- agent step summaries
- event sequence without timestamps/event ids
- final output
- SHA-256 digest of the stable comparable payload

### Trace comparison

`compare_trace_snapshots(...)` returns:

- match status
- expected/actual digests
- concise path-based differences

### Replay-oriented run-log persistence

Implemented in `src/team_factory/observability/run_store.py`.

A `JsonlRunStore` persists each mock run as JSONL with:

- full `RunResult`
- deterministic `RunTraceSnapshot`
- metadata
- recorded timestamp

This is replay-oriented persistence, not a production database.

## CLI additions

```bash
# Run and persist a full run record plus snapshot
~/.venvs/myenv/bin/python scripts/team_factory_cli.py run-mock \
  team_specs/travel_planning_team.yaml \
  "Plan a short trip." \
  --workflow-id plan_trip \
  --run-log examples/artifacts/runs.jsonl \
  --snapshot-out examples/artifacts/travel_snapshot.json

# Create a snapshot directly
~/.venvs/myenv/bin/python scripts/team_factory_cli.py trace-snapshot \
  team_specs/travel_planning_team.yaml \
  "Plan a short trip." \
  --workflow-id plan_trip \
  --out examples/artifacts/travel_snapshot.json

# Compare snapshots
~/.venvs/myenv/bin/python scripts/team_factory_cli.py trace-compare \
  expected_snapshot.json actual_snapshot.json

# Inspect run logs
~/.venvs/myenv/bin/python scripts/team_factory_cli.py run-log-list \
  --run-log examples/artifacts/runs.jsonl
```

## API addition

`POST /runs/mock` now returns a deterministic `trace_snapshot` and can persist to
a JSONL run log when the request body includes `run_log_path`.

## Scope limits

Still not implemented:

- replaying real external tool effects
- deterministic LLM replay
- production run database
- trace snapshot baselining policy
- CI snapshot approval workflow
- LangGraph checkpoint replay

## Recommended next hardening work

- Add checked-in golden snapshots for stable example-team smoke scenarios.
- Add a CLI command to approve/update golden snapshots intentionally.
- Add replay endpoints once the production run-log schema is finalized.
- Only then introduce real LLM/tool adapters behind mockable interfaces.
