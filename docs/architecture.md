# Architecture

The Agent Team Factory is designed as a spec-driven system.

## Current implementation scope

Phase 0/1 implements only:

- documentation skeleton
- static local website
- team spec schema models
- YAML spec loading
- cross-reference and safety-adjacent validation
- example team specs
- unit tests

## Future architecture

```text
Spec -> Validate -> Compile -> Run -> Log -> Evaluate -> Revise -> Deploy
```

The runtime should remain behind internal interfaces so the project can use LangGraph later without exposing LangGraph-specific details throughout the repository.

## Design principles

- Human-editable specs.
- Versioned team definitions.
- Explicit stopping criteria.
- Approval gates before high-impact actions.
- Logged and replayable runs.
- Evaluation-first team development.
