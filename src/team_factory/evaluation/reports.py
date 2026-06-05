"""Report output helpers for Phase 5 evaluations."""

from __future__ import annotations

from pathlib import Path

from team_factory.evaluation.models import EvaluationReport


def write_markdown_report(report: EvaluationReport, path: str | Path) -> Path:
    """Write an evaluation report as Markdown."""

    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(report.to_markdown(), encoding="utf-8")
    return output_path
