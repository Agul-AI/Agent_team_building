from __future__ import annotations

import json
from pathlib import Path

from team_factory.cli import main


def test_cli_validate_specs(capsys) -> None:
    exit_code = main(["validate", "team_specs/travel_planning_team.yaml"])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "travel_planning_team v0.1.0" in captured.out


def test_cli_workflow_order_json(capsys) -> None:
    exit_code = main(
        [
            "workflow-order",
            "team_specs/trading_strategy_research_team.yaml",
            "--workflow-id",
            "research_backtest_review",
            "--json",
        ]
    )

    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert exit_code == 0
    assert payload["team_id"] == "trading_strategy_research_team"
    assert payload["agent_order"] == [
        "strategy_ideator",
        "market_data_researcher",
        "backtest_engineer",
        "risk_manager",
        "overfitting_critic",
        "final_synthesizer",
    ]


def test_cli_run_mock(capsys) -> None:
    exit_code = main(
        [
            "run-mock",
            "team_specs/scientific_discovery_team.yaml",
            "Survey automated discovery.",
            "--workflow-id",
            "main",
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "scientific_discovery_team" in captured.out
    assert "final_synthesizer" in captured.out


def test_cli_tool_check_allowed(capsys) -> None:
    exit_code = main(
        [
            "tool-check",
            "team_specs/travel_planning_team.yaml",
            "--agent-id",
            "destination_researcher",
            "--tool-id",
            "web_search",
            "--purpose",
            "Research museums.",
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "allowed" in captured.out


def test_cli_tool_check_blocked_returns_nonzero(capsys) -> None:
    exit_code = main(
        [
            "tool-check",
            "team_specs/travel_planning_team.yaml",
            "--agent-id",
            "preference_gatherer",
            "--tool-id",
            "web_search",
            "--purpose",
            "Try unauthorized search.",
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 2
    assert "blocked" in captured.out


def test_cli_memory_put_get_list_delete(tmp_path, capsys) -> None:
    db_path = tmp_path / "memory.sqlite3"

    put_code = main(
        [
            "memory-put",
            "--db",
            str(db_path),
            "--category",
            "project",
            "--key",
            "decision:test",
            "--value-json",
            '{"decision":"use cli","api_key":"secret"}',
            "--metadata-json",
            '{"source":"test"}',
        ]
    )
    put_out = capsys.readouterr().out

    get_code = main(
        [
            "memory-get",
            "--db",
            str(db_path),
            "--category",
            "project",
            "--key",
            "decision:test",
            "--json",
        ]
    )
    get_payload = json.loads(capsys.readouterr().out)

    list_code = main(["memory-list", "--db", str(db_path), "--category", "project"])
    list_out = capsys.readouterr().out

    delete_code = main(
        [
            "memory-delete",
            "--db",
            str(db_path),
            "--category",
            "project",
            "--key",
            "decision:test",
        ]
    )
    delete_out = capsys.readouterr().out

    assert put_code == get_code == list_code == delete_code == 0
    assert "stored project:decision:test" in put_out
    assert get_payload["value"] == {"api_key": "[REDACTED]", "decision": "use cli"}
    assert "project:decision:test" in list_out
    assert "deleted project:decision:test" in delete_out


def test_cli_eval_writes_reports(tmp_path, capsys) -> None:
    out_dir = tmp_path / "eval_reports"

    exit_code = main(
        [
            "eval",
            "team_specs/scientific_discovery_team.yaml",
            "team_specs/trading_strategy_research_team.yaml",
            "team_specs/travel_planning_team.yaml",
            "--out-dir",
            str(out_dir),
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert captured.out.count("PASSED") == 3
    report_paths = sorted(Path(out_dir).glob("*.md"))
    assert [path.name for path in report_paths] == [
        "scientific_discovery_team.md",
        "trading_strategy_research_team.md",
        "travel_planning_team.md",
    ]


def test_cli_trace_snapshot_compare_and_run_log(tmp_path, capsys) -> None:
    snapshot_a = tmp_path / "snapshot_a.json"
    snapshot_b = tmp_path / "snapshot_b.json"
    run_log = tmp_path / "runs.jsonl"

    run_code = main(
        [
            "run-mock",
            "team_specs/travel_planning_team.yaml",
            "Plan a short trip.",
            "--workflow-id",
            "plan_trip",
            "--run-log",
            str(run_log),
            "--snapshot-out",
            str(snapshot_a),
        ]
    )
    run_out = capsys.readouterr().out

    snapshot_code = main(
        [
            "trace-snapshot",
            "team_specs/travel_planning_team.yaml",
            "Plan a short trip.",
            "--workflow-id",
            "plan_trip",
            "--out",
            str(snapshot_b),
        ]
    )
    snapshot_out = capsys.readouterr().out

    compare_code = main(["trace-compare", str(snapshot_a), str(snapshot_b)])
    compare_out = capsys.readouterr().out

    list_code = main(["run-log-list", "--run-log", str(run_log)])
    list_out = capsys.readouterr().out
    run_id = list_out.split()[0]

    get_code = main(["run-log-get", "--run-log", str(run_log), "--run-id", run_id])
    get_out = capsys.readouterr().out

    assert run_code == snapshot_code == compare_code == list_code == get_code == 0
    assert "persisted run" in run_out
    assert snapshot_a.exists()
    assert snapshot_b.exists()
    assert "digest=" in snapshot_out
    assert compare_out.startswith("MATCH")
    assert "travel_planning_team" in list_out
    assert "Mock run for team" in get_out


def test_cli_trace_compare_detects_difference(tmp_path, capsys) -> None:
    snapshot_a = tmp_path / "snapshot_a.json"
    snapshot_b = tmp_path / "snapshot_b.json"
    main(
        [
            "trace-snapshot",
            "team_specs/travel_planning_team.yaml",
            "Plan a short trip.",
            "--workflow-id",
            "plan_trip",
            "--out",
            str(snapshot_a),
        ]
    )
    capsys.readouterr()
    main(
        [
            "trace-snapshot",
            "team_specs/travel_planning_team.yaml",
            "Plan a long trip.",
            "--workflow-id",
            "plan_trip",
            "--out",
            str(snapshot_b),
        ]
    )
    capsys.readouterr()

    compare_code = main(["trace-compare", str(snapshot_a), str(snapshot_b)])
    compare_out = capsys.readouterr().out

    assert compare_code == 2
    assert compare_out.startswith("DIFF")
