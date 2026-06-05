"""Replay-oriented JSONL run-log persistence."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from team_factory.observability.traces import RunTraceSnapshot, build_trace_snapshot
from team_factory.orchestration.runtime import RunResult

RUN_LOG_SCHEMA_VERSION = "0.1"


class PersistedRunRecord(BaseModel):
    """Full run result plus deterministic trace snapshot for replay work."""

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["0.1"] = RUN_LOG_SCHEMA_VERSION
    recorded_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    run_result: RunResult
    trace_snapshot: RunTraceSnapshot
    metadata: dict[str, Any] = Field(default_factory=dict)

    @property
    def run_id(self) -> str:
        """Return the persisted run id."""

        return self.run_result.run_id


class JsonlRunStore:
    """Append-only JSONL store for replay-oriented mock run records."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)

    def append(
        self,
        run_result: RunResult,
        *,
        metadata: dict[str, Any] | None = None,
    ) -> PersistedRunRecord:
        """Persist one run result plus its deterministic trace snapshot."""

        record = PersistedRunRecord(
            run_result=run_result,
            trace_snapshot=build_trace_snapshot(run_result),
            metadata=metadata or {},
        )
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(record.model_dump_json() + "\n")
        return record

    def list_records(self) -> list[PersistedRunRecord]:
        """Read all persisted run records."""

        if not self.path.exists():
            return []
        records: list[PersistedRunRecord] = []
        for line in self.path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                records.append(PersistedRunRecord.model_validate_json(line))
        return records

    def get(self, run_id: str) -> PersistedRunRecord | None:
        """Return a persisted run by id."""

        for record in self.list_records():
            if record.run_id == run_id:
                return record
        return None

    def latest(self) -> PersistedRunRecord | None:
        """Return the latest persisted run record."""

        records = self.list_records()
        return records[-1] if records else None

    def export_snapshot(self, run_id: str, path: str | Path) -> Path:
        """Write a persisted run's deterministic trace snapshot to disk."""

        record = self.get(run_id)
        if record is None:
            raise ValueError(f"run id not found: {run_id}")
        output_path = Path(path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(record.trace_snapshot.model_dump_json(indent=2), encoding="utf-8")
        return output_path
