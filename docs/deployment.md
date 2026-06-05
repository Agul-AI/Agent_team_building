# Deployment

Production deployment is not implemented yet. Phase 8 adds a local API skeleton only.

Planned deployment path:

1. Local CLI. Implemented in Phase 7.
2. Local API server skeleton. Implemented in Phase 8 with Python stdlib HTTP handling.
3. Cloud worker with persistent run storage.
4. Production monitoring, audit, and approval queues.

Team specs can already declare deployment intent with `deployment.mode`.


## Phase 8 local API skeleton

Run locally with:

```bash
~/.venvs/myenv/bin/python scripts/team_factory_api.py --host 127.0.0.1 --port 8765
```

This is not a production server. It has no auth/RBAC, TLS, metrics backend, or deployment manifests.
