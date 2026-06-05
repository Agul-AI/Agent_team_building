"""Spec version helpers.

Phase 1 only supports schema version 0.1. Migrations are intentionally deferred
until a second schema version exists.
"""

from __future__ import annotations

from team_factory.specs.models import SUPPORTED_SCHEMA_VERSION


def is_supported_schema_version(schema_version: str) -> bool:
    """Return whether a schema version is supported by this package."""

    return schema_version == SUPPORTED_SCHEMA_VERSION
