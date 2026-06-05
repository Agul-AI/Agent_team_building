"""LLM adapter layer with deterministic default and strict real-provider opt-in."""

from team_factory.llm.adapters import (
    DeterministicLLMAdapter,
    LLMAdapter,
    LLMAdapterError,
    OpenAIResponsesLLMAdapter,
    build_llm_adapter,
)
from team_factory.llm.config import LLMAdapterConfig, LLMProvider
from team_factory.llm.models import LLMRequest, LLMResponse

__all__ = [
    "DeterministicLLMAdapter",
    "LLMAdapter",
    "LLMAdapterConfig",
    "LLMAdapterError",
    "LLMProvider",
    "LLMRequest",
    "LLMResponse",
    "OpenAIResponsesLLMAdapter",
    "build_llm_adapter",
]
