from __future__ import annotations

import pytest
from pydantic import ValidationError

from team_factory.specs.loader import load_team_spec
from team_factory.specs.models import RiskLevel, SideEffectLevel
from team_factory.tools.base import ToolCallRequest, ToolManifest
from team_factory.tools.permissions import AuthorizationStatus
from team_factory.tools.registry import ToolRegistry, ToolRegistryError


def test_registry_loads_team_tool_manifests() -> None:
    spec = load_team_spec("team_specs/travel_planning_team.yaml")

    registry = ToolRegistry.from_team_spec(spec)

    assert registry.list_tool_ids() == [
        "booking_api",
        "calculator",
        "flight_search",
        "maps_api",
        "web_search",
    ]
    assert registry.get("booking_api").enabled is False
    assert registry.allowed_tools_for_agent("destination_researcher") == frozenset(
        {"web_search", "maps_api", "flight_search"}
    )


def test_allowed_read_only_tool_call_is_authorized_manifest_only() -> None:
    spec = load_team_spec("team_specs/travel_planning_team.yaml")
    registry = ToolRegistry.from_team_spec(spec)
    request = ToolCallRequest(
        tool_id="web_search",
        agent_id="destination_researcher",
        purpose="Research destination opening hours.",
    )

    decision = registry.authorize(request)

    assert decision.status == AuthorizationStatus.ALLOWED
    assert decision.allowed is True
    assert decision.reason == "tool call is authorized in manifest-only mode"


def test_agent_tool_allowlist_is_enforced() -> None:
    spec = load_team_spec("team_specs/travel_planning_team.yaml")
    registry = ToolRegistry.from_team_spec(spec)
    request = ToolCallRequest(
        tool_id="web_search",
        agent_id="preference_gatherer",
        purpose="Try to search before allowed.",
    )

    decision = registry.authorize(request)

    assert decision.status == AuthorizationStatus.BLOCKED
    assert decision.allowed is False
    assert decision.reason == "agent is not allowed to use this tool"


def test_disabled_tool_is_blocked_even_if_approval_is_present() -> None:
    spec = load_team_spec("team_specs/travel_planning_team.yaml")
    registry = ToolRegistry.from_team_spec(spec)
    request = ToolCallRequest(
        tool_id="booking_api",
        agent_id="itinerary_synthesizer",
        purpose="Attempt to book travel.",
        approved_by_human=True,
        approval_id="approval-123",
    )

    decision = registry.authorize(request)

    assert decision.status == AuthorizationStatus.BLOCKED
    assert decision.reason == "tool is disabled"


def test_unknown_tool_is_blocked() -> None:
    spec = load_team_spec("team_specs/travel_planning_team.yaml")
    registry = ToolRegistry.from_team_spec(spec)
    request = ToolCallRequest(
        tool_id="unknown_tool",
        agent_id="destination_researcher",
        purpose="Try unknown tool.",
    )

    decision = registry.authorize(request)

    assert decision.status == AuthorizationStatus.BLOCKED
    assert decision.reason == "tool is not registered"


def test_missing_permissions_are_blocked() -> None:
    manifest = ToolManifest(
        id="database_reader",
        risk_level=RiskLevel.MEDIUM,
        side_effect_level=SideEffectLevel.READ_ONLY,
        permissions=frozenset({"db:read:approved"}),
    )
    registry = ToolRegistry.from_manifests(
        [manifest],
        agent_allowed_tools={"researcher": ["database_reader"]},
    )
    request = ToolCallRequest(
        tool_id="database_reader",
        agent_id="researcher",
        purpose="Read approved project records.",
    )

    decision = registry.authorize(request)

    assert decision.status == AuthorizationStatus.BLOCKED
    assert decision.reason == "required permissions are missing"
    assert decision.missing_permissions == frozenset({"db:read:approved"})


def test_required_permissions_allow_call_when_granted() -> None:
    manifest = ToolManifest(
        id="database_reader",
        risk_level=RiskLevel.MEDIUM,
        side_effect_level=SideEffectLevel.READ_ONLY,
        permissions=frozenset({"db:read:approved"}),
    )
    registry = ToolRegistry.from_manifests(
        [manifest],
        agent_allowed_tools={"researcher": ["database_reader"]},
    )
    request = ToolCallRequest(
        tool_id="database_reader",
        agent_id="researcher",
        purpose="Read approved project records.",
        requested_permissions=frozenset({"db:read:approved"}),
    )

    decision = registry.authorize(request)

    assert decision.status == AuthorizationStatus.ALLOWED
    assert decision.allowed is True


def test_enabled_critical_tool_requires_human_approval() -> None:
    manifest = ToolManifest(
        id="purchase_api",
        risk_level=RiskLevel.CRITICAL,
        side_effect_level=SideEffectLevel.HIGH_IMPACT,
        approval_required=True,
    )
    registry = ToolRegistry.from_manifests(
        [manifest],
        agent_allowed_tools={"buyer": ["purchase_api"]},
    )
    request = ToolCallRequest(
        tool_id="purchase_api",
        agent_id="buyer",
        purpose="Attempt purchase.",
    )

    decision = registry.authorize(request)

    assert decision.status == AuthorizationStatus.REQUIRES_HUMAN_APPROVAL
    assert decision.approval_required is True


def test_enabled_critical_tool_is_allowed_after_traceable_approval() -> None:
    manifest = ToolManifest(
        id="purchase_api",
        risk_level=RiskLevel.CRITICAL,
        side_effect_level=SideEffectLevel.HIGH_IMPACT,
        approval_required=True,
    )
    registry = ToolRegistry.from_manifests(
        [manifest],
        agent_allowed_tools={"buyer": ["purchase_api"]},
    )
    request = ToolCallRequest(
        tool_id="purchase_api",
        agent_id="buyer",
        purpose="Attempt purchase.",
        approved_by_human=True,
        approval_id="approval-456",
    )

    decision = registry.authorize(request)

    assert decision.status == AuthorizationStatus.ALLOWED
    assert decision.approval_id == "approval-456"


def test_approval_claim_requires_approval_id() -> None:
    with pytest.raises(ValidationError, match="approved tool calls must include approval_id"):
        ToolCallRequest(
            tool_id="purchase_api",
            agent_id="buyer",
            purpose="Attempt purchase.",
            approved_by_human=True,
        )


def test_duplicate_manifest_ids_are_rejected() -> None:
    manifest = ToolManifest(id="calculator")

    with pytest.raises(ToolRegistryError, match="duplicate tool manifest ids"):
        ToolRegistry.from_manifests([manifest, manifest])
