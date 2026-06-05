# Agent Team Factory Implementation Plan

## A. Executive summary

Build a spec-driven **Agent Team Factory**: a platform that lets users define reusable, versioned AI-agent teams from structured specs, validate those specs, simulate and evaluate them, and eventually deploy them with observability and safety controls.

The platform should not be one hard-coded team. It should compile editable team specifications into executable workflows and evaluation suites.

Recommended MVP stack:

- Python backend.
- Pydantic for specs and validation.
- LangGraph behind an internal orchestration adapter in later phases.
- SQLite for local run metadata and project memory in early phases.
- Postgres/pgvector for production memory and audit logs later.
- CLI-first developer experience, with a static/local website and optional web UI later.

## B. Assumptions

1. The first product is local-first and inspectable.
2. Runtime orchestration starts with deterministic mock execution before real LLM/tool integration.
3. Trading-related teams are research/simulation-only unless separately extended with legal/compliance review.
4. High-impact actions require explicit human approval.
5. Every run should eventually be logged, replayable, and evaluable.
6. Memory is opt-in and governed by retention/redaction policies.

## C. Clarifying questions

None are blocking for Phase 0 or Phase 1.

## D. Recommended architecture

```text
Team Spec YAML
  -> Spec Loader
  -> Pydantic Validator
  -> Safety/Consistency Linter
  -> Team Factory Compiler
  -> Orchestration Runtime
  -> Agents + Tools + Memory + Evaluation
  -> Logs + Replay + Reports
```

Phase 0/1 implemented the foundation:

- docs and plan
- repository skeleton
- team spec data model
- YAML loading
- validation tests
- example team specs

Phase 2 adds deterministic mock execution for sequential workflows. Phase 3 adds manifest-only tool authorization. Phase 4 adds standalone SQLite memory persistence, retention, and redaction. Phase 5 adds deterministic mock evaluation reports. Phase 6 adds mock-compatible critique-revision and supervisor-worker workflow support. Phase 7 adds local CLI flows. Phase 8 adds a local API skeleton and JSONL observability. Phase 9 hardening adds regression trace snapshots and replay-oriented run-log persistence. Phase 10 adds checked-in golden snapshots and an explicit approval/update workflow. Phase 11 adds CI-ready deterministic regression commands and a lightweight release checklist. Phase 12 adds the first strict opt-in real LLM adapter path with a `gpt-5.5-codex` plus `medium` reasoning default while keeping deterministic mocks as the default provider. Phase 13 adds a guarded real-LLM single-agent smoke workflow with no tools, no trading, no brokerage, and explicit opt-in acknowledgements. LLM-backed orchestration, actual tool execution, runtime memory integration, vector memory, semantic evaluation scoring, and production deployment services are future phases.

## E. Alternative architectures and tradeoffs

### Python vs TypeScript

| Option | Pros | Cons | Recommendation |
|---|---|---|---|
| Python | Best for LLM orchestration, data science, scientific workflows, trading research, evals | Less ideal for frontend-heavy UI | Use for backend/runtime |
| TypeScript | Excellent for web UI/full-stack work | Less natural for scientific/trading analysis | Use later for UI if needed |

### LangGraph vs CrewAI vs AutoGen/Microsoft Agent Framework vs custom

| Option | Pros | Cons | Recommendation |
|---|---|---|---|
| LangGraph | Graph control, durable execution, checkpoints, HITL, replay | Requires more engineering than simple crew abstractions | Preferred runtime later |
| CrewAI | Quick agent-team prototypes | Less control for deeply custom workflow semantics | Useful reference/prototype |
| AutoGen/Microsoft Agent Framework | Strong multi-agent concepts and enterprise direction | More ecosystem-specific and still shifting | Consider if Microsoft stack matters |
| Custom orchestrator | Maximum control | Expensive to build safely | Avoid as primary runtime |

### Storage

- MVP: SQLite and JSONL logs.
- Production: Postgres for audit/run metadata.
- Vector memory: pgvector first, external vector DB later if scale requires it.

## F. Core abstractions and data models

- `TeamSpec`: root spec with team metadata, agents, workflows, tools, memory, evaluation, safety, and deployment intent.
- `AgentSpec`: role, goal, instructions, allowed tools, memory access, output schema, constraints.
- `WorkflowSpec`: workflow type, steps/supervisor/workers/nodes/edges, stopping criteria, human checkpoints.
- `ToolSpec`: tool manifest with risk, side effects, permissions, approval requirement, sandbox hints.
- `MemorySpec`: short-term, project, long-term, user preference, and domain knowledge memory configuration.
- `EvaluationSpec`: metrics, scenarios, regression tests, human review rubrics.
- `SafetyPolicy`: prohibited actions, high-impact actions, human review gates, privacy handling.

## G. Agent-team specification format

Team specs should be YAML or JSON. YAML is preferred for human editing. Each spec is versioned and validated.

Minimum required fields:

- `schema_version`
- `team_id`
- `team_version`
- `name`
- `domain`
- `purpose`
- `agents`
- `workflows`

The Phase 1 schema supports reusable roles and domain-specific role strings.

## H. Orchestration design

