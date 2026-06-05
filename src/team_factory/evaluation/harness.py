"""Deterministic mock evaluation harness for Phase 5."""

from __future__ import annotations

from dataclasses import dataclass

from team_factory.evaluation.models import (
    EvaluationReport,
    EvaluationStatus,
    EvaluationSummary,
    PropertyCheck,
    ScenarioResult,
    StructuralCheck,
    StructuralCheckStatus,
)
from team_factory.orchestration.compiler import compile_workflow
from team_factory.orchestration.runtime import RunResult, WorkflowRunError
from team_factory.specs.models import EvaluationScenario, TeamSpec


@dataclass(frozen=True)
class EvaluationHarness:
    """Run deterministic scenario evaluations over mock workflows.

    The harness currently checks structural execution success only. It records
    declared metrics and expected properties but does not semantically score them.
    """

    default_workflow_id: str | None = None

    def run_team(
        self,
        team: TeamSpec,
        *,
        workflow_id: str | None = None,
    ) -> EvaluationReport:
        """Run every declared scenario for a team and return a report."""

        selected_workflow_id = self._resolve_workflow_id(
            team,
            workflow_id or self.default_workflow_id,
        )
        scenarios = team.evaluation.scenarios
        notes = [
            "Phase 5 evaluates deterministic mock-run structure only.",
            "Declared metrics and expected properties are recorded but not semantically scored.",
        ]

        if not scenarios:
            return self._build_report(
                team=team,
                workflow_id=selected_workflow_id,
                scenario_results=[],
                notes=notes + ["No evaluation scenarios are declared in this team spec."],
            )

        try:
            compiled_workflow = compile_workflow(team, selected_workflow_id)
        except WorkflowRunError as exc:
            scenario_results = [
                self._skipped_result(
                    scenario,
                    workflow_id=selected_workflow_id,
                    reason=str(exc),
                )
                for scenario in scenarios
            ]
            return self._build_report(
                team=team,
                workflow_id=selected_workflow_id,
                scenario_results=scenario_results,
                notes=notes,
            )

        scenario_results: list[ScenarioResult] = []
        for scenario in scenarios:
            try:
                run_result = compiled_workflow.run(scenario.input)
            except Exception as exc:  # pragma: no cover - defensive future-proofing
                scenario_results.append(
                    ScenarioResult(
                        scenario_id=scenario.id,
                        status=EvaluationStatus.FAILED,
                        workflow_id=compiled_workflow.workflow.id,
                        input=scenario.input,
                        expected_properties=scenario.expected_properties,
                        property_checks=self._property_checks(scenario),
                        error=str(exc),
                    )
                )
                continue

            scenario_results.append(
                self._completed_result(
                    scenario,
                    workflow_id=compiled_workflow.workflow.id,
                    run_result=run_result,
                )
            )

        return self._build_report(
            team=team,
            workflow_id=compiled_workflow.workflow.id,
            scenario_results=scenario_results,
            notes=notes,
        )

    def _resolve_workflow_id(self, team: TeamSpec, workflow_id: str | None) -> str | None:
        """Resolve a workflow id for reports when the team has a single workflow."""

        if workflow_id is not None:
            return workflow_id
        if len(team.workflows) == 1:
            return team.workflows[0].id
        return None

    def _completed_result(
        self,
        scenario: EvaluationScenario,
        *,
        workflow_id: str,
        run_result: RunResult,
    ) -> ScenarioResult:
        structural_checks = self._structural_checks(run_result)
        status = (
            EvaluationStatus.PASSED
            if all(check.status == StructuralCheckStatus.PASSED for check in structural_checks)
            else EvaluationStatus.FAILED
        )
        return ScenarioResult(
            scenario_id=scenario.id,
            status=status,
            workflow_id=workflow_id,
            input=scenario.input,
            expected_properties=scenario.expected_properties,
            structural_checks=structural_checks,
            property_checks=self._property_checks(scenario),
            run_id=run_result.run_id,
            final_output=run_result.final_output,
        )

    def _skipped_result(
        self,
        scenario: EvaluationScenario,
        *,
        workflow_id: str | None,
        reason: str,
    ) -> ScenarioResult:
        return ScenarioResult(
            scenario_id=scenario.id,
            status=EvaluationStatus.SKIPPED,
            workflow_id=workflow_id,
            input=scenario.input,
            expected_properties=scenario.expected_properties,
            property_checks=self._property_checks(scenario),
            skipped_reason=reason,
        )

    def _structural_checks(self, run_result: RunResult) -> list[StructuralCheck]:
        return [
            self._check(
                name="run_completed",
                passed=run_result.status == "completed",
                pass_reason="Run status is completed.",
                fail_reason=f"Run status is {run_result.status!r}.",
            ),
            self._check(
                name="final_output_present",
                passed=bool(run_result.final_output.strip()),
                pass_reason="Final output is non-empty.",
                fail_reason="Final output is empty.",
            ),
            self._check(
                name="agent_outputs_present",
                passed=bool(run_result.agent_outputs),
                pass_reason=f"Run produced {len(run_result.agent_outputs)} agent output(s).",
                fail_reason="Run produced no agent outputs.",
            ),
            self._check(
                name="events_present",
                passed=bool(run_result.events),
                pass_reason=f"Run emitted {len(run_result.events)} event(s).",
                fail_reason="Run emitted no events.",
            ),
        ]

    def _check(
        self,
        *,
        name: str,
        passed: bool,
        pass_reason: str,
        fail_reason: str,
    ) -> StructuralCheck:
        return StructuralCheck(
            name=name,
            status=StructuralCheckStatus.PASSED if passed else StructuralCheckStatus.FAILED,
            reason=pass_reason if passed else fail_reason,
        )

    def _property_checks(self, scenario: EvaluationScenario) -> list[PropertyCheck]:
        return [PropertyCheck(property=prop) for prop in scenario.expected_properties]

    def _build_report(
        self,
        *,
        team: TeamSpec,
        workflow_id: str | None,
        scenario_results: list[ScenarioResult],
        notes: list[str],
    ) -> EvaluationReport:
        summary = self._summary(scenario_results)
        return EvaluationReport(
            team_id=team.team_id,
            team_version=team.team_version,
            workflow_id=workflow_id,
            status=self._report_status(summary),
            declared_metrics=team.evaluation.metrics,
            scenario_results=scenario_results,
            summary=summary,
            notes=notes,
        )

    def _summary(self, results: list[ScenarioResult]) -> EvaluationSummary:
        return EvaluationSummary(
            total_scenarios=len(results),
            passed=sum(result.status == EvaluationStatus.PASSED for result in results),
            failed=sum(result.status == EvaluationStatus.FAILED for result in results),
            skipped=sum(result.status == EvaluationStatus.SKIPPED for result in results),
            not_scored_properties=sum(len(result.property_checks) for result in results),
        )

    def _report_status(self, summary: EvaluationSummary) -> EvaluationStatus:
        if summary.total_scenarios == 0:
            return EvaluationStatus.SKIPPED
        if summary.failed:
            return EvaluationStatus.FAILED
        if summary.skipped == summary.total_scenarios:
            return EvaluationStatus.SKIPPED
        if summary.skipped:
            return EvaluationStatus.PARTIAL
        return EvaluationStatus.PASSED


def run_mock_evaluation(
    team: TeamSpec,
    *,
    workflow_id: str | None = None,
) -> EvaluationReport:
    """Convenience wrapper for deterministic mock evaluation."""

    return EvaluationHarness().run_team(team, workflow_id=workflow_id)
