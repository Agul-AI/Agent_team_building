#!/usr/bin/env python3
"""Serve the local Team Factory API skeleton without installing the package."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from team_factory.api.server import main

if __name__ == "__main__":
    raise SystemExit(main())
