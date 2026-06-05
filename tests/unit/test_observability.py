from __future__ import annotations

from team_factory.observability import AuditStatus, JsonlEventLogger
from team_factory.orchestration.compiler import compile_workflow
from team_factory.specs.loader import load_team_spec


def test_jsonl_event_logger_writes_audit_and_run_events(tmp_path) -> None:
    log_path = tmp_path / "events.jsonl"
    logger = JsonlEventLogger(log_path)

    audit = logger.append_audit(
        action="test.action",
        status=AuditStatus.SUCCEEDED,
        subject="unit-test",
        details={"ok": True},
        correlation_id="corr-1",
    )
    spec = load_team_spec("team_specs/travel_planning_team.yaml")
    result = compile_workflow(spec, "plan_trip").run("Plan a short trip.")
    run_event = logger.append_run_result(result, correlation_id="corr-1")

    events = logger.read_events()

    assert audit.event_id is not None
    assert run_event.run_id == result.run_id
    assert len(events) == 2
    assert events[0]["event_type"] == "audit"
    assert events[0]["action"] == "test.action"
    assert events[1]["event_type"] == "run"
    assert events[1]["team_id"] == "travel_planning_team"
    assert events[1]["agent_count"] == 5
