# Team Spec Schema

Phase 1 defines a minimal schema in `src/team_factory/specs/models.py`.

## Required root fields

- `schema_version`: currently `0.1`.
- `team_id`: stable identifier.
- `team_version`: semantic version.
- `name`: human-readable name.
- `domain`: domain label.
- `purpose`: team purpose.
- `agents`: non-empty list.
- `workflows`: non-empty list.

## Validation rules

- Agent, tool, and workflow IDs must be unique.
- Workflow agent references must point to declared agents.
- Agent tool references must point to declared tools.
- Agent model profiles must point to declared profiles.
- Every workflow must include at least one hard stopping criterion.
- Critical or high-impact enabled tools must require approval.
- High-impact safety actions must also appear in `human_review.required_before`.

## JSON Schema export

Use `team_factory.specs.schema_export.export_team_spec_schema(path)` to write the current JSON Schema.
