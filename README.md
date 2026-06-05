# Agent Team Factory

A greenfield, spec-driven platform for designing, configuring, validating, evaluating, and eventually deploying specialized AI agent teams.

Current completed scope: **Phase 0 through Phase 13 guarded LLM smoke workflow**.

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
- Deterministic evaluation harness and Markdown scenario reports.
- Mock-compatible workflow support for sequential, critique-revision, and supervisor-worker teams.
- Local CLI flows for validation, workflow order, mock runs, tool checks, memory, and evals.
- Local API skeleton and structured JSONL audit/run observability.
- Regression trace snapshots and replay-oriented JSONL run-log persistence.
- Checked-in golden snapshots and explicit `golden-update --approve` workflow.
- CI-ready deterministic regression script and lightweight release checklist.
- Strict opt-in LLM adapter layer with deterministic default, OpenAI Responses API path, and Codex CLI path for Codex/ChatGPT sign-in quota.
- Guarded real-LLM single-agent smoke workflow with no tools/trading/brokerage.

Not implemented yet:

- Full LLM-backed multi-agent runtime orchestration.
- Debate, parallel-research, and custom workflow runtime semantics.
- Tool execution.
  - Phase 3 can authorize proposed calls but intentionally does not execute them.
- Runtime memory integration.
- Vector memory and semantic retrieval.
- Semantic evaluation scoring, LLM judges, and domain-specific metric computation.
- Production API framework, auth/RBAC, deployment manifests, dashboards, and metrics backends.
- Deployment.




## Generate text with the LLM adapter layer

The default model identifier is `gpt-5.5-codex` with `medium` reasoning effort.
The default provider still stays deterministic unless real LLM use is explicitly
enabled. Override the model/reasoning defaults with `--model`,
`--reasoning-effort`, `TEAM_FACTORY_DEFAULT_LLM_MODEL`, or
`TEAM_FACTORY_DEFAULT_LLM_REASONING_EFFORT`.

Deterministic default using the Codex model identifier:

```bash
~/.venvs/myenv/bin/python scripts/team_factory_cli.py llm-generate \
  "Summarize the platform in one sentence." \
  --instructions "Be concise."
```

Codex quota path requires explicit opt-in and is not used by CI. It does not
require `OPENAI_API_KEY`; it uses the local `codex` CLI sign-in. The factory's
`gpt-5.5-codex` default is mapped to the Codex CLI model id `gpt-5.5` for this
provider:

```bash
export TEAM_FACTORY_ENABLE_REAL_LLM=1
~/.venvs/myenv/bin/python scripts/team_factory_cli.py llm-generate \
  "Summarize the platform in one sentence." \
  --provider codex_exec \
  --model gpt-5.5-codex \
  --reasoning-effort medium \
  --enable-real-llm
```

OpenAI API path also requires explicit opt-in and is not used by CI:

```bash
export TEAM_FACTORY_ENABLE_REAL_LLM=1
export OPENAI_API_KEY=...
~/.venvs/myenv/bin/python scripts/team_factory_cli.py llm-generate \
  "Summarize the platform in one sentence." \
  --provider openai_responses \
  --model gpt-5.5-codex \
  --reasoning-effort medium \
  --enable-real-llm
```

Guarded single-agent LLM smoke workflow using Codex quota, still no
tools/trading/brokerage:

```bash
export TEAM_FACTORY_ENABLE_REAL_LLM=1
~/.venvs/myenv/bin/python scripts/team_factory_cli.py run-llm-smoke \
  team_specs/trading_strategy_research_team.yaml \
  "Research robust long-term trend-following strategies on ETF for simulation only." \
  --agent-id strategy_ideator \
  --provider codex_exec \
  --model gpt-5.5-codex \
  --reasoning-effort medium \
  --enable-real-llm \
  --acknowledge-no-tools \
  --acknowledge-simulation-only \
  --out examples/artifacts/strategy_building_team/llm_smoke_strategy_ideator.json
```

## Run the CI regression suite locally

```bash
scripts/ci_regression.sh
```

Run release checks before tagging or merging major changes:

```bash
scripts/release_check.sh
```

## Use the local CLI

From this source checkout:

```bash
~/.venvs/myenv/bin/python scripts/team_factory_cli.py --help
~/.venvs/myenv/bin/python scripts/team_factory_cli.py validate team_specs/*.yaml
~/.venvs/myenv/bin/python scripts/team_factory_cli.py eval team_specs/*.yaml
```

## Validate locally

```bash
~/.venvs/myenv/bin/python -m pytest
~/.venvs/myenv/bin/python scripts/validate_specs.py team_specs/*.yaml
```

## Run a deterministic mock workflow

The deterministic mock runtime supports sequential, critique-revision, and supervisor-worker workflows.

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

## Run deterministic mock evaluations

The Phase 5 evaluation harness executes declared scenarios through supported mock workflows and writes static reports.

```bash
~/.venvs/myenv/bin/python scripts/run_mock_evals.py team_specs/*.yaml
```

The scientific, trading, and travel example teams now run through the mock evaluator. Debate, parallel-research, and custom workflows are still reported as skipped.




## Check golden snapshots

```bash
~/.venvs/myenv/bin/python scripts/team_factory_cli.py golden-check team_specs/*.yaml
```

Update golden snapshots only after intentional review:

```bash
~/.venvs/myenv/bin/python scripts/team_factory_cli.py golden-update team_specs/*.yaml --approve
```

## Capture and compare deterministic trace snapshots

```bash
~/.venvs/myenv/bin/python scripts/team_factory_cli.py trace-snapshot \
  team_specs/travel_planning_team.yaml \
  "Plan a short trip." \
  --workflow-id plan_trip \
  --out examples/artifacts/travel_snapshot.json

~/.venvs/myenv/bin/python scripts/team_factory_cli.py run-mock \
  team_specs/travel_planning_team.yaml \
  "Plan a short trip." \
  --workflow-id plan_trip \
  --run-log examples/artifacts/runs.jsonl
```

## Serve the local API skeleton

```bash
~/.venvs/myenv/bin/python scripts/team_factory_api.py --host 127.0.0.1 --port 8765
```

Example health check:

```bash
curl -s http://127.0.0.1:8765/health
```

## View the local website

Open this file in a browser:

```text
site/index.html
```

It summarizes the implementation plan and current progress.
