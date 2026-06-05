"""Deterministic trace snapshots for mock run regression tests."""

from __future__ import annotations

import hashlib
import json
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from team_factory.orchestration.runtime import AgentOutput, RunResult

TRACE_SCHEMA_VERSION = "0.1"


class TraceAgentStep(BaseModel):
    """Stable agent-output projection for trace snapshots."""

    model_config = ConfigDict(extra="forbid")

    agent_id: str
    role: str
    goal: str
    summary: str
    prior_agent_outputs: list[str] = Field(default_factory=list)


class TraceEventStep(BaseModel):
    """Stable event projection for trace snapshots.

    Non-deterministic event fields such as event ids and timestamps are omitted.
    """

    model_config = ConfigDict(extra="forbid")

    type: str
    agent_id: str | None = None
    message: str
    data: dict[str, Any] = Field(default_factory=dict)


class RunTraceSnapshot(BaseModel):
    """Deterministic, replay-friendly projection of a mock run."""

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["0.1"] = TRACE_SCHEMA_VERSION
    team_id: str
    team_version: str
    workflow_id: str
    status: str
    input: dict[str, Any]
    agent_order: list[str]
    agent_steps: list[TraceAgentStep]
    event_sequence: list[TraceEventStep]
    final_output: str
    digest: str

    @classmethod
    def from_run_result(cls, run_result: RunResult) -> RunTraceSnapshot:
        """Create a deterministic snapshot from a run result."""

        agent_steps = [_agent_step(output) for output in run_result.agent_outputs]
        event_sequence = [
            TraceEventStep(
                type=event.type.value,
                agent_id=event.agent_id,
                message=event.message,
                data=event.data,
            )
            for event in run_result.events
        ]
        payload = {
            "schema_version": TRACE_SCHEMA_VERSION,
            "team_id": run_result.team_id,
            "team_version": run_result.team_version,
            "workflow_id": run_result.workflow_id,
            "status": run_result.status,
            "input": run_result.input,
            "agent_order": [step.agent_id for step in agent_steps],
            "agent_steps": [step.model_dump(mode="json") for step in agent_steps],
            "event_sequence": [step.model_dump(mode="json") for step in event_sequence],
            "final_output": run_result.final_output,
        }
        return cls(**payload, digest=_digest(payload))

    def comparable_payload(self) -> dict[str, Any]:
        """Return the snapshot payload without the digest field."""

        payload = self.model_dump(mode="json")
        payload.pop("digest", None)
        return payload


class TraceComparison(BaseModel):
    """Result of comparing two deterministic trace snapshots."""

    model_config = ConfigDict(extra="forbid")

    matches: bool
    expected_digest: str
    actual_digest: str
    differences: list[str] = Field(default_factory=list)


def build_trace_snapshot(run_result: RunResult) -> RunTraceSnapshot:
    """Convenience wrapper for creating a trace snapshot."""

    return RunTraceSnapshot.from_run_result(run_result)


def compare_trace_snapshots(
    expected: RunTraceSnapshot,
    actual: RunTraceSnapshot,
) -> TraceComparison:
    """Compare two snapshots and return a concise difference summary."""

    expected_payload = expected.comparable_payload()
    actual_payload = actual.comparable_payload()
    differences = _diff_payloads(expected_payload, actual_payload)
    return TraceComparison(
        matches=not differences,
        expected_digest=expected.digest,
        actual_digest=actual.digest,
        differences=differences,
    )


def _agent_step(output: AgentOutput) -> TraceAgentStep:
    return TraceAgentStep(
        agent_id=output.agent_id,
        role=output.role,
        goal=output.goal,
        summary=output.summary,
        prior_agent_outputs=output.prior_agent_outputs,
    )


def _digest(payload: dict[str, Any]) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _diff_payloads(expected: Any, actual: Any, *, path: str = "$") -> list[str]:
    if type(expected) is not type(actual):
        return [
            f"{path}: type differs expected "
            f"{type(expected).__name__}, got {type(actual).__name__}"
        ]

    if isinstance(expected, dict):
        differences: list[str] = []
        expected_keys = set(expected)
        actual_keys = set(actual)
        for key in sorted(expected_keys - actual_keys):
            differences.append(f"{path}.{key}: missing from actual")
        for key in sorted(actual_keys - expected_keys):
            differences.append(f"{path}.{key}: unexpected in actual")
        for key in sorted(expected_keys & actual_keys):
            differences.extend(_diff_payloads(expected[key], actual[key], path=f"{path}.{key}"))
        return differences

    if isinstance(expected, list):
        differences = []
        if len(expected) != len(actual):
            differences.append(
                f"{path}: length differs expected {len(expected)}, got {len(actual)}"
            )
        for index, (expected_item, actual_item) in enumerate(zip(expected, actual, strict=False)):
            differences.extend(_diff_payloads(expected_item, actual_item, path=f"{path}[{index}]"))
        return differences

    if expected != actual:
        return [f"{path}: expected {expected!r}, got {actual!r}"]
    return []
