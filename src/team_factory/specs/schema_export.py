"""Export JSON Schema for the current TeamSpec model."""

from __future__ import annotations

import json
from pathlib import Path

from team_factory.specs.models import TeamSpec


def export_team_spec_schema(path: str | Path) -> Path:
    """Write the TeamSpec JSON Schema to disk and return the output path."""

    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(TeamSpec.model_json_schema(), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return output_path
