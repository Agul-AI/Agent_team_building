#!/usr/bin/env python3
"""Run deterministic mock evaluations for one or more team specs."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from team_factory.evaluation import EvaluationHarness, write_markdown_report
from team_factory.specs.loader import TeamSpecLoadError, load_team_spec


def main(argv: list[str]) -> int:
    if not argv:
        print("Usage: run_mock_evals.py <spec.yaml> [<spec.yaml> ...]", file=sys.stderr)
        return 2

    output_dir = Path("examples/artifacts/evaluation_reports")
    harness = EvaluationHarness()
    exit_code = 0
    for arg in argv:
        path = Path(arg)
        try:
            spec = load_team_spec(path)
        except TeamSpecLoadError as exc:
            print(f"FAIL {path}: {exc}", file=sys.stderr)
            exit_code = 1
            continue

        report = harness.run_team(spec)
        output_path = write_markdown_report(report, output_dir / f"{spec.team_id}.md")
        print(f"{report.status.value.upper():7} {path}: wrote {output_path}")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
