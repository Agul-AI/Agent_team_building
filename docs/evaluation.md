# Evaluation Strategy

Phase 5 implements the first executable evaluation foundation: deterministic mock
scenario execution and Markdown reports.

## Current implementation

- Reads scenarios and metrics from `TeamSpec.evaluation`.
- Runs scenarios through supported deterministic mock workflows: sequential, critique-revision, and supervisor-worker.
- Performs structural checks only:
  - run completed
  - final output present
  - agent outputs present
  - events present
- Records expected properties as `not_scored` placeholders.
- Records declared metrics without computing domain scores.
- Produces structured `EvaluationReport` objects and Markdown reports.

## Current limitations

The harness does not yet perform semantic scoring. It cannot verify whether a
scientific hypothesis is novel, a backtest is valid, or a travel budget truly fits.
Those checks require later domain-specific metric implementations, human rubrics,
and eventually optional LLM-judge workflows.

## Future evaluation layers

1. Static spec checks.
2. Deterministic mock-agent scenario tests. Implemented in Phase 5.
3. Regression trace tests.
4. Domain-specific rubric scoring.
5. Human review checkpoints.
6. Optional LLM-as-judge scoring with calibration and audit trails.

Each generated team should ship with its own scenarios, metrics, and review rubrics.
