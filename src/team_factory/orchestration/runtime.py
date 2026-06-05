"""Deterministic Phase 2 mock workflow runtime.

The runtime executes declared agent order using static, deterministic mock agent
outputs. It is useful for testing spec compilation, event logging shape, and
basic workflow boundaries before any real LLM/tool orchestration exists.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field

from team_factory.orchestration.events import EventType, RunEvent
from team_factory.specs.models import AgentSpec, TeamSpec, WorkflowSpec, WorkflowType


class WorkflowRunError(RuntimeError):
    """Raised when a workflow cannot be run by the Phase 2 mock runtime."""


class AgentOutput(BaseModel):
    """Deterministic mock output from one agent step."""

    model_config = ConfigDict(extra="forbid")

    agent_id: str
    role: str
    goal: str
    summary: str
    inputs_seen: dict[str, Any] = Field(default_factory=dict)
    prior_agent_outputs: list[str] = Field(default_factory=list)


class RunResult(BaseModel):
    """Result of a deterministic mock workflow run."""

    model_config = ConfigDict(extra="forbid")

    run_id: str
    team_id: str
    team_version: str
    workflow_id: str
    status: str
    input: dict[str, Any]
    agent_outputs: list[AgentOutput]
    final_output: str
    events: list[RunEvent]


@dataclass(frozen=True)
class CompiledWorkflow:
    """Executable wrapper around a validated team/workflow pair."""

    team: TeamSpec
    workflow: WorkflowSpec
    ordered_agents: tuple[AgentSpec, ...]
    supported_mode: WorkflowType

    def run(
        self,
        user_input: str | Mapping[str, Any],
        *,
        runtime: MockAgentRuntime | None = None,
    ) -> RunResult:
        """Run this workflow with the deterministic mock runtime."""

        selected_runtime = runtime or MockAgentRuntime()
        return selected_runtime.run(self, user_input)


@dataclass
class MockAgentRuntime:
    """Deterministic runtime that simulates agent handoffs.

    No LLMs, tools, files, networks, or databases are called. Each agent receives
    the original run input and the ids of prior agents, then emits a predictable
    summary. This makes tests stable and keeps Phase 2 narrowly scoped.
    """

    emit_events: bool = True
    _events: list[RunEvent] = field(default_factory=list, init=False)

    def run(self, workflow: CompiledWorkflow, user_input: str | Mapping[str, Any]) -> RunResult:
        """Run a compiled workflow and return a structured result."""

        normalized_input = self._normalize_input(user_input)
        run_id = str(uuid4())
        self._events = []
        self._emit(
            run_id=run_id,
            workflow_id=workflow.workflow.id,
            event_type=EventType.RUN_STARTED,
            message="Mock workflow run started.",
            data={
                "team_id": workflow.team.team_id,
                "team_version": workflow.team.team_version,
                "workflow_type": workflow.workflow.type.value,
                "agent_count": len(workflow.ordered_agents),
            },
        )

        outputs: list[AgentOutput] = []
        try:
            for index, agent in enumerate(workflow.ordered_agents, start=1):
                self._emit(
                    run_id=run_id,
                    workflow_id=workflow.workflow.id,
                    event_type=EventType.AGENT_STARTED,
                    agent_id=agent.id,
                    message=f"Mock agent '{agent.id}' started.",
                    data={"step_index": index, "role": agent.role},
                )
                output = self._run_agent(agent, normalized_input, outputs)
                outputs.append(output)
                self._emit(
                    run_id=run_id,
                    workflow_id=workflow.workflow.id,
                    event_type=EventType.AGENT_COMPLETED,
                    agent_id=agent.id,
                    message=f"Mock agent '{agent.id}' completed.",
                    data={"step_index": index, "summary": output.summary},
                )
        except Exception as exc:
            self._emit(
                run_id=run_id,
                workflow_id=workflow.workflow.id,
                event_type=EventType.RUN_FAILED,
                message="Mock workflow run failed.",
                data={"error": str(exc)},
            )
            raise

        final_output = self._build_final_output(workflow, outputs)
        self._emit(
            run_id=run_id,
            workflow_id=workflow.workflow.id,
            event_type=EventType.RUN_COMPLETED,
            message="Mock workflow run completed.",
            data={"final_output": final_output},
        )

        return RunResult(
            run_id=run_id,
            team_id=workflow.team.team_id,
            team_version=workflow.team.team_version,
            workflow_id=workflow.workflow.id,
            status="completed",
            input=normalized_input,
            agent_outputs=outputs,
            final_output=final_output,
            events=list(self._events),
        )

    def _normalize_input(self, user_input: str | Mapping[str, Any]) -> dict[str, Any]:
        if isinstance(user_input, str):
            return {"task": user_input}
        return dict(user_input)

    def _run_agent(
        self,
        agent: AgentSpec,
        normalized_input: dict[str, Any],
        prior_outputs: list[AgentOutput],
    ) -> AgentOutput:
        prior_agent_ids = [output.agent_id for output in prior_outputs]
        task = str(normalized_input.get("task", normalized_input))
        summary = (
            f"{agent.id} ({agent.role}) mock-processed task '{task}' "
            f"after {len(prior_agent_ids)} prior step(s)."
        )
        return AgentOutput(
            agent_id=agent.id,
            role=agent.role,
            goal=agent.goal,
            summary=summary,
            inputs_seen=normalized_input,
            prior_agent_outputs=prior_agent_ids,
        )

    def _build_final_output(self, workflow: CompiledWorkflow, outputs: list[AgentOutput]) -> str:
        if not outputs:
            raise WorkflowRunError("workflow produced no agent outputs")
        final_agent = outputs[-1]
        return (
            f"Mock run for team '{workflow.team.team_id}' workflow "
            f"'{workflow.workflow.id}' completed with final agent "
            f"'{final_agent.agent_id}'."
        )

    def _emit(
        self,
        *,
        run_id: str,
        workflow_id: str,
        event_type: EventType,
        message: str,
        agent_id: str | None = None,
        data: dict[str, Any] | None = None,
    ) -> None:
        if not self.emit_events:
            return
        self._events.append(
            RunEvent(
                run_id=run_id,
                type=event_type,
                workflow_id=workflow_id,
                agent_id=agent_id,
                message=message,
                data=data or {},
            )
        )
