from __future__ import annotations

from datetime import UTC, datetime, timedelta

from team_factory.memory import MemoryCategory, SQLiteMemoryStore, redact_data
from team_factory.specs.loader import load_team_spec


def test_redact_data_redacts_sensitive_keys_and_secret_strings() -> None:
    report = redact_data(
        {
            "user": "alice",
            "api_key": "sk-test",
            "nested": {
                "notes": "token: abc123 should not be stored",
                "safe": "keep",
            },
            "items": [{"password": "pw"}],
        }
    )

    assert report.redacted is True
    assert report.data["api_key"] == "[REDACTED]"
    assert report.data["nested"]["notes"] == "token=[REDACTED] should not be stored"
    assert report.data["nested"]["safe"] == "keep"
    assert report.data["items"][0]["password"] == "[REDACTED]"
    assert "api_key" in report.paths
    assert "items[0].password" in report.paths


def test_sqlite_memory_store_put_get_update_and_redaction(tmp_path) -> None:
    db_path = tmp_path / "memory.sqlite3"
    with SQLiteMemoryStore(db_path) as store:
        first = store.put(
            category=MemoryCategory.PROJECT,
            key="decision:architecture",
            value={"decision": "Use specs first.", "api_key": "secret"},
            metadata={"source": "test"},
        )
        second = store.put(
            category="project",
            key="decision:architecture",
            value={"decision": "Use specs before runtime."},
            metadata={"source": "updated"},
        )

        loaded = store.get(MemoryCategory.PROJECT, "decision:architecture")

    assert loaded is not None
    assert first.id == second.id == loaded.id
    assert loaded.value == {"decision": "Use specs before runtime."}
    assert loaded.metadata == {"source": "updated"}
    assert first.redacted is True
    assert second.created_at == first.created_at
    assert second.updated_at >= first.updated_at

    with SQLiteMemoryStore(db_path) as reopened:
        persisted = reopened.get("project", "decision:architecture")

    assert persisted is not None
    assert persisted.id == first.id


def test_memory_store_lists_by_category_and_deletes(tmp_path) -> None:
    with SQLiteMemoryStore(tmp_path / "memory.sqlite3") as store:
        store.put(category="project", key="a", value={"value": 1})
        store.put(category="user_preferences", key="b", value={"value": 2})

        project_records = store.list_records(category="project")
        all_records = store.list_records()
        deleted = store.delete("project", "a")
        deleted_again = store.delete("project", "a")

    assert [record.key for record in project_records] == ["a"]
    assert [record.key for record in all_records] == ["a", "b"]
    assert deleted is True
    assert deleted_again is False


def test_memory_store_retention_excludes_and_deletes_expired_records(tmp_path) -> None:
    now = datetime(2026, 6, 5, tzinfo=UTC)
    with SQLiteMemoryStore(tmp_path / "memory.sqlite3") as store:
        store.put(
            category="project",
            key="expired",
            value={"value": "old"},
            retention_days=1,
            now=now - timedelta(days=2),
        )
        store.put(
            category="project",
            key="fresh",
            value={"value": "new"},
            retention_days=3,
            now=now,
        )

        visible_before = store.list_records(category="project")
        all_before = store.list_records(category="project", include_expired=True)
        deleted_count = store.apply_retention(now=now)
        all_after = store.list_records(category="project", include_expired=True)

    assert [record.key for record in visible_before] == ["fresh"]
    assert sorted(record.key for record in all_before) == ["expired", "fresh"]
    assert deleted_count == 1
    assert [record.key for record in all_after] == ["fresh"]


def test_retention_policy_can_be_read_from_team_spec(tmp_path) -> None:
    spec = load_team_spec("team_specs/travel_planning_team.yaml")
    with SQLiteMemoryStore(tmp_path / "memory.sqlite3") as store:
        project_retention = store.retention_days_for_category(spec.memory, "project")
        user_pref_retention = store.retention_days_for_category(
            spec.memory,
            MemoryCategory.USER_PREFERENCES,
        )

    assert project_retention == 180
    assert user_pref_retention == 365


def test_store_from_team_spec_records_policy_metadata(tmp_path) -> None:
    spec = load_team_spec("team_specs/travel_planning_team.yaml")
    with SQLiteMemoryStore.from_team_spec(spec, path=tmp_path / "memory.sqlite3") as store:
        record = store.get("project", "team_policy:travel_planning_team")

    assert record is not None
    assert record.metadata == {"kind": "team_memory_policy"}
    assert record.value["team_id"] == "travel_planning_team"
    assert record.value["memory"]["project"]["retention_days"] == 180


def test_export_jsonl_writes_records(tmp_path) -> None:
    output_path = tmp_path / "exports" / "memory.jsonl"
    with SQLiteMemoryStore(tmp_path / "memory.sqlite3") as store:
        store.put(category="project", key="a", value={"value": 1})
        written_path = store.export_jsonl(output_path)

    text = written_path.read_text(encoding="utf-8")
    assert written_path == output_path
    assert '"key":"a"' in text
    assert '"category":"project"' in text
