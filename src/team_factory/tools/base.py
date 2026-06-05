"""Tool manifest and call-request models.

The Phase 3 tool layer is deliberately declarative. It can answer whether a tool
call would be authorized, whether approval is required, and why a call is blocked,
but it cannot execute tools.
"""

from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from team_factory.specs.models import RiskLevel, SideEffectLevel, ToolSpec


class ToolExecutionMode(StrEnum):
    """Execution support level for a tool manifest."""

    MANIFEST_ONLY = "manifest_only"


class ToolManifest(BaseModel):
    """Normalized runtime-facing view of a declared tool."""

    model_config = ConfigDict(extra="forbid")

    id: str = Field(..., pattern=r"^[a-z][a-z0-9_\-]*$")
    provider: str | None = None
    description: str | None = None
    enabled: bool = True
    risk_level: RiskLevel = RiskLevel.LOW
    side_effect_level: SideEffectLevel = SideEffectLevel.NONE
    approval_required: bool = False
    permissions: frozenset[str] = Field(default_factory=frozenset)
    sandbox: str | None = None
    secrets_required: frozenset[str] = Field(default_factory=frozenset)
    input_schema: dict[str, Any] | None = None
    output_schema: dict[str, Any] | None = None
    rate_limits: dict[str, Any] = Field(default_factory=dict)
    execution_mode: ToolExecutionMode = ToolExecutionMode.MANIFEST_ONLY

    @classmethod
    def from_tool_spec(cls, spec: ToolSpec) -> ToolManifest:
        """Build a normalized manifest from a team-spec tool declaration."""

        return cls(
            id=spec.id,
            provider=spec.provider,
            description=spec.description,
            enabled=spec.enabled,
            risk_level=spec.risk_level,
            side_effect_level=spec.side_effect_level,
            approval_required=spec.approval_required,
            permissions=frozenset(spec.permissions),
            sandbox=spec.sandbox,
            secrets_required=frozenset(spec.secrets_required),
            input_schema=spec.input_schema,
            output_schema=spec.output_schema,
            rate_limits=spec.rate_limits,
        )

    @model_validator(mode="after")
    def ensure_risky_tools_require_approval(self) -> ToolManifest:
        """Keep manifest invariants aligned with spec validation."""

        if self.enabled and self.risk_level == RiskLevel.CRITICAL and not self.approval_required:
            msg = f"critical tool '{self.id}' must require approval"
            raise ValueError(msg)
        if (
            self.enabled
            and self.side_effect_level == SideEffectLevel.HIGH_IMPACT
            and not self.approval_required
        ):
            msg = f"high-impact tool '{self.id}' must require approval"
            raise ValueError(msg)
        return self

    @property
    def is_high_impact(self) -> bool:
        """Return whether the tool is high-impact by risk or side-effect level."""

        return (
            self.risk_level == RiskLevel.CRITICAL
            or self.side_effect_level == SideEffectLevel.HIGH_IMPACT
        )


class ToolCallRequest(BaseModel):
    """A proposed tool call used for authorization decisions."""

    model_config = ConfigDict(extra="forbid")

    tool_id: str = Field(..., pattern=r"^[a-z][a-z0-9_\-]*$")
    agent_id: str = Field(..., pattern=r"^[a-z][a-z0-9_\-]*$")
    purpose: str = Field(..., min_length=1)
    requested_permissions: frozenset[str] = Field(default_factory=frozenset)
    approved_by_human: bool = False
    approval_id: str | None = None
    input_preview: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def require_approval_id_when_approved(self) -> ToolCallRequest:
        """Require a traceable approval id when approval is claimed."""

        if self.approved_by_human and not self.approval_id:
            msg = "approved tool calls must include approval_id"
            raise ValueError(msg)
        return self
