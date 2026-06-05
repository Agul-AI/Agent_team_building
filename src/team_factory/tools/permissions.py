"""Authorization decision models for proposed tool calls."""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class AuthorizationStatus(StrEnum):
    """Possible outcomes of a tool authorization check."""

    ALLOWED = "allowed"
    REQUIRES_HUMAN_APPROVAL = "requires_human_approval"
    BLOCKED = "blocked"


class AuthorizationDecision(BaseModel):
    """Structured result from checking a proposed tool call."""

    model_config = ConfigDict(extra="forbid")

    status: AuthorizationStatus
    tool_id: str
    agent_id: str
    reason: str
    required_permissions: frozenset[str] = Field(default_factory=frozenset)
    missing_permissions: frozenset[str] = Field(default_factory=frozenset)
    approval_required: bool = False
    approval_id: str | None = None

    @property
    def allowed(self) -> bool:
        """Convenience boolean for callers."""

        return self.status == AuthorizationStatus.ALLOWED
