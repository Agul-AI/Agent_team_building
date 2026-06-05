from __future__ import annotations

from team_factory.evaluation import EvaluationHarness, EvaluationStatus, write_markdown_report
from team_factory.evaluation.models import PropertyCheckStatus, StructuralCheckStatus
from team_factory.specs.loader import load_team_spec, load_team_spec_from_text


def test_evaluation_harness_runs_sequential_travel_scenario() -> None:
    spec = load_team_spec("team_specs/travel_planning_team.yaml")

    report = EvaluationHarness().run_team(spec, workflow_id="plan_trip")

    assert report.team_id == "travel_planning_team"
    assert report.workflow_id == "plan_trip"
    assert report.status == EvaluationStatus.PASSED
    assert report.summary.total_scenarios == 1
    assert report.summary.passed == 1
    assert report.summary.failed == 0
    assert report.summary.skipped == 0
    assert report.summary.not_scored_properties == 3

    scenario = report.scenario_results[0]
    assert scenario.scenario_id == "weekend_city_trip"
    assert scenario.run_id is not None
    assert scenario.final_output is not None
    assert all(check.status == StructuralCheckStatus.PASSED for check in scenario.structural_checks)
    assert {check.name for check in scenario.structural_checks} == {
        "run_completed",
        "final_output_present",
        "agent_outputs_present",
        "events_present",
    }
    assert all(check.status == PropertyCheckStatus.NOT_SCORED for check in scenario.property_checks)


def test_evaluation_harness_runs_critique_revision_scientific_scenario() -> None:
    spec = load_team_spec("team_specs/scientific_discovery_team.yaml")

    report = EvaluationHarness().run_team(spec, workflow_id="main")

    assert report.status == EvaluationStatus.PASSED
    assert report.summary.total_scenarios == 1
    assert report.summary.passed == 1
    scenario = report.scenario_results[0]
    assert scenario.status == EvaluationStatus.PASSED
    assert scenario.run_id is not None
    assert scenario.final_output is not None
    assert len(scenario.property_checks) == 3


def test_evaluation_harness_runs_supervisor_worker_trading_scenario() -> None:
    spec = load_team_spec("team_specs/trading_strategy_research_team.yaml")

    report = EvaluationHarness().run_team(spec, workflow_id="research_backtest_review")

    assert report.status == EvaluationStatus.PASSED
    assert report.summary.total_scenarios == 1
    assert report.summary.passed == 1
    scenario = report.scenario_results[0]
    assert scenario.status == EvaluationStatus.PASSED
    assert scenario.run_id is not None
    assert scenario.final_output is not None
    assert len(scenario.property_checks) == 3


def test_evaluation_harness_skips_still_unsupported_workflow_type() -> None:
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
evaluation:
  scenarios:
    - id: "debate_case"
      input: "Compare options."
      expected_properties: ["records a debate"]
"""
    )

    report = EvaluationHarness().run_team(spec, workflow_id="main")

    assert report.status == EvaluationStatus.SKIPPED
    assert report.summary.total_scenarios == 1
    assert report.summary.skipped == 1
    scenario = report.scenario_results[0]
    assert scenario.status == EvaluationStatus.SKIPPED
    assert scenario.skipped_reason is not None
    assert "supports only" in scenario.skipped_reason
    assert len(scenario.property_checks) == 1


def test_evaluation_report_markdown_contains_summary_and_scenarios(tmp_path) -> None:
    spec = load_team_spec("team_specs/travel_planning_team.yaml")
    report = EvaluationHarness().run_team(spec, workflow_id="plan_trip")

    markdown = report.to_markdown()
    output_path = write_markdown_report(report, tmp_path / "report.md")

    assert "# Evaluation Report: travel_planning_team" in markdown
    assert "## Summary" in markdown
    assert "### weekend_city_trip" in markdown
    assert "Expected properties not scored: 3" in markdown
    assert output_path.read_text(encoding="utf-8") == markdown


def test_evaluation_harness_reports_no_scenarios_as_skipped() -> None:
    spec = load_team_spec_from_text(
        """
schema_version: "0.1"
team_id: "no_eval_team"
team_version: "0.1.0"
name: "No Eval Team"
domain: "test"
purpose: "Has no scenarios."
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
evaluation:
  metrics: ["basic_quality"]
"""
    )

    report = EvaluationHarness().run_team(spec, workflow_id="main")

    assert report.status == EvaluationStatus.SKIPPED
    assert report.summary.total_scenarios == 0
    assert report.scenario_results == []
    assert "No evaluation scenarios" in report.notes[-1]


def test_evaluation_harness_fails_unknown_workflow_as_skipped() -> None:
    spec = load_team_spec("team_specs/travel_planning_team.yaml")

    report = EvaluationHarness().run_team(spec, workflow_id="missing")

    assert report.status == EvaluationStatus.SKIPPED
    assert report.summary.skipped == 1
    assert "does not define workflow" in report.scenario_results[0].skipped_reason
