# Phase 7: Local CLI Flows

Phase 7 adds local command-line flows over the Phase 1-6 foundations. The CLI is
argparse-based so it works without installing additional packages. A console entry
point is declared for installed environments, and `scripts/team_factory_cli.py`
works directly from the repository checkout.

## CLI entry points

From a source checkout:

```bash
~/.venvs/myenv/bin/python scripts/team_factory_cli.py --help
```

When installed as a package:

```bash
team-factory --help
```

## Implemented commands

| Command | Purpose |
|---|---|
| `validate` | Validate one or more team spec YAML files. |
| `workflow-order` | Inspect deterministic mock execution order. |
| `run-mock` | Run a supported deterministic mock workflow. |
| `tool-check` | Authorize a proposed tool call without executing it. |
| `memory-put` | Store a local memory record with optional redaction/retention. |
| `memory-get` | Read one local memory record. |
| `memory-list` | List local memory records. |
| `memory-delete` | Delete one local memory record. |
| `eval` | Run deterministic mock evaluations and write Markdown reports. |
| `trace-snapshot` | Run a mock workflow and write a deterministic trace snapshot. |
| `trace-compare` | Compare two deterministic trace snapshots. |
| `run-log-list` | List persisted replay-oriented run records. |
| `run-log-get` | Retrieve one persisted replay-oriented run record. |

## Examples

Validate specs:

```bash
~/.venvs/myenv/bin/python scripts/team_factory_cli.py validate team_specs/*.yaml
```

Inspect workflow order:

```bash
~/.venvs/myenv/bin/python scripts/team_factory_cli.py workflow-order \
  team_specs/trading_strategy_research_team.yaml \
  --workflow-id research_backtest_review
```

Run a mock workflow:

```bash
~/.venvs/myenv/bin/python scripts/team_factory_cli.py run-mock \
  team_specs/scientific_discovery_team.yaml \
  "Survey automated materials discovery." \
  --workflow-id main
```

Check a proposed tool call:

```bash
~/.venvs/myenv/bin/python scripts/team_factory_cli.py tool-check \
  team_specs/travel_planning_team.yaml \
  --agent-id destination_researcher \
  --tool-id web_search \
  --purpose "Research museum opening hours."
```

Store and read local memory:

```bash
~/.venvs/myenv/bin/python scripts/team_factory_cli.py memory-put \
  --db local_memory.sqlite3 \
  --category project \
  --key decision:architecture \
  --value-json '{"decision":"Use specs first.","api_key":"secret"}'

~/.venvs/myenv/bin/python scripts/team_factory_cli.py memory-get \
  --db local_memory.sqlite3 \
  --category project \
  --key decision:architecture \
  --json
```

Run mock evaluations:

```bash
~/.venvs/myenv/bin/python scripts/team_factory_cli.py eval team_specs/*.yaml
```

## Scope limits

The CLI only wraps existing local foundations. It does not add:

- real LLM execution
- actual tool execution
- interactive UI flows
- API server
- production auth/RBAC
- LangGraph integration
