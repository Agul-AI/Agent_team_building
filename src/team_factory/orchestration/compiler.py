"""Compile validated team specs into deterministic mock workflows."""

from __future__ import annotations

from team_factory.orchestration.runtime import CompiledWorkflow, WorkflowRunError
from team_factory.specs.models import AgentSpec, TeamSpec, WorkflowSpec, WorkflowType

SUPPORTED_MOCK_WORKFLOWS = {
    WorkflowType.SEQUENTIAL,
    WorkflowType.CRITIQUE_AND_REVISION,
    WorkflowType.SUPERVISOR_WORKER,
}


def compile_workflow(team: TeamSpec, workflow_id: str | None = None) -> CompiledWorkflow:
    """Compile one workflow from a validated team spec.

    The mock compiler supports deterministic execution for sequential,
    critique-and-revision, and supervisor-worker workflows. It still does not
    perform real LLM calls, tool calls, parallelism, or iterative improvement.
    """

    workflow = _select_workflow(team, workflow_id)
    if workflow.type not in SUPPORTED_MOCK_WORKFLOWS:
        msg = (
            f"workflow '{workflow.id}' has type '{workflow.type.value}', but the deterministic "
            "mock runtime supports only sequential, critique_and_revision, and "
            "supervisor_worker workflows"
        )
        raise WorkflowRunError(msg)

    agent_map = {agent.id: agent for agent in team.agents}
    ordered_agents = _ordered_agents(workflow, agent_map)
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


def _ordered_agents(
    workflow: WorkflowSpec,
    agent_map: dict[str, AgentSpec],
) -> tuple[AgentSpec, ...]:
    if workflow.type in {WorkflowType.SEQUENTIAL, WorkflowType.CRITIQUE_AND_REVISION}:
        agent_ids = workflow.steps
    elif workflow.type == WorkflowType.SUPERVISOR_WORKER:
        agent_ids = []
        if workflow.supervisor:
            agent_ids.append(workflow.supervisor)
        agent_ids.extend(workflow.workers)
        if workflow.final:
            agent_ids.append(workflow.final)
    else:  # pragma: no cover - guarded by compile_workflow before this helper runs
        raise WorkflowRunError(f"unsupported workflow type '{workflow.type.value}'")

    return tuple(agent_map[agent_id] for agent_id in agent_ids)


def ordered_agent_ids_for_workflow(team: TeamSpec, workflow_id: str | None = None) -> list[str]:
    """Return the deterministic mock execution order for a supported workflow."""

    return [agent.id for agent in compile_workflow(team, workflow_id).ordered_agents]
