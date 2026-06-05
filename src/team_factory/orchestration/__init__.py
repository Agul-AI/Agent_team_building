"""Deterministic mock orchestration for Phase 2.

This package intentionally does not call LLMs, tools, or external services. It
provides a minimal, inspectable runtime for validating that team specs can be
compiled into bounded workflow runs.
"""

from team_factory.orchestration.compiler import compile_workflow
from team_factory.orchestration.runtime import MockAgentRuntime, RunResult, WorkflowRunError

__all__ = ["MockAgentRuntime", "RunResult", "WorkflowRunError", "compile_workflow"]
