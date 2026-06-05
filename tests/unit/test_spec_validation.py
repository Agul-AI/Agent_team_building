from __future__ import annotations

from pathlib import Path

import pytest

from team_factory.specs.loader import TeamSpecLoadError, load_team_spec, load_team_spec_from_text
from team_factory.specs.models import TeamSpec
from team_factory.specs.validator import validate_team_spec

ROOT = Path(__file__).resolve().parents[2]
TEAM_SPECS = ROOT / "team_specs"


def test_example_team_specs_load() -> None:
    paths = sorted(TEAM_SPECS.glob("*.yaml"))
    assert {path.name for path in paths} == {
        "scientific_discovery_team.yaml",
        "trading_strategy_research_team.yaml",
        "travel_planning_team.yaml",
    }

    specs = [load_team_spec(path) for path in paths]

    assert all(isinstance(spec, TeamSpec) for spec in specs)
    assert {spec.team_id for spec in specs} == {
        "scientific_discovery_team",
        "trading_strategy_research_team",
        "travel_planning_team",
    }


def test_validate_team_spec_round_trip() -> None:
    spec = load_team_spec(TEAM_SPECS / "scientific_discovery_team.yaml")

    validated = validate_team_spec(spec)

    assert validated.team_id == "scientific_discovery_team"
    assert validated.model_dump() == spec.model_dump()


def test_duplicate_agent_ids_are_rejected() -> None:
    text = """
schema_version: "0.1"
team_id: "bad_team"
team_version: "0.1.0"
name: "Bad Team"
domain: "test"
purpose: "Invalid duplicate agents."
agents:
  - id: "planner"
    role: "planner"
    goal: "Plan."
  - id: "planner"
    role: "critic"
    goal: "Critique."
workflows:
  - id: "main"
    type: "sequential"
    steps: ["planner"]
    stopping_criteria:
      max_iterations: 1
"""

    with pytest.raises(TeamSpecLoadError, match="duplicate agent ids"):
        load_team_spec_from_text(text)


def test_unknown_workflow_agent_reference_is_rejected() -> None:
    text = """
schema_version: "0.1"
team_id: "bad_team"
team_version: "0.1.0"
name: "Bad Team"
domain: "test"
purpose: "Invalid workflow reference."
agents:
  - id: "planner"
    role: "planner"
    goal: "Plan."
workflows:
  - id: "main"
    type: "sequential"
    steps: ["planner", "missing_agent"]
    stopping_criteria:
      max_iterations: 1
"""

    with pytest.raises(TeamSpecLoadError, match="references unknown agents"):
        load_team_spec_from_text(text)


def test_unknown_agent_tool_reference_is_rejected() -> None:
    text = """
schema_version: "0.1"
team_id: "bad_team"
team_version: "0.1.0"
name: "Bad Team"
domain: "test"
purpose: "Invalid tool reference."
agents:
  - id: "planner"
    role: "planner"
    goal: "Plan."
    allowed_tools: ["missing_tool"]
workflows:
  - id: "main"
    type: "sequential"
    steps: ["planner"]
    stopping_criteria:
      max_iterations: 1
"""

    with pytest.raises(TeamSpecLoadError, match="references unknown tools"):
        load_team_spec_from_text(text)


def test_workflow_without_stopping_criteria_limit_is_rejected() -> None:
    text = """
schema_version: "0.1"
team_id: "bad_team"
team_version: "0.1.0"
name: "Bad Team"
domain: "test"
purpose: "Invalid stopping criteria."
agents:
  - id: "planner"
    role: "planner"
    goal: "Plan."
workflows:
  - id: "main"
    type: "sequential"
    steps: ["planner"]
    stopping_criteria:
      require_terminal_node: true
"""

    with pytest.raises(TeamSpecLoadError, match="stopping_criteria must include"):
        load_team_spec_from_text(text)


def test_enabled_critical_tool_requires_approval() -> None:
    text = """
schema_version: "0.1"
team_id: "bad_team"
team_version: "0.1.0"
name: "Bad Team"
domain: "test"
purpose: "Invalid critical tool."
agents:
  - id: "planner"
    role: "planner"
    goal: "Plan."
    allowed_tools: ["broker_api"]
workflows:
  - id: "main"
    type: "sequential"
    steps: ["planner"]
    stopping_criteria:
      max_iterations: 1
tools:
  - id: "broker_api"
    risk_level: "critical"
    side_effect_level: "high_impact"
    approval_required: false
"""

    with pytest.raises(TeamSpecLoadError, match="critical tool 'broker_api'"):
        load_team_spec_from_text(text)


def test_high_impact_safety_actions_require_human_review() -> None:
    text = """
schema_version: "0.1"
team_id: "bad_team"
team_version: "0.1.0"
name: "Bad Team"
domain: "test"
purpose: "Invalid high-impact safety gate."
agents:
  - id: "planner"
    role: "planner"
    goal: "Plan."
workflows:
  - id: "main"
    type: "sequential"
    steps: ["planner"]
    stopping_criteria:
      max_iterations: 1
safety:
  high_impact_actions:
    - "making_purchase"
  human_review:
    required_before: []
"""

    with pytest.raises(TeamSpecLoadError, match="high_impact_actions must also be listed"):
        load_team_spec_from_text(text)
