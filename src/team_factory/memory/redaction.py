"""Simple deterministic redaction utilities for memory persistence."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

DEFAULT_SENSITIVE_KEYWORDS = frozenset(
    {
        "api_key",
        "apikey",
        "auth_token",
        "bearer",
        "brokerage_credentials",
        "credential",
        "credentials",
        "cvv",
        "password",
        "passport",
        "passport_number",
        "payment",
        "payment_information",
        "secret",
        "ssn",
        "token",
    }
)

DEFAULT_REDACTION_TEXT = "[REDACTED]"

_SECRETISH_PATTERN = re.compile(
    r"(?i)(api[_-]?key|secret|token|password|bearer)\s*[:=]\s*([^\s,;]+)"
)


@dataclass(frozen=True)
class RedactionReport:
    """Result of redacting JSON-like data."""

    data: Any
    redacted: bool
    paths: tuple[str, ...] = field(default_factory=tuple)


def redact_data(
    data: Any,
    *,
    sensitive_keywords: frozenset[str] = DEFAULT_SENSITIVE_KEYWORDS,
    replacement: str = DEFAULT_REDACTION_TEXT,
) -> RedactionReport:
    """Redact sensitive-looking keys and secret-looking string fragments.

    This is a conservative local foundation, not a complete DLP system. Future
    phases can replace or extend it with policy packs and richer PII detection.
    """

    paths: list[str] = []

    def should_redact_key(key: str) -> bool:
        normalized = key.strip().lower().replace("-", "_")
        return any(keyword in normalized for keyword in sensitive_keywords)

    def walk(value: Any, path: str) -> Any:
        if isinstance(value, dict):
            output: dict[str, Any] = {}
            for key, child in value.items():
                child_path = f"{path}.{key}" if path else str(key)
                if should_redact_key(str(key)):
                    paths.append(child_path)
                    output[str(key)] = replacement
                else:
                    output[str(key)] = walk(child, child_path)
            return output

        if isinstance(value, list):
            return [walk(child, f"{path}[{index}]") for index, child in enumerate(value)]

        if isinstance(value, tuple):
            return [walk(child, f"{path}[{index}]") for index, child in enumerate(value)]

        if isinstance(value, str):
            matches = list(_SECRETISH_PATTERN.finditer(value))
            if not matches:
                return value
            paths.append(path or "<root>")
            return _SECRETISH_PATTERN.sub(lambda match: f"{match.group(1)}={replacement}", value)

        return value

    redacted_data = walk(data, "")
    return RedactionReport(data=redacted_data, redacted=bool(paths), paths=tuple(paths))
