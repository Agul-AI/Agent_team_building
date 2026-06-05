"""Tool registry and manifest-only authorization layer."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

from team_factory.specs.models import TeamSpec
from team_factory.tools.base import ToolCallRequest, ToolManifest
from team_factory.tools.permissions import AuthorizationDecision, AuthorizationStatus


class ToolRegistryError(ValueError):
    """Raised when a registry cannot be built or queried."""


@dataclass(frozen=True)
class ToolRegistry:
    """Registry of normalized tool manifests plus agent allowlists.

    This class does not execute tools. Its job is to answer whether a proposed
    call is allowed, blocked, or waiting for explicit human approval.
    """

    manifests: dict[str, ToolManifest]
    agent_allowed_tools: dict[str, frozenset[str]]

    @classmethod
    def from_team_spec(cls, team: TeamSpec) -> ToolRegistry:
        """Create a registry from a validated team spec."""

        manifests = {tool.id: ToolManifest.from_tool_spec(tool) for tool in team.tools}
        agent_allowed_tools = {
            agent.id: frozenset(agent.allowed_tools)
            for agent in team.agents
        }
        return cls(manifests=manifests, agent_allowed_tools=agent_allowed_tools)

    @classmethod
    def from_manifests(
        cls,
        manifests: Iterable[ToolManifest],
        *,
        agent_allowed_tools: dict[str, Iterable[str]] | None = None,
    ) -> ToolRegistry:
        """Create a registry from explicit manifests for tests or future adapters."""

        manifest_map: dict[str, ToolManifest] = {}
        duplicates: set[str] = set()
        for manifest in manifests:
            if manifest.id in manifest_map:
                duplicates.add(manifest.id)
            manifest_map[manifest.id] = manifest
        if duplicates:
            msg = "duplicate tool manifest ids: " + ", ".join(sorted(duplicates))
            raise ToolRegistryError(msg)

        allowed = {
            agent_id: frozenset(tool_ids)
            for agent_id, tool_ids in (agent_allowed_tools or {}).items()
        }
        return cls(manifests=manifest_map, agent_allowed_tools=allowed)

    def get(self, tool_id: str) -> ToolManifest:
        """Return one manifest or raise a clear error."""

        try:
            return self.manifests[tool_id]
        except KeyError as exc:
            raise ToolRegistryError(f"unknown tool '{tool_id}'") from exc

    def list_tool_ids(self) -> list[str]:
        """Return all registered tool ids in stable order."""

        return sorted(self.manifests)

    def allowed_tools_for_agent(self, agent_id: str) -> frozenset[str]:
        """Return a specific agent's declared tool allowlist."""

        return self.agent_allowed_tools.get(agent_id, frozenset())

    def authorize(self, request: ToolCallRequest) -> AuthorizationDecision:
        """Authorize a proposed tool call without executing it."""

        manifest = self.manifests.get(request.tool_id)
        if manifest is None:
            return AuthorizationDecision(
                status=AuthorizationStatus.BLOCKED,
                tool_id=request.tool_id,
                agent_id=request.agent_id,
                reason="tool is not registered",
            )

        if not manifest.enabled:
            return AuthorizationDecision(
                status=AuthorizationStatus.BLOCKED,
                tool_id=request.tool_id,
                agent_id=request.agent_id,
                reason="tool is disabled",
                approval_required=manifest.approval_required,
                required_permissions=manifest.permissions,
            )

        agent_allowlist = self.allowed_tools_for_agent(request.agent_id)
        if request.tool_id not in agent_allowlist:
            return AuthorizationDecision(
                status=AuthorizationStatus.BLOCKED,
                tool_id=request.tool_id,
                agent_id=request.agent_id,
                reason="agent is not allowed to use this tool",
                approval_required=manifest.approval_required,
                required_permissions=manifest.permissions,
            )

        missing_permissions = manifest.permissions - request.requested_permissions
        if missing_permissions:
            return AuthorizationDecision(
                status=AuthorizationStatus.BLOCKED,
                tool_id=request.tool_id,
                agent_id=request.agent_id,
                reason="required permissions are missing",
                required_permissions=manifest.permissions,
                missing_permissions=missing_permissions,
                approval_required=manifest.approval_required,
            )

        if manifest.approval_required and not request.approved_by_human:
            return AuthorizationDecision(
                status=AuthorizationStatus.REQUIRES_HUMAN_APPROVAL,
                tool_id=request.tool_id,
                agent_id=request.agent_id,
                reason="human approval is required before this tool can be used",
                required_permissions=manifest.permissions,
                approval_required=True,
            )

        return AuthorizationDecision(
            status=AuthorizationStatus.ALLOWED,
            tool_id=request.tool_id,
            agent_id=request.agent_id,
            reason="tool call is authorized in manifest-only mode",
            required_permissions=manifest.permissions,
            approval_required=manifest.approval_required,
            approval_id=request.approval_id,
        )
