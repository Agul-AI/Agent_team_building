from __future__ import annotations

import pytest

from team_factory.orchestration.compiler import compile_workflow, ordered_agent_ids_for_workflow
from team_factory.orchestration.events import EventType
from team_factory.orchestration.runtime import WorkflowRunError
from team_factory.specs.loader import load_team_spec, load_team_spec_from_text


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


def test_compile_critique_revision_workflow_orders_agents() -> None:
    spec = load_team_spec("team_specs/scientific_discovery_team.yaml")

    ordered_ids = ordered_agent_ids_for_workflow(spec, "main")

    assert ordered_ids == [
        "literature_reviewer",
        "hypothesis_generator",
        "experiment_designer",
        "scientific_critic",
        "final_synthesizer",
    ]


def test_run_critique_revision_workflow_with_mock_agents() -> None:
    spec = load_team_spec("team_specs/scientific_discovery_team.yaml")
    workflow = compile_workflow(spec, "main")

    result = workflow.run("Survey recent automated materials discovery approaches.")

    assert result.status == "completed"
    assert result.team_id == "scientific_discovery_team"
    assert len(result.agent_outputs) == 5
    assert result.agent_outputs[-1].agent_id == "final_synthesizer"
    assert "final agent 'final_synthesizer'" in result.final_output


def test_compile_supervisor_worker_workflow_orders_agents() -> None:
    spec = load_team_spec("team_specs/trading_strategy_research_team.yaml")

    ordered_ids = ordered_agent_ids_for_workflow(spec, "research_backtest_review")

    assert ordered_ids == [
        "strategy_ideator",
        "market_data_researcher",
        "backtest_engineer",
        "risk_manager",
        "overfitting_critic",
        "final_synthesizer",
    ]


def test_run_supervisor_worker_workflow_with_mock_agents() -> None:
    spec = load_team_spec("team_specs/trading_strategy_research_team.yaml")
    workflow = compile_workflow(spec, "research_backtest_review")

    result = workflow.run("Evaluate a moving-average crossover strategy for simulation only.")

    assert result.status == "completed"
    assert result.team_id == "trading_strategy_research_team"
    assert len(result.agent_outputs) == 6
    assert result.agent_outputs[0].agent_id == "strategy_ideator"
    assert result.agent_outputs[-1].agent_id == "final_synthesizer"
    assert result.events[0].data["execution_order"] == [
        "strategy_ideator",
        "market_data_researcher",
        "backtest_engineer",
        "risk_manager",
        "overfitting_critic",
        "final_synthesizer",
    ]


def test_mock_compiler_rejects_still_unsupported_workflow_types() -> None:
    spec = load_team_spec_from_text(
        """
schema_version: "0.1"
team_id: "debate_team"
team_version: "0.1.0"
name: "Debate Team"
domain: "test"
purpose: "Still unsupported workflow type."
agents:
  - id: "agent_a"
    role: "researcher"
    goal: "Argue A."
  - id: "agent_b"
    role: "critic"
    goal: "Argue B."
workflows:
  - id: "main"
    type: "debate"
    steps: ["agent_a", "agent_b"]
    stopping_criteria:
      max_iterations: 1
"""
    )

    with pytest.raises(WorkflowRunError, match="supports only"):
        compile_workflow(spec, "main")


def test_compile_unknown_workflow_fails_clearly() -> None:
    spec = load_team_spec("team_specs/travel_planning_team.yaml")

    with pytest.raises(WorkflowRunError, match="does not define workflow"):
        compile_workflow(spec, "missing_workflow")
