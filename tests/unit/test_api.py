from __future__ import annotations

from pathlib import Path

from team_factory.api import TeamFactoryAPI
from team_factory.observability import JsonlEventLogger


def test_api_health_and_validate_spec(tmp_path) -> None:
    api = TeamFactoryAPI(audit_log_path=tmp_path / "audit.jsonl")

    health = api.handle("GET", "/health")
    validate = api.handle(
        "POST",
        "/specs/validate",
        {"spec_path": "team_specs/travel_planning_team.yaml"},
    )

    assert health.status_code == 200
    assert health.body["ok"] is True
    assert validate.status_code == 200
    assert validate.body["team_id"] == "travel_planning_team"
    assert validate.body["workflow_ids"] == ["plan_trip"]


def test_api_workflow_order_and_mock_run_are_observable(tmp_path) -> None:
    audit_path = tmp_path / "audit.jsonl"
    api = TeamFactoryAPI(audit_log_path=audit_path)

    order = api.handle(
        "POST",
        "/workflows/order",
        {
            "spec_path": "team_specs/trading_strategy_research_team.yaml",
            "workflow_id": "research_backtest_review",
        },
    )
    run = api.handle(
        "POST",
        "/runs/mock",
        {
            "spec_path": "team_specs/travel_planning_team.yaml",
            "workflow_id": "plan_trip",
            "task": "Plan a short trip.",
        },
    )
    events = JsonlEventLogger(audit_path).read_events()

    assert order.status_code == 200
    assert order.body["agent_order"][0] == "strategy_ideator"
    assert run.status_code == 200
    assert run.body["run_result"]["team_id"] == "travel_planning_team"
    assert any(event["event_type"] == "run" for event in events)
    assert any(event.get("action") == "POST /runs/mock" for event in events)


def test_api_tool_check_blocks_unauthorized_agent() -> None:
    api = TeamFactoryAPI()

    response = api.handle(
        "POST",
        "/tools/check",
        {
            "spec_path": "team_specs/travel_planning_team.yaml",
            "agent_id": "preference_gatherer",
            "tool_id": "web_search",
            "purpose": "Try unauthorized search.",
        },
    )

    assert response.status_code == 403
    assert response.body["ok"] is False
    assert response.body["decision"]["status"] == "blocked"


def test_api_eval_mock_writes_markdown_report(tmp_path) -> None:
    api = TeamFactoryAPI(eval_output_dir=tmp_path / "eval_reports")

    response = api.handle(
        "POST",
        "/eval/mock",
        {"spec_path": "team_specs/scientific_discovery_team.yaml"},
    )

    output_path = Path(response.body["output_path"])
    assert response.status_code == 200
    assert response.body["report"]["status"] == "passed"
    assert output_path.exists()
    assert "scientific_discovery_team" in output_path.read_text(encoding="utf-8")


def test_api_unknown_route_and_bad_request() -> None:
    api = TeamFactoryAPI()

    missing = api.handle("GET", "/missing")
    bad = api.handle("POST", "/specs/validate", {})

    assert missing.status_code == 404
    assert missing.body["ok"] is False
    assert bad.status_code == 400
    assert bad.body["ok"] is False
    assert "spec_path" in bad.body["error"]
