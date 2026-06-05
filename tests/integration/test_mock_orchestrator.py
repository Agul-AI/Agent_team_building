from __future__ import annotations

import pytest

from team_factory.orchestration.compiler import compile_workflow, ordered_agent_ids_for_workflow
from team_factory.orchestration.events import EventType
from team_factory.orchestration.runtime import WorkflowRunError
from team_factory.specs.loader import load_team_spec


def test_compile_sequential_workflow_orders_agents() -> None:
    spec = load_team_spec("team_specs/travel_planning_team.yaml")

    ordered_ids = ordered_agent_ids_for_workflow(spec, "plan_trip")

    assert ordered_ids == [
        "preference_gatherer",
        "destination_researcher",
        "budget_optimizer",
        "feasibility_critic",
        "itinerary_synthesizer",
    ]


def test_run_sequential_workflow_with_mock_agents() -> None:
    spec = load_team_spec("team_specs/travel_planning_team.yaml")
    workflow = compile_workflow(spec, "plan_trip")

    result = workflow.run("Plan a three-day museum-focused trip under $1,500.")

    assert result.status == "completed"
    assert result.team_id == "travel_planning_team"
    assert result.workflow_id == "plan_trip"
    assert len(result.agent_outputs) == 5
    assert result.agent_outputs[0].agent_id == "preference_gatherer"
    assert result.agent_outputs[-1].agent_id == "itinerary_synthesizer"
    assert "final agent 'itinerary_synthesizer'" in result.final_output

    event_types = [event.type for event in result.events]
    assert event_types[0] == EventType.RUN_STARTED
    assert event_types[-1] == EventType.RUN_COMPLETED
    assert event_types.count(EventType.AGENT_STARTED) == 5
    assert event_types.count(EventType.AGENT_COMPLETED) == 5


def test_phase2_rejects_unsupported_workflow_types() -> None:
    spec = load_team_spec("team_specs/scientific_discovery_team.yaml")

    with pytest.raises(WorkflowRunError, match="Phase 2 only supports"):
        compile_workflow(spec, "main")


def test_compile_unknown_workflow_fails_clearly() -> None:
    spec = load_team_spec("team_specs/travel_planning_team.yaml")

    with pytest.raises(WorkflowRunError, match="does not define workflow"):
        compile_workflow(spec, "missing_workflow")
