"""Checked-in golden snapshot helpers."""

from __future__ import annotations

import json
import re
from enum import StrEnum
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field

from team_factory.observability.traces import (
    RunTraceSnapshot,
    compare_trace_snapshots,
)
from team_factory.orchestration.compiler import compile_workflow
from team_factory.specs.models import EvaluationScenario, TeamSpec

DEFAULT_GOLDEN_SNAPSHOT_DIR = Path("tests/golden_snapshots")


class GoldenSnapshotStatus(StrEnum):
    """Statuses for golden snapshot checks/updates."""

    MATCH = "match"
    DIFF = "diff"
    MISSING = "missing"
    UPDATED = "updated"
    ERROR = "error"


class GoldenSnapshotResult(BaseModel):
    """Result for one golden snapshot case."""

    model_config = ConfigDict(extra="forbid")

    status: GoldenSnapshotStatus
    team_id: str
    workflow_id: str
    scenario_id: str
    snapshot_path: str
    expected_digest: str | None = None
    actual_digest: str | None = None
    differences: list[str] = Field(default_factory=list)
    error: str | None = None

    @property
    def ok(self) -> bool:
        """Return whether this result represents an acceptable check/update."""

        return self.status in {GoldenSnapshotStatus.MATCH, GoldenSnapshotStatus.UPDATED}


def check_golden_snapshots(
    team: TeamSpec,
    *,
    snapshot_dir: str | Path = DEFAULT_GOLDEN_SNAPSHOT_DIR,
    workflow_id: str | None = None,
) -> list[GoldenSnapshotResult]:
    """Compare current deterministic snapshots against checked-in goldens."""

    return [
        _check_one(team, scenario, snapshot_dir=Path(snapshot_dir), workflow_id=workflow_id)
        for scenario in team.evaluation.scenarios
    ]


def update_golden_snapshots(
    team: TeamSpec,
    *,
    snapshot_dir: str | Path = DEFAULT_GOLDEN_SNAPSHOT_DIR,
    workflow_id: str | None = None,
) -> list[GoldenSnapshotResult]:
    """Write current deterministic snapshots to the golden snapshot directory."""

    return [
        _update_one(team, scenario, snapshot_dir=Path(snapshot_dir), workflow_id=workflow_id)
        for scenario in team.evaluation.scenarios
    ]


def build_snapshot_for_scenario(
    team: TeamSpec,
    scenario: EvaluationScenario,
    *,
    workflow_id: str | None = None,
) -> RunTraceSnapshot:
    """Run one scenario through the deterministic mock workflow and snapshot it."""

    selected_workflow_id = _resolve_workflow_id(team, workflow_id)
    workflow = compile_workflow(team, selected_workflow_id)
    run_result = workflow.run(scenario.input)
    return RunTraceSnapshot.from_run_result(run_result)


def golden_snapshot_path(
    team: TeamSpec,
    scenario: EvaluationScenario,
    *,
    snapshot_dir: str | Path = DEFAULT_GOLDEN_SNAPSHOT_DIR,
    workflow_id: str | None = None,
) -> Path:
    """Return the conventional checked-in snapshot path for a scenario."""

    selected_workflow_id = _resolve_workflow_id(team, workflow_id)
    filename = "__".join(
        [
            _safe_filename_part(team.team_id),
            _safe_filename_part(selected_workflow_id),
            _safe_filename_part(scenario.id),
        ]
    )
    return Path(snapshot_dir) / f"{filename}.json"


def read_golden_snapshot(path: str | Path) -> RunTraceSnapshot:
    """Read a golden snapshot JSON file."""

    return RunTraceSnapshot.model_validate_json(Path(path).read_text(encoding="utf-8"))


def write_golden_snapshot(snapshot: RunTraceSnapshot, path: str | Path) -> Path:
    """Write a golden snapshot JSON file with stable formatting."""

    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    payload = snapshot.model_dump(mode="json")
    output_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return output_path


def _check_one(
    team: TeamSpec,
    scenario: EvaluationScenario,
    *,
    snapshot_dir: Path,
    workflow_id: str | None,
) -> GoldenSnapshotResult:
    path = golden_snapshot_path(
        team,
        scenario,
        snapshot_dir=snapshot_dir,
        workflow_id=workflow_id,
    )
    selected_workflow_id = _resolve_workflow_id(team, workflow_id)
    try:
        actual = build_snapshot_for_scenario(team, scenario, workflow_id=selected_workflow_id)
    except Exception as exc:
        return _result(
            status=GoldenSnapshotStatus.ERROR,
            team=team,
            workflow_id=selected_workflow_id,
            scenario=scenario,
            path=path,
            error=str(exc),
        )

    if not path.exists():
        return _result(
            status=GoldenSnapshotStatus.MISSING,
            team=team,
            workflow_id=selected_workflow_id,
            scenario=scenario,
            path=path,
            actual_digest=actual.digest,
            differences=["golden snapshot file is missing"],
        )

    expected = read_golden_snapshot(path)
    comparison = compare_trace_snapshots(expected, actual)
    return _result(
        status=GoldenSnapshotStatus.MATCH if comparison.matches else GoldenSnapshotStatus.DIFF,
        team=team,
        workflow_id=selected_workflow_id,
        scenario=scenario,
        path=path,
        expected_digest=comparison.expected_digest,
        actual_digest=comparison.actual_digest,
        differences=comparison.differences,
    )


def _update_one(
    team: TeamSpec,
    scenario: EvaluationScenario,
    *,
    snapshot_dir: Path,
    workflow_id: str | None,
) -> GoldenSnapshotResult:
    selected_workflow_id = _resolve_workflow_id(team, workflow_id)
    path = golden_snapshot_path(
        team,
        scenario,
        snapshot_dir=snapshot_dir,
        workflow_id=selected_workflow_id,
    )
    try:
        snapshot = build_snapshot_for_scenario(team, scenario, workflow_id=selected_workflow_id)
    except Exception as exc:
        return _result(
            status=GoldenSnapshotStatus.ERROR,
            team=team,
            workflow_id=selected_workflow_id,
            scenario=scenario,
            path=path,
            error=str(exc),
        )
    write_golden_snapshot(snapshot, path)
    return _result(
        status=GoldenSnapshotStatus.UPDATED,
        team=team,
        workflow_id=selected_workflow_id,
        scenario=scenario,
        path=path,
        actual_digest=snapshot.digest,
    )


def _result(
    *,
    status: GoldenSnapshotStatus,
    team: TeamSpec,
    workflow_id: str,
    scenario: EvaluationScenario,
    path: Path,
    expected_digest: str | None = None,
    actual_digest: str | None = None,
    differences: list[str] | None = None,
    error: str | None = None,
) -> GoldenSnapshotResult:
    return GoldenSnapshotResult(
        status=status,
        team_id=team.team_id,
        workflow_id=workflow_id,
        scenario_id=scenario.id,
        snapshot_path=str(path),
        expected_digest=expected_digest,
        actual_digest=actual_digest,
        differences=differences or [],
        error=error,
    )


def _resolve_workflow_id(team: TeamSpec, workflow_id: str | None) -> str:
    if workflow_id is not None:
        return workflow_id
    if len(team.workflows) == 1:
        return team.workflows[0].id
    raise ValueError("workflow_id is required when a team declares multiple workflows")


def _safe_filename_part(value: str) -> str:
    return re.sub(r"[^a-zA-Z0-9_.-]+", "_", value).strip("_")
