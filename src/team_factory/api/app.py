"""Dependency-light local API skeleton for Phase 8.

This module uses Python's standard-library HTTP server instead of a production
web framework. It is intended for local development and testable API-shape work,
not internet-facing deployment.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import urlparse
from uuid import uuid4

from pydantic import BaseModel, ConfigDict

from team_factory.evaluation import EvaluationHarness, write_markdown_report
from team_factory.observability import AuditStatus, JsonlEventLogger
from team_factory.orchestration.compiler import compile_workflow, ordered_agent_ids_for_workflow
from team_factory.specs.loader import load_team_spec
from team_factory.specs.models import TeamSpec
from team_factory.tools import ToolCallRequest, ToolRegistry

DEFAULT_EVAL_OUTPUT_DIR = Path("examples/artifacts/evaluation_reports")


class LocalAPIResponse(BaseModel):
    """Structured response returned by the local API dispatcher."""

    model_config = ConfigDict(extra="forbid")

    status_code: int
    body: dict[str, Any]


@dataclass
class TeamFactoryAPI:
    """Small local API dispatcher for team-factory operations."""

    spec_root: Path = Path(".")
    audit_log_path: Path | None = None
    eval_output_dir: Path = Path("examples/artifacts/evaluation_reports")

    def __post_init__(self) -> None:
        self.spec_root = Path(self.spec_root)
        self.eval_output_dir = Path(self.eval_output_dir)
        self._logger = JsonlEventLogger(self.audit_log_path) if self.audit_log_path else None

    def handle(
        self,
        method: str,
        path: str,
        body: dict[str, Any] | None = None,
    ) -> LocalAPIResponse:
        """Handle one local API request and return a structured response."""

        correlation_id = str(uuid4())
        route = urlparse(path).path.rstrip("/") or "/"
        normalized_method = method.upper()
        body = body or {}
        self._log_audit(
            action=f"{normalized_method} {route}",
            status=AuditStatus.SUCCEEDED,
            details={"stage": "received"},
            correlation_id=correlation_id,
        )
        try:
            response = self._dispatch(normalized_method, route, body, correlation_id)
        except Exception as exc:  # local API skeleton returns JSON errors rather than raising
            self._log_audit(
                action=f"{normalized_method} {route}",
                status=AuditStatus.FAILED,
                details={"error": str(exc)},
                correlation_id=correlation_id,
            )
            return LocalAPIResponse(
                status_code=400,
                body={"ok": False, "error": str(exc), "correlation_id": correlation_id},
            )

        self._log_audit(
            action=f"{normalized_method} {route}",
            status=AuditStatus.SUCCEEDED,
            details={"stage": "completed", "status_code": response.status_code},
            correlation_id=correlation_id,
        )
        response.body.setdefault("correlation_id", correlation_id)
        return response

    def _dispatch(
        self,
        method: str,
        route: str,
        body: dict[str, Any],
        correlation_id: str,
    ) -> LocalAPIResponse:
        if method == "GET" and route == "/health":
            return LocalAPIResponse(status_code=200, body={"ok": True, "status": "healthy"})
        if method == "POST" and route == "/specs/validate":
            return self._validate_spec(body)
        if method == "POST" and route == "/workflows/order":
            return self._workflow_order(body)
        if method == "POST" and route == "/runs/mock":
            return self._run_mock(body, correlation_id)
        if method == "POST" and route == "/tools/check":
            return self._tool_check(body)
        if method == "POST" and route == "/eval/mock":
            return self._eval_mock(body)
        return LocalAPIResponse(
            status_code=404,
            body={"ok": False, "error": f"unknown route: {method} {route}"},
        )

    def _validate_spec(self, body: dict[str, Any]) -> LocalAPIResponse:
        spec = self._load_spec_from_body(body)
        return LocalAPIResponse(
            status_code=200,
            body={
                "ok": True,
                "team_id": spec.team_id,
                "team_version": spec.team_version,
                "agent_count": len(spec.agents),
                "workflow_ids": [workflow.id for workflow in spec.workflows],
                "tool_ids": [tool.id for tool in spec.tools],
            },
        )

    def _workflow_order(self, body: dict[str, Any]) -> LocalAPIResponse:
        spec = self._load_spec_from_body(body)
        workflow_id = body.get("workflow_id")
        order = ordered_agent_ids_for_workflow(spec, workflow_id)
        return LocalAPIResponse(
            status_code=200,
            body={
                "ok": True,
                "team_id": spec.team_id,
                "workflow_id": workflow_id or spec.workflows[0].id,
                "agent_order": order,
            },
        )

    def _run_mock(self, body: dict[str, Any], correlation_id: str) -> LocalAPIResponse:
        spec = self._load_spec_from_body(body)
        workflow = compile_workflow(spec, body.get("workflow_id"))
        task = str(body.get("task", "Run deterministic mock task."))
        result = workflow.run(task)
        if self._logger:
            self._logger.append_run_result(result, correlation_id=correlation_id)
        return LocalAPIResponse(
            status_code=200,
            body={"ok": True, "run_result": result.model_dump(mode="json")},
        )

    def _tool_check(self, body: dict[str, Any]) -> LocalAPIResponse:
        spec = self._load_spec_from_body(body)
        request = ToolCallRequest(
            tool_id=str(body["tool_id"]),
            agent_id=str(body["agent_id"]),
            purpose=str(body["purpose"]),
            requested_permissions=frozenset(body.get("permissions", [])),
            approved_by_human=bool(body.get("approved", False)),
            approval_id=body.get("approval_id"),
        )
        decision = ToolRegistry.from_team_spec(spec).authorize(request)
        status_code = 200 if decision.allowed else 403
        return LocalAPIResponse(
            status_code=status_code,
            body={"ok": decision.allowed, "decision": decision.model_dump(mode="json")},
        )

    def _eval_mock(self, body: dict[str, Any]) -> LocalAPIResponse:
        spec = self._load_spec_from_body(body)
        report = EvaluationHarness().run_team(spec, workflow_id=body.get("workflow_id"))
        output_dir = Path(body.get("out_dir", self.eval_output_dir))
        output_path = write_markdown_report(report, output_dir / f"{spec.team_id}.md")
        return LocalAPIResponse(
            status_code=200,
            body={
                "ok": True,
                "report": report.model_dump(mode="json"),
                "output_path": str(output_path),
            },
        )

    def _load_spec_from_body(self, body: dict[str, Any]) -> TeamSpec:
        spec_path = body.get("spec_path")
        if not spec_path:
            raise ValueError("request body must include spec_path")
        path = Path(str(spec_path))
        if not path.is_absolute():
            path = self.spec_root / path
        return load_team_spec(path)

    def _log_audit(
        self,
        *,
        action: str,
        status: AuditStatus,
        details: dict[str, Any] | None = None,
        correlation_id: str | None = None,
    ) -> None:
        if self._logger is None:
            return
        self._logger.append_audit(
            action=action,
            status=status,
            details=details or {},
            correlation_id=correlation_id,
        )


def make_handler(api: TeamFactoryAPI) -> type[BaseHTTPRequestHandler]:
    """Create an HTTP request handler bound to a TeamFactoryAPI instance."""

    class TeamFactoryRequestHandler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:  # noqa: N802 - stdlib method name
            self._handle_request({})

        def do_POST(self) -> None:  # noqa: N802 - stdlib method name
            content_length = int(self.headers.get("Content-Length", "0"))
            raw = self.rfile.read(content_length).decode("utf-8") if content_length else "{}"
            try:
                body = json.loads(raw) if raw else {}
            except json.JSONDecodeError as exc:
                response = LocalAPIResponse(
                    status_code=400,
                    body={"ok": False, "error": f"invalid JSON body: {exc}"},
                )
                self._write_response(response)
                return
            if not isinstance(body, dict):
                response = LocalAPIResponse(
                    status_code=400,
                    body={"ok": False, "error": "JSON body must be an object"},
                )
                self._write_response(response)
                return
            self._handle_request(body)

        def log_message(self, format: str, *args: object) -> None:  # noqa: A002
            return

        def _handle_request(self, body: dict[str, Any]) -> None:
            response = api.handle(self.command, self.path, body)
            self._write_response(response)

        def _write_response(self, response: LocalAPIResponse) -> None:
            payload = json.dumps(response.body, sort_keys=True).encode("utf-8")
            self.send_response(response.status_code)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)

    return TeamFactoryRequestHandler


def serve(
    *,
    host: str = "127.0.0.1",
    port: int = 8765,
    spec_root: str | Path = ".",
    audit_log_path: str | Path | None = "examples/artifacts/api_audit.jsonl",
    eval_output_dir: str | Path = DEFAULT_EVAL_OUTPUT_DIR,
) -> None:
    """Serve the local API skeleton until interrupted."""

    api = TeamFactoryAPI(
        spec_root=Path(spec_root),
        audit_log_path=Path(audit_log_path) if audit_log_path else None,
        eval_output_dir=Path(eval_output_dir),
    )
    server = ThreadingHTTPServer((host, port), make_handler(api))
    print(f"Serving local Team Factory API on http://{host}:{port}")
    print("This is a local development skeleton, not a production server.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping local Team Factory API.")
    finally:
        server.server_close()

