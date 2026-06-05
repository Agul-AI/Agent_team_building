#!/usr/bin/env python3
"""Validate one or more team spec YAML files."""

from __future__ import annotations

import sys
from pathlib import Path

from team_factory.specs.loader import TeamSpecLoadError, load_team_spec


def main(argv: list[str]) -> int:
    if not argv:
        print("Usage: validate_specs.py <spec.yaml> [<spec.yaml> ...]", file=sys.stderr)
        return 2

    exit_code = 0
    for arg in argv:
        path = Path(arg)
        try:
            spec = load_team_spec(path)
        except TeamSpecLoadError as exc:
            exit_code = 1
            print(f"FAIL {path}: {exc}", file=sys.stderr)
        else:
            print(f"OK   {path}: {spec.team_id} v{spec.team_version}")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
