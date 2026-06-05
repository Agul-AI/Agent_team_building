"""Run event models for the Phase 2 mock orchestrator."""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field


class EventType(str, Enum):
    """Event types emitted by the deterministic mock runtime."""

    RUN_STARTED = "run_started"
    AGENT_STARTED = "agent_started"
    AGENT_COMPLETED = "agent_completed"
    RUN_COMPLETED = "run_completed"
    RUN_FAILED = "run_failed"


class RunEvent(BaseModel):
    """A single structured event in a mock workflow run."""

    model_config = ConfigDict(extra="forbid")

    event_id: str = Field(default_factory=lambda: str(uuid4()))
    run_id: str
    type: EventType
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    workflow_id: str
    agent_id: str | None = None
    message: str
    data: dict[str, Any] = Field(default_factory=dict)
