"""SQLite-backed local memory store for Phase 4."""

from __future__ import annotations

import json
import sqlite3
from contextlib import AbstractContextManager
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any
from uuid import uuid4

from team_factory.memory.models import MemoryCategory, MemoryRecord
from team_factory.memory.redaction import redact_data
from team_factory.specs.models import MemorySpec, TeamSpec


class MemoryStoreError(ValueError):
    """Raised for local memory store errors."""


def _utc_now() -> datetime:
    return datetime.now(UTC)


def _to_iso(value: datetime | None) -> str | None:
    return value.isoformat() if value is not None else None


def _from_iso(value: str | None) -> datetime | None:
    if value is None:
        return None
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=UTC)
    return parsed


class SQLiteMemoryStore(AbstractContextManager["SQLiteMemoryStore"]):
    """Small SQLite memory store with retention and redaction support.

    The store is suitable for local project/user-preference memory in early
    development. It is not a vector store and does not implement semantic search.
    """

    def __init__(self, path: str | Path = ":memory:") -> None:
        self.path = str(path)
        self._connection = sqlite3.connect(self.path)
        self._connection.row_factory = sqlite3.Row
        self._initialize_schema()

    @classmethod
    def from_team_spec(
        cls,
        team: TeamSpec,
        *,
        path: str | Path = ":memory:",
    ) -> SQLiteMemoryStore:
        """Create a store and record the team memory policy as metadata."""

        store = cls(path)
        store.put(
            category=MemoryCategory.PROJECT,
            key=f"team_policy:{team.team_id}",
            value={
                "team_id": team.team_id,
                "team_version": team.team_version,
                "memory": team.memory.model_dump(mode="json"),
                "privacy": team.safety.privacy.model_dump(mode="json"),
            },
            metadata={"kind": "team_memory_policy"},
            redact=True,
        )
        return store

    def __exit__(self, exc_type: object, exc_value: object, traceback: object) -> None:
        self.close()

    def close(self) -> None:
        """Close the SQLite connection."""

        self._connection.close()

    def put(
        self,
        *,
        category: MemoryCategory | str,
        key: str,
        value: dict[str, Any],
        metadata: dict[str, Any] | None = None,
        retention_days: int | None = None,
        redact: bool = True,
        now: datetime | None = None,
    ) -> MemoryRecord:
        """Insert or update one memory item by `(category, key)`."""

        if not key:
            raise MemoryStoreError("memory key must be non-empty")
        normalized_category = MemoryCategory(category)
        timestamp = now or _utc_now()
        expires_at = (
            timestamp + timedelta(days=retention_days)
            if retention_days is not None
            else None
        )
        report = redact_data(value) if redact else None
        stored_value = report.data if report is not None else value
        was_redacted = bool(report.redacted) if report is not None else False
        existing = self.get(normalized_category, key, include_expired=True)
        record_id = existing.id if existing is not None else str(uuid4())
        created_at = existing.created_at if existing is not None else timestamp

        self._connection.execute(
            """
            INSERT INTO memory_records (
                id, category, key, value_json, metadata_json,
                created_at, updated_at, expires_at, redacted
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(category, key) DO UPDATE SET
                value_json = excluded.value_json,
                metadata_json = excluded.metadata_json,
                updated_at = excluded.updated_at,
                expires_at = excluded.expires_at,
                redacted = excluded.redacted
            """,
            (
                record_id,
                normalized_category.value,
                key,
                json.dumps(stored_value, sort_keys=True),
                json.dumps(metadata or {}, sort_keys=True),
                _to_iso(created_at),
                _to_iso(timestamp),
                _to_iso(expires_at),
                1 if was_redacted else 0,
            ),
        )
        self._connection.commit()
        record = self.get(normalized_category, key, include_expired=True)
        if record is None:
            raise MemoryStoreError("failed to read memory record after write")
        return record

    def get(
        self,
        category: MemoryCategory | str,
        key: str,
        *,
        include_expired: bool = False,
    ) -> MemoryRecord | None:
        """Return one memory item by category/key."""

        normalized_category = MemoryCategory(category)
        row = self._connection.execute(
            """
            SELECT * FROM memory_records
            WHERE category = ? AND key = ?
            """,
            (normalized_category.value, key),
        ).fetchone()
        if row is None:
            return None
        record = self._row_to_record(row)
        if record.is_expired and not include_expired:
            return None
        return record

    def list_records(
        self,
        *,
        category: MemoryCategory | str | None = None,
        include_expired: bool = False,
    ) -> list[MemoryRecord]:
        """List memory records in stable order."""

        if category is None:
            rows = self._connection.execute(
                "SELECT * FROM memory_records ORDER BY category, key"
            ).fetchall()
        else:
            normalized_category = MemoryCategory(category)
            rows = self._connection.execute(
                "SELECT * FROM memory_records WHERE category = ? ORDER BY key",
                (normalized_category.value,),
            ).fetchall()
        records = [self._row_to_record(row) for row in rows]
        if include_expired:
            return records
        return [record for record in records if not record.is_expired]

    def delete(self, category: MemoryCategory | str, key: str) -> bool:
        """Delete a memory item and return whether a row was removed."""

        normalized_category = MemoryCategory(category)
        cursor = self._connection.execute(
            "DELETE FROM memory_records WHERE category = ? AND key = ?",
            (normalized_category.value, key),
        )
        self._connection.commit()
        return cursor.rowcount > 0

    def clear_category(self, category: MemoryCategory | str) -> int:
        """Delete every item in one memory category."""

        normalized_category = MemoryCategory(category)
        cursor = self._connection.execute(
            "DELETE FROM memory_records WHERE category = ?",
            (normalized_category.value,),
        )
        self._connection.commit()
        return cursor.rowcount

    def apply_retention(self, *, now: datetime | None = None) -> int:
        """Delete expired records and return the number removed."""

        timestamp = now or _utc_now()
        cursor = self._connection.execute(
            "DELETE FROM memory_records WHERE expires_at IS NOT NULL AND expires_at <= ?",
            (_to_iso(timestamp),),
        )
        self._connection.commit()
        return cursor.rowcount

    def retention_days_for_category(
        self,
        memory_spec: MemorySpec,
        category: MemoryCategory | str,
    ) -> int | None:
        """Read category-specific retention from a TeamSpec memory policy."""

        normalized_category = MemoryCategory(category)
        store_spec = getattr(memory_spec, normalized_category.value)
        return store_spec.retention_days

    def export_jsonl(self, path: str | Path, *, include_expired: bool = False) -> Path:
        """Export records to JSONL for inspection or future replay tests."""

        output_path = Path(path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        lines = [
            record.model_dump_json() + "\n"
            for record in self.list_records(include_expired=include_expired)
        ]
        output_path.write_text("".join(lines), encoding="utf-8")
        return output_path

    def _initialize_schema(self) -> None:
        self._connection.execute(
            """
            CREATE TABLE IF NOT EXISTS memory_records (
                id TEXT PRIMARY KEY,
                category TEXT NOT NULL,
                key TEXT NOT NULL,
                value_json TEXT NOT NULL,
                metadata_json TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                expires_at TEXT,
                redacted INTEGER NOT NULL DEFAULT 0,
                UNIQUE(category, key)
            )
            """
        )
        self._connection.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_memory_records_category_key
            ON memory_records(category, key)
            """
        )
        self._connection.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_memory_records_expires_at
            ON memory_records(expires_at)
            """
        )
        self._connection.commit()

    def _row_to_record(self, row: sqlite3.Row) -> MemoryRecord:
        return MemoryRecord(
            id=row["id"],
            category=MemoryCategory(row["category"]),
            key=row["key"],
            value=json.loads(row["value_json"]),
            metadata=json.loads(row["metadata_json"]),
            created_at=_from_iso(row["created_at"]),
            updated_at=_from_iso(row["updated_at"]),
            expires_at=_from_iso(row["expires_at"]),
            redacted=bool(row["redacted"]),
        )
