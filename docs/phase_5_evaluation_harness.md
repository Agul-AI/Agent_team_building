# Phase 5: Evaluation Harness Foundation

Phase 5 adds a deterministic evaluation harness for mock workflow runs and local
scenario reports. It does **not** add LLM judges, real domain scoring, production
evaluation services, or actual tool execution.

## Scope

Implemented:

- `EvaluationHarness`: runs declared spec scenarios through supported mock workflows.
- `EvaluationReport`: structured report with team metadata, status, summary, metrics, and scenario results.
- `ScenarioResult`: per-scenario outcome, structural checks, expected properties, run id, and final output.
- Structural checks for deterministic mock runs:
  - run completed
  - final output present
  - agent outputs present
  - events present
- Expected-property placeholders with `not_scored` status.
- Skipped reporting for unsupported workflow types.
- Markdown report rendering.
- `scripts/run_mock_evals.py` helper for writing reports under `examples/artifacts/evaluation_reports/`.

Not implemented:

- LLM-as-judge scoring.
- Semantic rubric scoring.
- Domain-specific metric computation.
- Regression trace comparison.
- Human review UI/API.
- Evaluation dashboards.
- Real scientific/trading/travel validators.

## Report statuses

| Status | Meaning |
|---|---|
| `passed` | All deterministic structural checks passed for all executable scenarios. |
| `failed` | At least one executable scenario failed a structural check or raised an error. |
| `skipped` | No scenarios could be executed, usually because the workflow type is unsupported. |
| `partial` | Some scenarios passed and some were skipped. |

## Important limitation

Expected properties and declared metrics are recorded but not semantically scored in
Phase 5. For example, a travel scenario can declare `fits stated budget`, but the
harness does not yet verify budget fit. It only verifies that the deterministic
mock workflow completed structurally.

## Example

```python
from team_factory.evaluation import EvaluationHarness, write_markdown_report
from team_factory.specs.loader import load_team_spec

spec = load_team_spec("team_specs/travel_planning_team.yaml")
report = EvaluationHarness().run_team(spec, workflow_id="plan_trip")
write_markdown_report(report, "examples/artifacts/evaluation_reports/travel.md")
```

## CLI helper

```bash
~/.venvs/myenv/bin/python scripts/run_mock_evals.py team_specs/*.yaml
```

After Phase 6, the scientific, trading, and travel examples all run through
the deterministic mock orchestrator and pass structural checks.

## Future Phase 5+ extensions

- Add deterministic regression snapshots for mock traces.
- Add rubric objects and human-review checkpoint structures.
- Add domain-specific metric plugin interfaces.
- Add report persistence in the memory/run-log layer.
- Add LLM-judge support only after deterministic tests are stable.
