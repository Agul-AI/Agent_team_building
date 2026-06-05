# Phase 6: Expanded Mock Workflow Support

Phase 6 makes all three example teams runnable in deterministic mock mode by
adding support for two additional workflow families:

- `critique_and_revision`
- `supervisor_worker`

This remains a mock runtime. It does **not** add LLM calls, real parallelism,
tool execution, LangGraph integration, or iterative quality improvement.

## Implemented

- `critique_and_revision` execution order uses the workflow's declared `steps`.
- `supervisor_worker` execution order is:
  1. supervisor
  2. workers in declared order
  3. final agent, when declared
- `ordered_agent_ids_for_workflow(...)` supports the three runnable mock families.
- run-start events include deterministic `execution_order` metadata.
- Scientific discovery, trading strategy research, and travel planning example
  evaluations can now run through the deterministic mock evaluator.

## Still unsupported

- `debate`
- `parallel_research`
- `custom`
- real critique/revision loops
- true supervisor task dispatch
- worker parallelism
- evaluator-based stopping decisions

## Example evaluation result

```bash
~/.venvs/myenv/bin/python scripts/run_mock_evals.py team_specs/*.yaml
```

Expected result after Phase 6:

```text
PASSED scientific_discovery_team
PASSED trading_strategy_research_team
PASSED travel_planning_team
```

## Future extensions

- Add deterministic regression snapshots for each workflow family.
- Add true graph runtime support behind an adapter.
- Add debate and parallel-research mock semantics.
- Add configurable loop bounds for critique/revision simulations.
- Add real LangGraph integration only after deterministic coverage is stable.
