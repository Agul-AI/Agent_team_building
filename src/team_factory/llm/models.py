"""LLM request/response models."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class LLMRequest(BaseModel):
    """A provider-neutral text generation request.

    Tool execution is intentionally not represented here. Real providers must be
    called without tools in this phase.
    """

    model_config = ConfigDict(extra="forbid")

    prompt: str = Field(..., min_length=1)
    instructions: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class LLMResponse(BaseModel):
    """Provider-neutral text generation response."""

    model_config = ConfigDict(extra="forbid")

    provider: str
    model: str
    text: str
    raw_response: dict[str, Any] = Field(default_factory=dict)
    request_id: str | None = None
    usage: dict[str, Any] | None = None
