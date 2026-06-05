"""Evaluation harness foundation for Phase 5.

Phase 5 supports deterministic mock scenario execution and static reports. It
does not use LLM judges, real tools, domain-specific scorers, or production eval
services.
"""

from team_factory.evaluation.harness import EvaluationHarness
from team_factory.evaluation.models import (
    EvaluationReport,
    EvaluationStatus,
    PropertyCheck,
    PropertyCheckStatus,
    ScenarioResult,
    StructuralCheck,
    StructuralCheckStatus,
)
from team_factory.evaluation.reports import write_markdown_report

__all__ = [
    "EvaluationHarness",
    "EvaluationReport",
    "EvaluationStatus",
    "PropertyCheck",
    "PropertyCheckStatus",
    "ScenarioResult",
    "StructuralCheck",
    "StructuralCheckStatus",
    "write_markdown_report",
]
