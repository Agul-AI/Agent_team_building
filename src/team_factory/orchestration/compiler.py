"""Compile validated team specs into Phase 2 mock workflows."""

from __future__ import annotations

from team_factory.orchestration.runtime import CompiledWorkflow, WorkflowRunError
from team_factory.specs.models import AgentSpec, TeamSpec, WorkflowSpec, WorkflowType

SUPPORTED_PHASE2_WORKFLOWS = {WorkflowType.SEQUENTIAL}


def compile_workflow(team: TeamSpec, workflow_id: str | None = None) -> CompiledWorkflow:
    """Compile one workflow from a validated team spec.

    Phase 2 supports deterministic mock execution for sequential workflows only.
    Other workflow types are validated at the spec layer but intentionally rejected
    by this compiler until their runtime semantics are implemented.
    """

    workflow = _select_workflow(team, workflow_id)
    if workflow.type not in SUPPORTED_PHASE2_WORKFLOWS:
        msg = (
            f"workflow '{workflow.id}' has type '{workflow.type.value}', but Phase 2 only "
            "supports deterministic mock execution for sequential workflows"
        )
        raise WorkflowRunError(msg)

    agent_map = {agent.id: agent for agent in team.agents}
    ordered_agents = tuple(agent_map[agent_id] for agent_id in workflow.steps)
    return CompiledWorkflow(
        team=team,
        workflow=workflow,
        ordered_agents=ordered_agents,
        supported_mode=workflow.type,
    )


def _select_workflow(team: TeamSpec, workflow_id: str | None) -> WorkflowSpec:
    if workflow_id is None:
        if len(team.workflows) == 1:
            return team.workflows[0]
        msg = "workflow_id is required when a team declares multiple workflows"
        raise WorkflowRunError(msg)

    for workflow in team.workflows:
        if workflow.id == workflow_id:
            return workflow

    msg = f"team '{team.team_id}' does not define workflow '{workflow_id}'"
    raise WorkflowRunError(msg)


def ordered_agent_ids_for_workflow(team: TeamSpec, workflow_id: str | None = None) -> list[str]:
    """Return the Phase 2 execution order for a sequential workflow."""

    return [agent.id for agent in compile_workflow(team, workflow_id).ordered_agents]
