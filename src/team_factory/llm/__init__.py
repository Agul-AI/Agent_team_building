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
    "OpenAIResponsesLLMAdapter",
    "build_llm_adapter",
    "default_llm_model",
    "default_llm_reasoning_effort",
]
