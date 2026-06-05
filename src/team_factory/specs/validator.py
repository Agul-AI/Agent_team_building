"""Validation entry points for team specs."""

from __future__ import annotations

from pathlib import Path

from team_factory.specs.loader import TeamSpecLoadError, load_team_spec
from team_factory.specs.models import TeamSpec


def validate_team_spec(spec: TeamSpec) -> TeamSpec:
    """Validate an already constructed TeamSpec.

    Pydantic model construction performs all Phase 1 validation. This function is
    intentionally small to provide a stable future extension point for lint rules.
    """

    return TeamSpec.model_validate(spec.model_dump())


def validate_team_spec_file(path: str | Path) -> TeamSpec:
    """Load and validate a team spec file."""

    return load_team_spec(path)


def validation_error_message(path: str | Path) -> str | None:
    """Return a human-readable validation error, or None if the file is valid."""

    try:
        validate_team_spec_file(path)
    except TeamSpecLoadError as exc:
        return str(exc)
    return None