Future runtime should support:

1. Sequential workflows.
2. Debate workflows.
3. Supervisor-worker workflows.
4. Critique-and-revision loops.
5. Parallel research workflows.
6. Custom graph workflows.

Every workflow must include hard stopping criteria such as maximum iterations, tool calls, cost, tokens, or wall-clock time.

## I. Tooling design

Every tool should have a manifest:

- id
- provider
- description
- input/output schema
- risk level
- side-effect level
- permissions
- approval requirement
- sandbox policy
- rate limits
- secrets required

Risk levels:

| Risk | Examples | Policy |
|---|---|---|
| low | calculator | log only |
| medium | web search, paper search, market data read | log + rate limit |
| high | code execution, local writes | sandbox + possible approval |
| critical | trade, purchase, booking, email | mandatory approval |

## J. Memory design

Memory types:

- Short-term memory: current run state.
- Project memory: project decisions and artifacts.
- Long-term memory: opt-in cross-run knowledge.
- User preference memory: explicit user preferences only.
- Domain knowledge: curated papers, docs, datasets.

Do not store secrets, credentials, unnecessary PII, or sensitive financial/medical/legal data by default.

## K. Evaluation and testing strategy

Platform tests:

- spec validation
- cross-reference validation
- high-impact approval validation
- workflow stopping criteria
- schema export

Future runtime tests:

- deterministic mock-agent traces
- replay tests
- tool permission tests
- memory retention tests
- evaluation report tests

Domain-specific evals:

- Scientific discovery: novelty, citation quality, hypothesis plausibility, feasibility, reproducibility.
- Trading research: backtest validity, data leakage, overfitting, drawdown, costs, paper-trading gates.
- Travel planning: budget fit, preference match, feasibility, booking reliability, user satisfaction.

## L. Safety and compliance plan

Global rules:

1. No autonomous high-impact actions.
2. Critical tools require explicit approval.
3. Financial teams are simulation/research-only by default.
4. Claims must distinguish evidence from uncertainty.
5. Personal data is minimized and redacted from logs where possible.

## M. Proposed repository structure

```text
src/team_factory/
  specs/
    models.py
    loader.py
    validator.py
    schema_export.py
    versioning.py
team_specs/
  scientific_discovery_team.yaml
  trading_strategy_research_team.yaml
  travel_planning_team.yaml
docs/
  implementation_plan.md
  architecture.md
  team_spec_schema.md
  safety.md
  evaluation.md
  deployment.md
  implementation_progress.md
site/
  index.html
  styles.css
tests/unit/
  test_spec_validation.py
scripts/
  validate_specs.py
```

## N. Example team specs

Phase 1 includes three example specs:

- `team_specs/scientific_discovery_team.yaml`
- `team_specs/trading_strategy_research_team.yaml`
- `team_specs/travel_planning_team.yaml`

## O. Implementation roadmap

| Phase | Goal | Status |
|---|---|---|
| Phase 0 | Requirements, architecture, docs, repo skeleton | Implemented in this initial commit |
| Phase 1 | Minimal team spec format, YAML loader, validation, tests | Implemented in this initial commit |
| Phase 2 | Basic deterministic mock orchestrator | Implemented locally |
| Phase 3 | Manifest-only tool registry and permission layer | Implemented locally |
| Phase 4 | Local SQLite memory foundation | Implemented locally |
| Phase 5 | Deterministic mock evaluation harness | Implemented locally |
| Phase 6 | Example team mock runtime demos | Implemented locally |
| Phase 7 | Local CLI flows | Implemented locally |
| Phase 8 | Local API skeleton and observability | Implemented locally |
| Phase 9 | Regression trace snapshots and replay run logs | Implemented locally |
| Phase 10 | Golden snapshots and approval workflow | Implemented locally |
| Phase 11 | CI regression commands and release checklist | Implemented locally |
| Phase 12 | Strict opt-in LLM adapter layer | Implemented locally |
| Phase 13 | Guarded single-agent LLM smoke workflow | Implemented locally |

## P. First 10 Codex tasks

1. Initialize project structure.
2. Define Pydantic team spec models.
3. Add YAML loading and validation.
4. Create three example team specs.
5. Add validation tests.
6. Export JSON schema.
7. Add safety linter extensions.
8. Add mock orchestrator.
9. Add tool registry.
10. Add evaluation harness.

## Q. Risks and mitigations

| Risk | Mitigation |
|---|---|
| Specs become hard-coded | Keep team behavior declarative |
| Framework lock-in | Use internal adapter around orchestration runtime |
| Unsafe tools | Risk levels, approval gates, sandboxing |
| Infinite loops | Mandatory stopping criteria |
| Poor evaluations | Scenario tests and human rubrics from the beginning |
| Memory privacy issues | Opt-in memory, redaction, retention policies |

## R. MVP definition of done

MVP is done when:

1. Team specs validate.
2. Example teams exist and pass validation.
3. Basic workflows can run with mock agents.
4. Tool permissions are enforced.
5. Human approval gates exist for high-impact actions.
6. Runs are logged and replayable.
7. Evaluation scenarios can run.
8. Documentation explains how to add new teams.
