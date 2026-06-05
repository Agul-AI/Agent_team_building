# Phase 4: Local Memory Foundation

Phase 4 adds a standalone local memory foundation with SQLite persistence,
retention, and redaction. It does **not** add vector memory, embeddings,
semantic retrieval, or automatic agent-runtime memory use.

## Scope

Implemented:

- `MemoryCategory`: categories aligned with `TeamSpec.memory`.
- `MemoryRecord`: structured JSON-compatible memory item.
- `redact_data`: deterministic redaction for sensitive-looking keys and secret-like strings.
- `SQLiteMemoryStore`: local SQLite-backed store.
- Upsert-by-category/key behavior.
- Category listing and deletion.
- Expiration timestamps and retention deletion.
- Retention-policy lookup from `TeamSpec.memory`.
- JSONL export for inspection and future replay/evaluation workflows.
- Team memory-policy metadata recording via `SQLiteMemoryStore.from_team_spec(...)`.

Not implemented:

- Vector memory.
- Embeddings.
- Semantic search.
- Automatic memory injection into agent prompts.
- Memory use by the mock orchestrator.
- Multi-user authorization.
- Encryption-at-rest.
- Production database migrations.

## Memory categories

| Category | Intended use |
|---|---|
| `short_term` | Current run state; future runtime integration. |
| `project` | Project decisions, artifacts, and run-adjacent facts. |
| `long_term` | Future opt-in cross-run memory; not implemented as vector memory yet. |
| `user_preferences` | Explicit preferences only. |
| `domain_knowledge` | Curated domain references; semantic retrieval deferred. |

## Redaction behavior

The current redactor is intentionally simple and deterministic. It redacts:

- sensitive-looking keys such as `api_key`, `password`, `token`, `secret`, `passport`, and `payment`
- secret-like fragments in strings such as `token: abc123`

This is not a complete DLP system. Future phases should add richer policy packs,
PII detectors, encryption-at-rest, and per-user controls.

## Example

```python
from team_factory.memory import MemoryCategory, SQLiteMemoryStore

with SQLiteMemoryStore("local_memory.sqlite3") as store:
    store.put(
        category=MemoryCategory.PROJECT,
        key="decision:architecture",
        value={"decision": "Use specs before runtime.", "api_key": "secret"},
        retention_days=365,
    )
    record = store.get("project", "decision:architecture")
    print(record.value)
```

The stored value redacts the API key before persistence.

## Future Phase 4+ extensions

- Add a memory manager facade around category-specific policies.
- Add run-scoped short-term memory integration with the mock orchestrator.
- Add audit events for memory writes and deletes.
- Add encryption-at-rest for sensitive stores.
- Add explicit consent records for user-preference memory.
- Add vector memory only after retention/redaction behavior is stable.
