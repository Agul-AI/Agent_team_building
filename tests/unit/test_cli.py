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
