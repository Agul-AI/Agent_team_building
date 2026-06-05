"""YAML/JSON loading helpers for team specs."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from pydantic import ValidationError

from team_factory.specs.models import TeamSpec


class TeamSpecLoadError(ValueError):
    """Raised when a spec file cannot be parsed or validated."""


def _load_yaml_mapping(text: str, *, source: str) -> dict[str, Any]:
    try:
        raw = yaml.safe_load(text)
    except yaml.YAMLError as exc:
        raise TeamSpecLoadError(f"Failed to parse YAML from {source}: {exc}") from exc

    if raw is None:
        raise TeamSpecLoadError(f"Spec file is empty: {source}")
    if not isinstance(raw, dict):
        raise TeamSpecLoadError(f"Spec root must be a mapping/object: {source}")
    return raw


def load_team_spec(path: str | Path) -> TeamSpec:
    """Load and validate a team spec from a YAML file."""

    spec_path = Path(path)
    try:
        text = spec_path.read_text(encoding="utf-8")
    except OSError as exc:
        raise TeamSpecLoadError(f"Failed to read spec file {spec_path}: {exc}") from exc

    return load_team_spec_from_text(text, source=str(spec_path))


def load_team_spec_from_text(text: str, *, source: str = "<text>") -> TeamSpec:
    """Load and validate a team spec from YAML text."""

    raw = _load_yaml_mapping(text, source=source)
    try:
        return TeamSpec.model_validate(raw)
    except ValidationError as exc:
        raise TeamSpecLoadError(f"Invalid team spec {source}: {exc}") from exc
