#!/usr/bin/env python3
"""Run the local Agent Team Factory CLI without installing the package."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from team_factory.cli import main

if __name__ == "__main__":
    raise SystemExit(main())
