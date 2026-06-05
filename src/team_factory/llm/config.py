"""Configuration for LLM adapters."""

from __future__ import annotations

import os
from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class LLMProvider(StrEnum):
    """Supported LLM adapter providers."""

    DETERMINISTIC = "deterministic"
    OPENAI_RESPONSES = "openai_responses"


LLMReasoningEffort = Literal["none", "minimal", "low", "medium", "high", "xhigh"]

DEFAULT_LLM_MODEL = "gpt-5.5-codex"
DEFAULT_LLM_REASONING_EFFORT: LLMReasoningEffort = "medium"


def default_llm_model() -> str:
    """Return the configured default LLM model id.

    The factory defaults to a Codex model identifier while keeping the provider
    deterministic unless real LLM usage is explicitly enabled.
    """

    return os.environ.get("TEAM_FACTORY_DEFAULT_LLM_MODEL", DEFAULT_LLM_MODEL)


def default_llm_reasoning_effort() -> str:
    """Return the configured default reasoning effort."""

    return os.environ.get(
        "TEAM_FACTORY_DEFAULT_LLM_REASONING_EFFORT",
        DEFAULT_LLM_REASONING_EFFORT,
    )


class LLMAdapterConfig(BaseModel):
    """Strict opt-in adapter config.

    Deterministic adapters are always allowed. Real provider adapters require both
    explicit config (`enable_real_llm=True`) and the environment variable
    `TEAM_FACTORY_ENABLE_REAL_LLM=1`.
    """

    model_config = ConfigDict(extra="forbid")

    provider: LLMProvider = LLMProvider.DETERMINISTIC
    model: str = Field(default_factory=default_llm_model)
    reasoning_effort: LLMReasoningEffort | None = Field(
        default_factory=default_llm_reasoning_effort,
        validate_default=True,
    )
    enable_real_llm: bool = False
    api_key_env: str = "OPENAI_API_KEY"
    base_url: str = "https://api.openai.com/v1"
    timeout_seconds: float = Field(default=30.0, gt=0)
    max_output_tokens: int | None = Field(default=512, gt=0)
    temperature: float | None = Field(default=0.2, ge=0.0, le=2.0)

    @model_validator(mode="after")
    def validate_real_provider_opt_in(self) -> LLMAdapterConfig:
        """Require explicit config/env opt-in for real providers."""

        if self.provider == LLMProvider.DETERMINISTIC:
            return self
        if not self.enable_real_llm:
            raise ValueError("real LLM providers require enable_real_llm=True")
        if os.environ.get("TEAM_FACTORY_ENABLE_REAL_LLM") != "1":
            raise ValueError("real LLM providers require TEAM_FACTORY_ENABLE_REAL_LLM=1")
        return self

    @property
    def api_key(self) -> str | None:
        """Read the configured API key from the environment."""

        return os.environ.get(self.api_key_env)
