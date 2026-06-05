"""Pydantic models for versioned agent-team specifications.

Phase 1 intentionally models only the declarative spec layer. It does not execute
agents, compile workflows, call tools, or persist runtime state.
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, NonNegativeFloat, PositiveInt, model_validator

Identifier = str

SUPPORTED_SCHEMA_VERSION = "0.1"


class StrictBaseModel(BaseModel):
    """Base model with strict-ish defaults for readable spec validation."""

    model_config = ConfigDict(extra="forbid", validate_assignment=True)


class RiskLevel(str, Enum):
    """Risk level attached to a tool manifest."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class SideEffectLevel(str, Enum):
    """How much a tool can change the outside world."""

    NONE = "none"
    READ_ONLY = "read_only"
    LOCAL_WRITE = "local_write"
    EXTERNAL_WRITE = "external_write"
    HIGH_IMPACT = "high_impact"


class WorkflowType(str, Enum):
    """Workflow families supported by the team-factory spec layer."""

    SEQUENTIAL = "sequential"
    DEBATE = "debate"
    SUPERVISOR_WORKER = "supervisor_worker"
    CRITIQUE_AND_REVISION = "critique_and_revision"
    PARALLEL_RESEARCH = "parallel_research"
    CUSTOM = "custom"


class DeploymentMode(str, Enum):
    """Declarative deployment mode. Execution is future work."""

    LOCAL_CLI = "local_cli"
    LOCAL_API = "local_api"
    CLOUD_WORKER = "cloud_worker"
    MANUAL_ONLY = "manual_only"


class ModelProfile(StrictBaseModel):
    """Reusable model settings for agents."""

    provider: str = Field(..., min_length=1)
    model: str = Field(..., min_length=1)
    temperature: float = Field(default=0.2, ge=0.0, le=2.0)
    max_output_tokens: PositiveInt | None = None
    timeout_seconds: PositiveInt | None = None


class AgentSpec(StrictBaseModel):
    """Declarative specification for a single agent role."""

    id: Identifier = Field(..., pattern=r"^[a-z][a-z0-9_\-]*$")
    role: str = Field(..., min_length=1)
    goal: str = Field(..., min_length=1)
    instructions: str | None = None
    allowed_tools: list[Identifier] = Field(default_factory=list)
    memory_access: list[str] = Field(default_factory=list)
    model_profile: Identifier | None = None
    output_schema: str | dict[str, Any] | None = None
    constraints: list[str] = Field(default_factory=list)


class StoppingCriteria(StrictBaseModel):
    """Hard boundaries that prevent unbounded agent loops."""

    max_iterations: PositiveInt | None = None
    max_tool_calls: PositiveInt | None = None
    max_tokens: PositiveInt | None = None
    max_cost_usd: NonNegativeFloat | None = None
    max_wall_time_minutes: PositiveInt | None = None
    require_terminal_node: bool = True

    @model_validator(mode="after")
    def require_at_least_one_limit(self) -> StoppingCriteria:
        limits = [
            self.max_iterations,
            self.max_tool_calls,
            self.max_tokens,
            self.max_cost_usd,
            self.max_wall_time_minutes,
        ]
        if not any(value is not None for value in limits):
            msg = "stopping_criteria must include at least one hard limit"
            raise ValueError(msg)
        return self


class WorkflowEdge(StrictBaseModel):
    """Optional explicit graph edge for custom workflows."""

    source: Identifier
    target: Identifier
    condition: str | None = None


