from __future__ import annotations

from team_factory.observability import (
    JsonlRunStore,
    build_trace_snapshot,
    compare_trace_snapshots,
)
from team_factory.orchestration.compiler import compile_workflow
from team_factory.specs.loader import load_team_spec


def _run_travel(task: str = "Plan a short trip."):
    spec = load_team_spec("team_specs/travel_planning_team.yaml")
    return compile_workflow(spec, "plan_trip").run(task)


def test_trace_snapshot_is_stable_across_run_ids_and_timestamps() -> None:
    first = build_trace_snapshot(_run_travel())
    second = build_trace_snapshot(_run_travel())

    comparison = compare_trace_snapshots(first, second)

    assert first.digest == second.digest
    assert comparison.matches is True
    assert first.agent_order == [
        "preference_gatherer",
        "destination_researcher",
        "budget_optimizer",
        "feasibility_critic",
        "itinerary_synthesizer",
    ]
    assert first.event_sequence[0].type == "run_started"


def test_trace_snapshot_comparison_reports_differences() -> None:
    expected = build_trace_snapshot(_run_travel("Plan a short trip."))
    actual = build_trace_snapshot(_run_travel("Plan a long trip."))

    comparison = compare_trace_snapshots(expected, actual)

    assert comparison.matches is False
    assert comparison.expected_digest != comparison.actual_digest
    assert comparison.differences
    assert any("input" in difference for difference in comparison.differences)


def test_jsonl_run_store_persists_records_and_exports_snapshot(tmp_path) -> None:
    store = JsonlRunStore(tmp_path / "runs.jsonl")
    run_result = _run_travel()

    record = store.append(run_result, metadata={"source": "test"})
    records = store.list_records()
    loaded = store.get(run_result.run_id)
    latest = store.latest()
    snapshot_path = store.export_snapshot(run_result.run_id, tmp_path / "snapshot.json")

    assert record.run_id == run_result.run_id
    assert len(records) == 1
    assert loaded is not None
    assert loaded.trace_snapshot.digest == record.trace_snapshot.digest
    assert latest is not None
    assert latest.run_id == run_result.run_id
    assert "travel_planning_team" in snapshot_path.read_text(encoding="utf-8")
