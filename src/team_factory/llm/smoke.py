"""Guarded single-agent LLM smoke workflow.

This module intentionally does not implement orchestration or tool execution. It
builds one prompt for one selected agent and sends it through an explicitly
provided LLM adapter. The CLI command that uses it requires real-provider opt-in
and explicit acknowledgements before any network call can happen.
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field

from team_factory.llm.adapters import LLMAdapter
from team_factory.llm.config import LLMAdapterConfig
from team_factory.llm.models import LLMRequest
from team_factory.specs.models import AgentSpec, TeamSpec


class LLMSmokeRunResult(BaseModel):
    """Safe artifact from a guarded single-agent LLM smoke run."""

    model_config = ConfigDict(extra="forbid")

    run_id: str = Field(default_factory=lambda: str(uuid4()))
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    team_id: str
    team_version: str
    agent_id: str
    agent_role: str
    task: str
    provider: str
    model: str
    reasoning_effort: str | None
    safety_mode: str = "simulation_only_no_tools"
    no_tools: bool = True
    no_brokerage: bool = True
    no_trading_execution: bool = True
    prompt: str
    output_text: str
    request_id: str | None = None
    usage: dict[str, Any] | None = None


def find_agent(team: TeamSpec, agent_id: str) -> AgentSpec:
    """Find one agent by id."""

    for agent in team.agents:
        if agent.id == agent_id:
            return agent
    raise ValueError(f"agent id not found in team spec: {agent_id}")


def build_single_agent_smoke_prompt(team: TeamSpec, agent: AgentSpec, task: str) -> str:
    """Build the guarded single-agent smoke-test prompt."""

    safety_constraints = "\n".join(f"- {item}" for item in team.safety.domain_constraints)
    prohibited_actions = "\n".join(f"- {item}" for item in team.safety.prohibited_actions)
    return (
        "You are running a guarded single-agent LLM smoke test for an agent-team factory.\n"
        "This is a smoke test only, not full orchestration.\n\n"
        f"Team: {team.team_id} v{team.team_version}\n"
        f"Team purpose: {team.purpose}\n"
        f"Agent id: {agent.id}\n"
        f"Agent role: {agent.role}\n"
        f"Agent goal: {agent.goal}\n\n"
        "Hard safety rules for this smoke test:\n"
        "- Do not call, request, or simulate use of tools.\n"
        "- Do not place trades, recommend live trades, or connect brokerage accounts.\n"
        "- Treat all trading-related content as research/simulation only.\n"
        "- Do not ask for secrets, account numbers, API keys, or brokerage credentials.\n"
        "- Return a concise process-oriented research note with assumptions and caveats.\n\n"
        f"Team domain constraints:\n{safety_constraints or '- none declared'}\n\n"
        f"Team prohibited actions:\n{prohibited_actions or '- none declared'}\n\n"
        f"User task:\n{task}\n"
    )


def run_single_agent_llm_smoke(
    *,
    team: TeamSpec,
    agent_id: str,
    task: str,
    adapter: LLMAdapter,
    config: LLMAdapterConfig,
) -> LLMSmokeRunResult:
    """Run one guarded LLM call for one selected agent."""

    agent = find_agent(team, agent_id)
    prompt = build_single_agent_smoke_prompt(team, agent, task)
    response = adapter.generate(
        LLMRequest(
            prompt=prompt,
            instructions=(
                "Follow the smoke-test safety rules exactly. Do not use tools. "
                "Do not provide live trading advice."
            ),
            metadata={
                "source": "llm_smoke",
                "team_id": team.team_id,
                "agent_id": agent.id,
                "no_tools": True,
            },
        )
    )
    return LLMSmokeRunResult(
        team_id=team.team_id,
        team_version=team.team_version,
        agent_id=agent.id,
        agent_role=agent.role,
        task=task,
        provider=response.provider,
        model=response.model,
        reasoning_effort=config.reasoning_effort,
        prompt=prompt,
        output_text=response.text,
        request_id=response.request_id,
        usage=response.usage,
    )


def write_llm_smoke_result(result: LLMSmokeRunResult, output_path: str | Path) -> Path:
    """Write a smoke result JSON artifact."""

    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(result.model_dump_json(indent=2), encoding="utf-8")
    return path
