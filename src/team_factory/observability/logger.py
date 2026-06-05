"""JSONL observability logger."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pydantic import BaseModel

from team_factory.observability.models import AuditEvent, AuditStatus, RunLogRecord
from team_factory.orchestration.runtime import RunResult


class JsonlEventLogger:
    """Append-only JSONL logger for local audit/run observability."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)

    def append(self, event: BaseModel | dict[str, Any]) -> None:
        """Append one event to the JSONL file."""

        self.path.parent.mkdir(parents=True, exist_ok=True)
        if isinstance(event, BaseModel):
            line = event.model_dump_json()
        else:
            line = json.dumps(event, sort_keys=True)
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(line + "\n")

    def append_audit(
        self,
        *,
        action: str,
        status: AuditStatus,
        subject: str | None = None,
        details: dict[str, Any] | None = None,
        correlation_id: str | None = None,
    ) -> AuditEvent:
        """Create and append an audit event."""

        event = AuditEvent(
            action=action,
            status=status,
            subject=subject,
            details=details or {},
            correlation_id=correlation_id,
        )
        self.append(event)
        return event

    def append_run_result(
        self,
        run_result: RunResult,
        *,
        correlation_id: str | None = None,
    ) -> RunLogRecord:
        """Create and append a compact run log record from a mock RunResult."""

        preview = run_result.final_output[:240]
        event = RunLogRecord(
            run_id=run_result.run_id,
            team_id=run_result.team_id,
            team_version=run_result.team_version,
            workflow_id=run_result.workflow_id,
            status=run_result.status,
            agent_count=len(run_result.agent_outputs),
            event_count=len(run_result.events),
            final_output_preview=preview,
            correlation_id=correlation_id,
        )
        self.append(event)
        return event

    def read_events(self) -> list[dict[str, Any]]:
        """Read all JSONL events from disk."""

        if not self.path.exists():
            return []
        return [
            json.loads(line)
            for line in self.path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