class WorkflowSpec(StrictBaseModel):
    """Declarative workflow connecting agents into an execution pattern."""

    id: Identifier = Field(..., pattern=r"^[a-z][a-z0-9_\-]*$")
    type: WorkflowType
    steps: list[Identifier] = Field(default_factory=list)
    supervisor: Identifier | None = None
    workers: list[Identifier] = Field(default_factory=list)
    final: Identifier | None = None
    nodes: list[Identifier] = Field(default_factory=list)
    edges: list[WorkflowEdge] = Field(default_factory=list)
    stopping_criteria: StoppingCriteria
    human_checkpoints: list[str] = Field(default_factory=list)
    retry_policy: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def require_shape_for_workflow_type(self) -> WorkflowSpec:
        if self.type in {
            WorkflowType.SEQUENTIAL,
            WorkflowType.DEBATE,
            WorkflowType.CRITIQUE_AND_REVISION,
            WorkflowType.PARALLEL_RESEARCH,
        } and not self.steps:
            msg = f"workflow '{self.id}' of type '{self.type.value}' requires non-empty steps"
            raise ValueError(msg)

        if self.type == WorkflowType.SUPERVISOR_WORKER:
            if not self.supervisor or not self.workers:
                msg = "supervisor_worker workflow requires supervisor and non-empty workers"
                raise ValueError(msg)

        if self.type == WorkflowType.CUSTOM and not (self.nodes and self.edges):
            msg = "custom workflow requires non-empty nodes and edges"
            raise ValueError(msg)

        return self

    def referenced_agents(self) -> set[Identifier]:
        """Return all agent ids referenced by this workflow."""

        ids: set[Identifier] = set(self.steps)
        ids.update(self.workers)
        ids.update(self.nodes)
        if self.supervisor:
            ids.add(self.supervisor)
        if self.final:
            ids.add(self.final)
        for edge in self.edges:
            ids.add(edge.source)
            ids.add(edge.target)
        return ids


class ToolSpec(StrictBaseModel):
    """Declarative tool manifest."""

    id: Identifier = Field(..., pattern=r"^[a-z][a-z0-9_\-]*$")
    provider: str | None = None
    description: str | None = None
    enabled: bool = True
    risk_level: RiskLevel = RiskLevel.LOW
    side_effect_level: SideEffectLevel = SideEffectLevel.NONE
    approval_required: bool = False
    permissions: list[str] = Field(default_factory=list)
    sandbox: str | None = None
    input_schema: dict[str, Any] | None = None
    output_schema: dict[str, Any] | None = None
    rate_limits: dict[str, Any] = Field(default_factory=dict)
    secrets_required: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def require_approval_for_critical_tools(self) -> ToolSpec:
        if self.enabled and self.risk_level == RiskLevel.CRITICAL and not self.approval_required:
            msg = f"critical tool '{self.id}' must set approval_required: true"
            raise ValueError(msg)
        if self.enabled and self.side_effect_level == SideEffectLevel.HIGH_IMPACT:
            if not self.approval_required:
                msg = f"high-impact tool '{self.id}' must set approval_required: true"
                raise ValueError(msg)
        return self


class MemoryStoreSpec(StrictBaseModel):
    """Configuration for one memory category."""

    enabled: bool = False
    store: str | None = None
    retention_days: PositiveInt | None = None
    notes: str | None = None


class MemorySpec(StrictBaseModel):
    """Memory categories available to the team."""

    short_term: MemoryStoreSpec = Field(default_factory=lambda: MemoryStoreSpec(enabled=True))
    project: MemoryStoreSpec = Field(default_factory=MemoryStoreSpec)
    long_term: MemoryStoreSpec = Field(default_factory=MemoryStoreSpec)
    user_preferences: MemoryStoreSpec = Field(default_factory=MemoryStoreSpec)
    domain_knowledge: MemoryStoreSpec = Field(default_factory=MemoryStoreSpec)
    avoid_storing: list[str] = Field(default_factory=list)


class EvaluationScenario(StrictBaseModel):
    """One scenario used by the future evaluation harness."""

    id: Identifier = Field(..., pattern=r"^[a-z][a-z0-9_\-]*$")
    input: str | dict[str, Any]
    expected_properties: list[str] = Field(default_factory=list)
    human_review_required: bool = False


class EvaluationSpec(StrictBaseModel):
    """Evaluation requirements bundled with each generated team."""

    metrics: list[str] = Field(default_factory=list)
    scenarios: list[EvaluationScenario] = Field(default_factory=list)
    regression_tests: list[str] = Field(default_factory=list)
    human_review_rubrics: list[str] = Field(default_factory=list)


class HumanReviewPolicy(StrictBaseModel):
    """Actions that must be paused for explicit human review."""

    required_before: list[str] = Field(default_factory=list)


class PrivacyPolicy(StrictBaseModel):
    """Data-handling preferences for a team."""

    avoid_storing: list[str] = Field(default_factory=list)
    retention_days: PositiveInt | None = None
    redact_logs: bool = True


