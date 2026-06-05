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
    LLMAdapterConfig,
    LLMProvider,
    default_llm_model,
)
from team_factory.llm.models import LLMRequest, LLMResponse

__all__ = [
    "DeterministicLLMAdapter",
    "DEFAULT_LLM_MODEL",
    "LLMAdapter",
    "LLMAdapterConfig",
    "LLMAdapterError",
    "LLMProvider",
    "LLMRequest",
    "LLMResponse",
    "OpenAIResponsesLLMAdapter",
    "build_llm_adapter",
    "default_llm_model",
]
