"""Local CLI flows for Phase 7.

The CLI is intentionally lightweight and argparse-based so it works without
installing extra packages. It exposes local developer workflows over the Phase
1-6 foundations: specs, mock orchestration, tool authorization, memory, and mock
evaluations.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from team_factory.evaluation import EvaluationHarness, write_markdown_report
from team_factory.memory import MemoryCategory, SQLiteMemoryStore
from team_factory.orchestration.compiler import compile_workflow, ordered_agent_ids_for_workflow
from team_factory.orchestration.runtime import WorkflowRunError
from team_factory.specs.loader import TeamSpecLoadError, load_team_spec
from team_factory.tools import ToolCallRequest, ToolRegistry

DEFAULT_EVAL_OUTPUT_DIR = Path("examples/artifacts/evaluation_reports")


def build_parser() -> argparse.ArgumentParser:
    """Build the root CLI parser."""

    parser = argparse.ArgumentParser(
        prog="team-factory",
        description="Local CLI for Agent Team Factory specs, mock runs, tools, memory, and evals.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    validate_parser = subparsers.add_parser("validate", help="Validate one or more team specs.")
    validate_parser.add_argument("specs", nargs="+", help="Spec YAML files to validate.")
    validate_parser.set_defaults(func=_cmd_validate)

    order_parser = subparsers.add_parser(
        "workflow-order",
        help="Print deterministic mock execution order for a workflow.",
    )
    order_parser.add_argument("spec", help="Spec YAML file.")
    order_parser.add_argument(
        "--workflow-id",
        help="Workflow id. Optional for single-workflow teams.",
    )
    order_parser.add_argument("--json", action="store_true", help="Emit JSON output.")
    order_parser.set_defaults(func=_cmd_workflow_order)

    run_parser = subparsers.add_parser(
        "run-mock",
        help="Run a supported deterministic mock workflow.",
    )
    run_parser.add_argument("spec", help="Spec YAML file.")
    run_parser.add_argument("task", nargs="?", default="Run deterministic mock task.")
    run_parser.add_argument(
        "--workflow-id",
        help="Workflow id. Optional for single-workflow teams.",
    )
    run_parser.add_argument("--json", action="store_true", help="Emit full JSON RunResult.")
    run_parser.set_defaults(func=_cmd_run_mock)

    tool_parser = subparsers.add_parser(
        "tool-check",
        help="Authorize a proposed tool call without executing it.",
    )
    tool_parser.add_argument("spec", help="Spec YAML file.")
    tool_parser.add_argument("--agent-id", required=True, help="Agent requesting the tool.")
    tool_parser.add_argument("--tool-id", required=True, help="Tool being requested.")
    tool_parser.add_argument("--purpose", required=True, help="Purpose of the proposed call.")
    tool_parser.add_argument(
        "--permission",
        action="append",
        default=[],
        help="Granted permission; may be repeated.",
    )
    tool_parser.add_argument("--approved", action="store_true", help="Mark request human-approved.")
    tool_parser.add_argument("--approval-id", help="Traceable approval id when approved.")
    tool_parser.add_argument("--json", action="store_true", help="Emit JSON output.")
    tool_parser.set_defaults(func=_cmd_tool_check)

    memory_put_parser = subparsers.add_parser("memory-put", help="Put a local memory record.")
    _add_memory_db_arg(memory_put_parser)
    memory_put_parser.add_argument(
        "--category",
        required=True,
        choices=[item.value for item in MemoryCategory],
    )
    memory_put_parser.add_argument("--key", required=True)
    memory_put_parser.add_argument(
        "--value-json",
        required=True,
        help="JSON object value to store.",
    )
    memory_put_parser.add_argument("--metadata-json", default="{}", help="JSON object metadata.")
    memory_put_parser.add_argument("--retention-days", type=int)
    memory_put_parser.add_argument(
        "--no-redact",
        action="store_true",
        help="Disable redaction before storing.",
    )
    memory_put_parser.add_argument("--json", action="store_true", help="Emit JSON output.")
    memory_put_parser.set_defaults(func=_cmd_memory_put)

    memory_get_parser = subparsers.add_parser("memory-get", help="Get a local memory record.")
    _add_memory_db_arg(memory_get_parser)
    memory_get_parser.add_argument(
        "--category",
        required=True,
        choices=[item.value for item in MemoryCategory],
    )
    memory_get_parser.add_argument("--key", required=True)
    memory_get_parser.add_argument("--include-expired", action="store_true")
    memory_get_parser.add_argument("--json", action="store_true", help="Emit JSON output.")
    memory_get_parser.set_defaults(func=_cmd_memory_get)

    memory_list_parser = subparsers.add_parser("memory-list", help="List local memory records.")
    _add_memory_db_arg(memory_list_parser)
    memory_list_parser.add_argument("--category", choices=[item.value for item in MemoryCategory])
    memory_list_parser.add_argument("--include-expired", action="store_true")
    memory_list_parser.add_argument("--json", action="store_true", help="Emit JSON output.")
    memory_list_parser.set_defaults(func=_cmd_memory_list)

    memory_delete_parser = subparsers.add_parser(
        "memory-delete",
        help="Delete a local memory record.",
    )
    _add_memory_db_arg(memory_delete_parser)
    memory_delete_parser.add_argument(
        "--category",
        required=True,
        choices=[item.value for item in MemoryCategory],
    )
    memory_delete_parser.add_argument("--key", required=True)
    memory_delete_parser.set_defaults(func=_cmd_memory_delete)

    eval_parser = subparsers.add_parser("eval", help="Run deterministic mock evaluations.")
    eval_parser.add_argument("specs", nargs="+", help="Spec YAML files to evaluate.")
    eval_parser.add_argument(
        "--out-dir",
        default=str(DEFAULT_EVAL_OUTPUT_DIR),
        help="Directory for Markdown evaluation reports.",
    )
    eval_parser.add_argument("--json", action="store_true", help="Emit JSON summary.")
    eval_parser.set_defaults(func=_cmd_eval)

    return parser


def main(argv: list[str] | None = None) -> int:
    """CLI entry point."""

    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return int(args.func(args))
    except (TeamSpecLoadError, WorkflowRunError, ValidationError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


def _add_memory_db_arg(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--db", default="local_memory.sqlite3", help="SQLite memory DB path.")


def _cmd_validate(args: argparse.Namespace) -> int:
    exit_code = 0
    for spec_path in args.specs:
        try:
            spec = load_team_spec(spec_path)
        except TeamSpecLoadError as exc:
            exit_code = 1
            print(f"FAIL {spec_path}: {exc}", file=sys.stderr)
        else:
            print(f"OK   {spec_path}: {spec.team_id} v{spec.team_version}")
    return exit_code


def _cmd_workflow_order(args: argparse.Namespace) -> int:
    spec = load_team_spec(args.spec)
    order = ordered_agent_ids_for_workflow(spec, args.workflow_id)
    payload = {
        "team_id": spec.team_id,
        "workflow_id": args.workflow_id or spec.workflows[0].id,
        "agent_order": order,
    }
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(f"{payload['team_id']}:{payload['workflow_id']} -> " + " -> ".join(order))
    return 0


def _cmd_run_mock(args: argparse.Namespace) -> int:
    spec = load_team_spec(args.spec)
    workflow = compile_workflow(spec, args.workflow_id)
    result = workflow.run(args.task)
    if args.json:
        print(result.model_dump_json(indent=2))
    else:
        print(result.final_output)
        print("Agent outputs:")
        for output in result.agent_outputs:
            print(f"- {output.agent_id}: {output.summary}")
    return 0


def _cmd_tool_check(args: argparse.Namespace) -> int:
    spec = load_team_spec(args.spec)
    registry = ToolRegistry.from_team_spec(spec)
    request = ToolCallRequest(
        tool_id=args.tool_id,
        agent_id=args.agent_id,
        purpose=args.purpose,
        requested_permissions=frozenset(args.permission),
        approved_by_human=args.approved,
        approval_id=args.approval_id,
    )
    decision = registry.authorize(request)
    if args.json:
        print(decision.model_dump_json(indent=2))
    else:
        print(f"{decision.status.value}: {decision.reason}")
        if decision.required_permissions:
            print("required_permissions: " + ", ".join(sorted(decision.required_permissions)))
        if decision.missing_permissions:
            print("missing_permissions: " + ", ".join(sorted(decision.missing_permissions)))
        if decision.approval_required:
            print("approval_required: true")
    return 0 if decision.allowed else 2


def _cmd_memory_put(args: argparse.Namespace) -> int:
    value = _parse_json_object(args.value_json, "value-json")
    metadata = _parse_json_object(args.metadata_json, "metadata-json")
    with SQLiteMemoryStore(args.db) as store:
        record = store.put(
            category=args.category,
            key=args.key,
            value=value,
            metadata=metadata,
            retention_days=args.retention_days,
            redact=not args.no_redact,
        )
    if args.json:
        print(record.model_dump_json(indent=2))
    else:
        redacted = str(record.redacted).lower()
        print(f"stored {record.category.value}:{record.key} redacted={redacted}")
    return 0


def _cmd_memory_get(args: argparse.Namespace) -> int:
    with SQLiteMemoryStore(args.db) as store:
        record = store.get(args.category, args.key, include_expired=args.include_expired)
    if record is None:
        print(f"not found: {args.category}:{args.key}", file=sys.stderr)
        return 2
    if args.json:
        print(record.model_dump_json(indent=2))
    else:
        print(f"{record.category.value}:{record.key} {json.dumps(record.value, sort_keys=True)}")
    return 0


def _cmd_memory_list(args: argparse.Namespace) -> int:
    with SQLiteMemoryStore(args.db) as store:
        records = store.list_records(category=args.category, include_expired=args.include_expired)
    if args.json:
        print(json.dumps([json.loads(record.model_dump_json()) for record in records], indent=2))
    else:
        for record in records:
            print(f"{record.category.value}:{record.key}")
    return 0


def _cmd_memory_delete(args: argparse.Namespace) -> int:
    with SQLiteMemoryStore(args.db) as store:
        deleted = store.delete(args.category, args.key)
    if deleted:
        print(f"deleted {args.category}:{args.key}")
        return 0
    print(f"not found: {args.category}:{args.key}", file=sys.stderr)
    return 2


def _cmd_eval(args: argparse.Namespace) -> int:
    out_dir = Path(args.out_dir)
    harness = EvaluationHarness()
    summaries: list[dict[str, Any]] = []
    exit_code = 0
    for spec_path in args.specs:
        try:
            spec = load_team_spec(spec_path)
        except TeamSpecLoadError as exc:
            exit_code = 1
            print(f"FAIL {spec_path}: {exc}", file=sys.stderr)
            continue
        report = harness.run_team(spec)
        output_path = write_markdown_report(report, out_dir / f"{spec.team_id}.md")
        summary = {
            "spec": spec_path,
            "team_id": spec.team_id,
            "status": report.status.value,
            "output_path": str(output_path),
            "passed": report.summary.passed,
            "failed": report.summary.failed,
            "skipped": report.summary.skipped,
        }
        summaries.append(summary)
        if not args.json:
            print(f"{report.status.value.upper():7} {spec_path}: wrote {output_path}")
    if args.json:
        print(json.dumps(summaries, indent=2, sort_keys=True))
    return exit_code


def _parse_json_object(raw: str, label: str) -> dict[str, Any]:
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError(f"{label} must be valid JSON: {exc}") from exc
    if not isinstance(parsed, dict):
        raise ValueError(f"{label} must be a JSON object")
    return parsed