class SafetyPolicy(StrictBaseModel):
    """Domain and cross-domain safety policy for a team."""

    domain_constraints: list[str] = Field(default_factory=list)
    prohibited_actions: list[str] = Field(default_factory=list)
    high_impact_actions: list[str] = Field(default_factory=list)
    human_review: HumanReviewPolicy = Field(default_factory=HumanReviewPolicy)
    privacy: PrivacyPolicy = Field(default_factory=PrivacyPolicy)

    @model_validator(mode="after")
    def require_review_for_high_impact_actions(self) -> SafetyPolicy:
        missing = set(self.high_impact_actions) - set(self.human_review.required_before)
        if missing:
            msg = (
                "high_impact_actions must also be listed in human_review.required_before: "
                + ", ".join(sorted(missing))
            )
            raise ValueError(msg)
        return self


class DeploymentSpec(StrictBaseModel):
    """Deployment intent. Runtime deployment is future work."""

    mode: DeploymentMode = DeploymentMode.LOCAL_CLI
    notes: str | None = None


class TeamSpec(StrictBaseModel):
    """Root model for a reusable, versioned agent-team specification."""

    schema_version: Literal["0.1"] = SUPPORTED_SCHEMA_VERSION
    team_id: Identifier = Field(..., pattern=r"^[a-z][a-z0-9_\-]*$")
    team_version: str = Field(..., pattern=r"^\d+\.\d+\.\d+[-+A-Za-z0-9.]*$")
    name: str = Field(..., min_length=1)
    domain: str = Field(..., min_length=1)
    purpose: str = Field(..., min_length=1)
    model_profiles: dict[Identifier, ModelProfile] = Field(default_factory=dict)
    agents: list[AgentSpec] = Field(..., min_length=1)
    workflows: list[WorkflowSpec] = Field(..., min_length=1)
    tools: list[ToolSpec] = Field(default_factory=list)
    memory: MemorySpec = Field(default_factory=MemorySpec)
    evaluation: EvaluationSpec = Field(default_factory=EvaluationSpec)
    safety: SafetyPolicy = Field(default_factory=SafetyPolicy)
    deployment: DeploymentSpec = Field(default_factory=DeploymentSpec)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_cross_references(self) -> TeamSpec:
        agent_ids = [agent.id for agent in self.agents]
        duplicate_agents = sorted({agent_id for agent_id in agent_ids if agent_ids.count(agent_id) > 1})
        if duplicate_agents:
            msg = "duplicate agent ids: " + ", ".join(duplicate_agents)
            raise ValueError(msg)

        tool_ids = [tool.id for tool in self.tools]
        duplicate_tools = sorted({tool_id for tool_id in tool_ids if tool_ids.count(tool_id) > 1})
        if duplicate_tools:
            msg = "duplicate tool ids: " + ", ".join(duplicate_tools)
            raise ValueError(msg)

        workflow_ids = [workflow.id for workflow in self.workflows]
        duplicate_workflows = sorted(
            {workflow_id for workflow_id in workflow_ids if workflow_ids.count(workflow_id) > 1}
        )
        if duplicate_workflows:
            msg = "duplicate workflow ids: " + ", ".join(duplicate_workflows)
            raise ValueError(msg)

        agent_id_set = set(agent_ids)
        for workflow in self.workflows:
            unknown_agents = sorted(workflow.referenced_agents() - agent_id_set)
            if unknown_agents:
                msg = (
                    f"workflow '{workflow.id}' references unknown agents: "
                    + ", ".join(unknown_agents)
                )
                raise ValueError(msg)

        tool_id_set = set(tool_ids)
        for agent in self.agents:
            unknown_tools = sorted(set(agent.allowed_tools) - tool_id_set)
            if unknown_tools:
                msg = (
                    f"agent '{agent.id}' references unknown tools: " + ", ".join(unknown_tools)
                )
                raise ValueError(msg)

            if agent.model_profile and agent.model_profile not in self.model_profiles:
                msg = f"agent '{agent.id}' references unknown model_profile '{agent.model_profile}'"
                raise ValueError(msg)

        return self
