"""Structured observability event models."""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field


class ObservabilityEventType(StrEnum):
    """Top-level observability event categories."""

    AUDIT = "audit"
    RUN = "run"
    API_REQUEST = "api_request"


class AuditStatus(StrEnum):
    """Status values for audit events."""

    SUCCEEDED = "succeeded"
    FAILED = "failed"
    BLOCKED = "blocked"


class ObservabilityEvent(BaseModel):
    """Base event envelope for JSONL logs."""

    model_config = ConfigDict(extra="forbid")

    event_id: str = Field(default_factory=lambda: str(uuid4()))
    event_type: ObservabilityEventType
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    correlation_id: str | None = None
    details: dict[str, Any] = Field(default_factory=dict)


class AuditEvent(ObservabilityEvent):
    """Audit event for local API/CLI-adjacent actions."""

    event_type: ObservabilityEventType = ObservabilityEventType.AUDIT
    action: str
    status: AuditStatus
    subject: str | None = None
    actor: str = "local_user"


class RunLogRecord(ObservabilityEvent):
    """Compact structured record for a completed deterministic mock run."""

    event_type: ObservabilityEventType = ObservabilityEventType.RUN
    run_id: str
    team_id: str
    team_version: str
    workflow_id: str
    status: str
    agent_count: int
    event_count: int
    final_output_preview: str
