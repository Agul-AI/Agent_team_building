from __future__ import annotations

from pathlib import Path

from team_factory.cli import main
from team_factory.observability import check_golden_snapshots, update_golden_snapshots
from team_factory.observability.golden import GoldenSnapshotStatus
from team_factory.specs.loader import load_team_spec

EXAMPLE_SPECS = [
    "team_specs/scientific_discovery_team.yaml",
    "team_specs/trading_strategy_research_team.yaml",
    "team_specs/travel_planning_team.yaml",
]


def test_checked_in_golden_snapshots_match_examples() -> None:
    results = []
    for spec_path in EXAMPLE_SPECS:
        results.extend(check_golden_snapshots(load_team_spec(spec_path)))

    assert len(results) == 3
    assert all(result.status == GoldenSnapshotStatus.MATCH for result in results)
    assert all(Path(result.snapshot_path).exists() for result in results)


def test_golden_update_then_check_in_temp_dir(tmp_path) -> None:
    spec = load_team_spec("team_specs/travel_planning_team.yaml")

    missing = check_golden_snapshots(spec, snapshot_dir=tmp_path)
    updated = update_golden_snapshots(spec, snapshot_dir=tmp_path)
    matched = check_golden_snapshots(spec, snapshot_dir=tmp_path)

    assert missing[0].status == GoldenSnapshotStatus.MISSING
    assert updated[0].status == GoldenSnapshotStatus.UPDATED
    assert matched[0].status == GoldenSnapshotStatus.MATCH


def test_cli_golden_check_passes_for_checked_in_goldens(capsys) -> None:
    exit_code = main(["golden-check", *EXAMPLE_SPECS])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert output.count("MATCH") == 3


def test_cli_golden_update_requires_explicit_approval(tmp_path, capsys) -> None:
    exit_code = main(
        [
            "golden-update",
            "team_specs/travel_planning_team.yaml",
            "--snapshot-dir",
            str(tmp_path),
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 1
    assert "requires --approve" in captured.err


def test_cli_golden_update_with_approval_writes_snapshot(tmp_path, capsys) -> None:
    exit_code = main(
        [
            "golden-update",
            "team_specs/travel_planning_team.yaml",
            "--snapshot-dir",
            str(tmp_path),
            "--approve",
        ]
    )

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "UPDATED" in output
    assert len(list(tmp_path.glob("*.json"))) == 1
