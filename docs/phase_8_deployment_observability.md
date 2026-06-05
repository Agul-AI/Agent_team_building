# Phase 8: Local API Skeleton and Observability Foundation

Phase 8 adds a dependency-light local API skeleton and structured JSONL
observability. This is a development foundation, not a production deployment.

## Implemented

### Local API skeleton

Implemented in `src/team_factory/api/` using Python's standard-library HTTP
server.

Available local routes:

| Method | Route | Purpose |
|---|---|---|
| `GET` | `/health` | Health check. |
| `POST` | `/specs/validate` | Validate a team spec. |
| `POST` | `/workflows/order` | Return deterministic mock workflow order. |
| `POST` | `/runs/mock` | Run a supported deterministic mock workflow; Phase 9 can also return trace snapshots and persist a run log when `run_log_path` is provided. |
| `POST` | `/tools/check` | Authorize a proposed tool call without executing it. |
| `POST` | `/eval/mock` | Run deterministic mock evaluation and write a Markdown report. |

Start the local server:

```bash
~/.venvs/myenv/bin/python scripts/team_factory_api.py --host 127.0.0.1 --port 8765
```

Example request:

```bash
curl -s http://127.0.0.1:8765/health
```

```bash
curl -s -X POST http://127.0.0.1:8765/runs/mock \
  -H 'Content-Type: application/json' \
  -d '{
    "spec_path": "team_specs/travel_planning_team.yaml",
    "workflow_id": "plan_trip",
    "task": "Plan a short trip."
  }'
```

### Structured observability

Implemented in `src/team_factory/observability/`.

- `AuditEvent`: structured audit events for local actions.
- `RunLogRecord`: compact run records for deterministic mock runs.
- `JsonlEventLogger`: append-only JSONL logger.

The local API can write audit/run records to:

```text
examples/artifacts/api_audit.jsonl
```

## Scope limits

Not implemented:

- production API framework
- authentication or RBAC
- TLS
- request size/rate limiting
- persistent run database
- dashboards
- distributed tracing
- metrics backend
- deployment manifests
- real LLM calls
- actual tool execution

## Future deployment work

Recommended next steps after Phase 8:

1. Add API auth/RBAC design.
2. Add persistent run/audit database tables.
3. Add structured run replay endpoints.
4. Add Dockerfile and docker-compose for local deployment.
5. Add metrics counters and health/readiness endpoints.
6. Add production framework migration only after local API shape stabilizes.
