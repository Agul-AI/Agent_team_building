"""Evaluation report models for deterministic Phase 5 scenarios."""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class EvaluationStatus(StrEnum):
    """High-level scenario/report status."""

    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
    PARTIAL = "partial"


class StructuralCheckStatus(StrEnum):
    """Status for deterministic structural checks."""

    PASSED = "passed"
    FAILED = "failed"


class PropertyCheckStatus(StrEnum):
    """Status for expected-property checks.

    Expected properties are recorded but not semantically scored in Phase 5.
    """

    NOT_SCORED = "not_scored"


class StructuralCheck(BaseModel):
    """Deterministic check over a mock run result."""

    model_config = ConfigDict(extra="forbid")

    name: str
    status: StructuralCheckStatus
    reason: str


class PropertyCheck(BaseModel):
    """Placeholder result for expected properties declared in a scenario."""

    model_config = ConfigDict(extra="forbid")

    property: str
    status: PropertyCheckStatus = PropertyCheckStatus.NOT_SCORED
    reason: str = "Semantic property scoring is not implemented in Phase 5."


class ScenarioResult(BaseModel):
    """Result for one evaluation scenario."""

    model_config = ConfigDict(extra="forbid")

    scenario_id: str
    status: EvaluationStatus
    workflow_id: str | None = None
    input: str | dict[str, Any]
    expected_properties: list[str] = Field(default_factory=list)
    structural_checks: list[StructuralCheck] = Field(default_factory=list)
    property_checks: list[PropertyCheck] = Field(default_factory=list)
    run_id: str | None = None
    final_output: str | None = None
    skipped_reason: str | None = None
    error: str | None = None


class EvaluationSummary(BaseModel):
    """Aggregate report counts."""

    model_config = ConfigDict(extra="forbid")

    total_scenarios: int = 0
    passed: int = 0
    failed: int = 0
    skipped: int = 0
    not_scored_properties: int = 0


class EvaluationReport(BaseModel):
    """Deterministic mock evaluation report."""

    model_config = ConfigDict(extra="forbid")

    team_id: str
    team_version: str
    workflow_id: str | None
    status: EvaluationStatus
    generated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    declared_metrics: list[str] = Field(default_factory=list)
    scenario_results: list[ScenarioResult] = Field(default_factory=list)
    summary: EvaluationSummary = Field(default_factory=EvaluationSummary)
    notes: list[str] = Field(default_factory=list)

    def to_markdown(self) -> str:
        """Render a compact Markdown report for local inspection."""

        lines = [
            f"# Evaluation Report: {self.team_id}",
            "",
            f"- Team version: `{self.team_version}`",
            f"- Workflow: `{self.workflow_id or 'not selected'}`",
            f"- Status: `{self.status.value}`",
            f"- Generated at: `{self.generated_at.isoformat()}`",
            "",
            "## Summary",
            "",
            f"- Total scenarios: {self.summary.total_scenarios}",
            f"- Passed: {self.summary.passed}",
            f"- Failed: {self.summary.failed}",
            f"- Skipped: {self.summary.skipped}",
            f"- Expected properties not scored: {self.summary.not_scored_properties}",
            "",
            "## Declared metrics",
            "",
        ]
        if self.declared_metrics:
            lines.extend(f"- {metric}" for metric in self.declared_metrics)
        else:
            lines.append("- None declared")

        if self.notes:
            lines.extend(["", "## Notes", ""])
            lines.extend(f"- {note}" for note in self.notes)

        lines.extend(["", "## Scenarios", ""])
        if not self.scenario_results:
            lines.append("No scenarios were declared.")
            return "\n".join(lines) + "\n"

        for scenario in self.scenario_results:
            lines.extend(
                [
                    f"### {scenario.scenario_id}",
                    "",
                    f"- Status: `{scenario.status.value}`",
                ]
            )
            if scenario.workflow_id:
                lines.append(f"- Workflow: `{scenario.workflow_id}`")
            if scenario.run_id:
                lines.append(f"- Run id: `{scenario.run_id}`")
            if scenario.skipped_reason:
                lines.append(f"- Skipped reason: {scenario.skipped_reason}")
            if scenario.error:
                lines.append(f"- Error: {scenario.error}")
            if scenario.final_output:
                lines.append(f"- Final output: {scenario.final_output}")

            if scenario.structural_checks:
                lines.extend(["", "Structural checks:"])
                for check in scenario.structural_checks:
                    lines.append(f"- `{check.status.value}` {check.name}: {check.reason}")

            if scenario.property_checks:
                lines.extend(["", "Expected properties:"])
                for check in scenario.property_checks:
                    lines.append(
                        f"- `{check.status.value}` {check.property}: {check.reason}"
                    )
            lines.append("")

        return "\n".join(lines).rstrip() + "\n"
