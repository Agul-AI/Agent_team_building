"""Memory data models for local Phase 4 persistence."""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class MemoryCategory(StrEnum):
    """Supported memory categories aligned with TeamSpec.memory."""

    SHORT_TERM = "short_term"
    PROJECT = "project"
    LONG_TERM = "long_term"
    USER_PREFERENCES = "user_preferences"
    DOMAIN_KNOWLEDGE = "domain_knowledge"


class MemoryRecord(BaseModel):
    """One persisted memory item.

    The value is stored as JSON-compatible data. Sensitive keys can be redacted
    before persistence, and records can have optional expiration timestamps.
    """

    model_config = ConfigDict(extra="forbid")

    id: str
    category: MemoryCategory
    key: str = Field(..., min_length=1)
    value: dict[str, Any]
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime
    expires_at: datetime | None = None
    redacted: bool = False

    @property
    def is_expired(self) -> bool:
        """Return whether the record is expired relative to current UTC time."""

        return self.expires_at is not None and self.expires_at <= datetime.now(UTC)
