"""LLM adapter layer with deterministic default and strict real-provider opt-in."""

from team_factory.llm.adapters import (
    DeterministicLLMAdapter,
    LLMAdapter,
    LLMAdapterError,
    OpenAIResponsesLLMAdapter,
    build_llm_adapter,
)
from team_factory.llm.config import (
    DEFAULT_LLM_MODEL,
    DEFAULT_LLM_REASONING_EFFORT,
    LLMAdapterConfig,
    LLMProvider,
    LLMReasoningEffort,
    default_llm_model,
    default_llm_reasoning_effort,
)
from team_factory.llm.models import LLMRequest, LLMResponse
from team_factory.llm.smoke import (
    LLMSmokeRunResult,
    build_single_agent_smoke_prompt,
    find_agent,
    run_single_agent_llm_smoke,
    write_llm_smoke_result,
)

__all__ = [
    "DeterministicLLMAdapter",
    "DEFAULT_LLM_MODEL",
    "DEFAULT_LLM_REASONING_EFFORT",
    "LLMAdapter",
    "LLMAdapterConfig",
    "LLMAdapterError",
    "LLMProvider",
    "LLMReasoningEffort",
    "LLMRequest",
    "LLMResponse",
    "LLMSmokeRunResult",
    "OpenAIResponsesLLMAdapter",
    "build_single_agent_smoke_prompt",
    "build_llm_adapter",
    "default_llm_model",
    "default_llm_reasoning_effort",
    "find_agent",
    "run_single_agent_llm_smoke",
    "write_llm_smoke_result",
]
