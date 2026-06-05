from __future__ import annotations

import json

import pytest

from team_factory.llm import (
    LLMAdapterConfig,
    LLMProvider,
    LLMResponse,
    build_single_agent_smoke_prompt,
    find_agent,
    run_single_agent_llm_smoke,
    write_llm_smoke_result,
)
from team_factory.specs.loader import load_team_spec


class FakeSmokeAdapter:
    def __init__(self) -> None:
        self.requests = []

    def generate(self, request):
        self.requests.append(request)
        return LLMResponse(
            provider="openai_responses",
            model="gpt-test",
            text="Smoke result: simulation only, no tools used.",
            request_id="req_smoke",
            usage={"input_tokens": 10, "output_tokens": 5},
        )


def test_single_agent_smoke_prompt_contains_safety_rules() -> None:
    team = load_team_spec("team_specs/trading_strategy_research_team.yaml")
    agent = find_agent(team, "strategy_ideator")

    prompt = build_single_agent_smoke_prompt(
        team,
        agent,
        "Research ETF trend following for simulation only.",
    )

    assert "Do not call, request, or simulate use of tools" in prompt
    assert "Do not place trades" in prompt
    assert "Research and simulation only" in prompt
    assert "strategy_ideator" in prompt
    assert "Research ETF trend following" in prompt


def test_single_agent_smoke_result_writes_safe_artifact(tmp_path) -> None:
    team = load_team_spec("team_specs/trading_strategy_research_team.yaml")
    adapter = FakeSmokeAdapter()
    config = LLMAdapterConfig(
        provider=LLMProvider.DETERMINISTIC,
        model="gpt-test",
        reasoning_effort="medium",
    )

    result = run_single_agent_llm_smoke(
        team=team,
        agent_id="strategy_ideator",
        task="Research ETF trend following for simulation only.",
        adapter=adapter,
        config=config,
    )
    output_path = write_llm_smoke_result(result, tmp_path / "smoke.json")
    payload = json.loads(output_path.read_text())

    assert result.no_tools is True
    assert result.no_brokerage is True
    assert result.no_trading_execution is True
    assert result.request_id == "req_smoke"
    assert payload["safety_mode"] == "simulation_only_no_tools"
    assert payload["agent_id"] == "strategy_ideator"
    assert adapter.requests[0].metadata["no_tools"] is True


def test_single_agent_smoke_unknown_agent_fails() -> None:
    team = load_team_spec("team_specs/trading_strategy_research_team.yaml")

    with pytest.raises(ValueError, match="agent id not found"):
        find_agent(team, "missing_agent")
