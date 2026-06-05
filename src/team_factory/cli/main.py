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
from team_factory.llm import (
    LLMAdapterConfig,
    LLMAdapterError,
    LLMProvider,
    LLMRequest,
    build_llm_adapter,
    default_llm_model,
    default_llm_reasoning_effort,
    run_single_agent_llm_smoke,
    write_llm_smoke_result,
)
from team_factory.memory import MemoryCategory, SQLiteMemoryStore
from team_factory.observability import (
    DEFAULT_GOLDEN_SNAPSHOT_DIR,
    GoldenSnapshotResult,
    JsonlRunStore,
    RunTraceSnapshot,
    build_trace_snapshot,
    check_golden_snapshots,
    compare_trace_snapshots,
    update_golden_snapshots,
)
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
    run_parser.add_argument("--run-log", help="Append full run plus trace snapshot to JSONL.")
    run_parser.add_argument("--snapshot-out", help="Write deterministic trace snapshot JSON.")
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


    llm_parser = subparsers.add_parser(
        "llm-generate",
        help="Generate text with deterministic adapter or explicit opt-in real LLM adapter.",
    )
    llm_parser.add_argument("prompt", help="Prompt text.")
    llm_parser.add_argument("--instructions", help="Optional instructions/developer message.")
    llm_parser.add_argument(
        "--provider",
        choices=[item.value for item in LLMProvider],
        default=LLMProvider.DETERMINISTIC.value,
        help="LLM provider. Real providers require explicit opt-in.",
    )
    llm_parser.add_argument(
        "--model",
        default=default_llm_model(),
        help="Model id. Defaults to TEAM_FACTORY_DEFAULT_LLM_MODEL or the Codex model default.",
    )
    llm_parser.add_argument(
        "--enable-real-llm",
        action="store_true",
        help="Required config opt-in for real providers; env gate is also required.",
    )
    llm_parser.add_argument("--api-key-env", default="OPENAI_API_KEY")
    llm_parser.add_argument("--base-url", default="https://api.openai.com/v1")
    llm_parser.add_argument("--timeout-seconds", type=float, default=30.0)
    llm_parser.add_argument("--max-output-tokens", type=int, default=512)
    llm_parser.add_argument("--temperature", type=float, default=0.2)
    llm_parser.add_argument(
        "--reasoning-effort",
        choices=["none", "minimal", "low", "medium", "high", "xhigh"],
        default=default_llm_reasoning_effort(),
        help=(
            "Reasoning effort for real providers. Defaults to "
            "TEAM_FACTORY_DEFAULT_LLM_REASONING_EFFORT or medium."
        ),
    )
    llm_parser.add_argument("--json", action="store_true", help="Emit JSON response.")
    llm_parser.set_defaults(func=_cmd_llm_generate)

    llm_smoke_parser = subparsers.add_parser(
        "run-llm-smoke",
        help=(
            "Run a guarded real-LLM single-agent smoke workflow. Strict opt-in only; "
            "no tools, trading, or brokerage execution."
        ),
    )
    llm_smoke_parser.add_argument("spec", help="Spec YAML file.")
    llm_smoke_parser.add_argument("task", help="Smoke-test task.")
    llm_smoke_parser.add_argument("--agent-id", required=True, help="Single agent to smoke test.")
    llm_smoke_parser.add_argument(
        "--provider",
        choices=[LLMProvider.OPENAI_RESPONSES.value],
        required=True,
        help="Real LLM provider. Deterministic provider is intentionally not allowed here.",
    )
    llm_smoke_parser.add_argument("--model", default=default_llm_model())
    llm_smoke_parser.add_argument(
        "--enable-real-llm",
        action="store_true",
        help="Required config opt-in. TEAM_FACTORY_ENABLE_REAL_LLM=1 is also required.",
    )
    llm_smoke_parser.add_argument(
        "--acknowledge-no-tools",
        action="store_true",
        help="Required acknowledgement that this smoke test cannot call tools.",
    )
    llm_smoke_parser.add_argument(
        "--acknowledge-simulation-only",
        action="store_true",
        help="Required acknowledgement that trading work is research/simulation only.",
    )
    llm_smoke_parser.add_argument("--api-key-env", default="OPENAI_API_KEY")
    llm_smoke_parser.add_argument("--base-url", default="https://api.openai.com/v1")
    llm_smoke_parser.add_argument("--timeout-seconds", type=float, default=30.0)
    llm_smoke_parser.add_argument("--max-output-tokens", type=int, default=512)
    llm_smoke_parser.add_argument("--temperature", type=float, default=0.2)
    llm_smoke_parser.add_argument(
        "--reasoning-effort",
        choices=["none", "minimal", "low", "medium", "high", "xhigh"],
        default=default_llm_reasoning_effort(),
    )
    llm_smoke_parser.add_argument("--out", help="Write safe smoke-result JSON artifact.")
    llm_smoke_parser.add_argument("--json", action="store_true", help="Emit JSON result.")
    llm_smoke_parser.set_defaults(func=_cmd_run_llm_smoke)

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


    trace_parser = subparsers.add_parser(
        "trace-snapshot",
        help="Run a mock workflow and write a deterministic trace snapshot.",
    )
    trace_parser.add_argument("spec", help="Spec YAML file.")
    trace_parser.add_argument("task", nargs="?", default="Run deterministic mock task.")
    trace_parser.add_argument(
        "--workflow-id",
        help="Workflow id. Optional for single-workflow teams.",
    )
    trace_parser.add_argument("--out", required=True, help="Snapshot JSON output path.")
    trace_parser.set_defaults(func=_cmd_trace_snapshot)

    trace_compare_parser = subparsers.add_parser(
        "trace-compare",
        help="Compare two deterministic trace snapshots.",
    )
    trace_compare_parser.add_argument("expected", help="Expected snapshot JSON path.")
    trace_compare_parser.add_argument("actual", help="Actual snapshot JSON path.")
    trace_compare_parser.add_argument("--json", action="store_true", help="Emit JSON output.")
    trace_compare_parser.set_defaults(func=_cmd_trace_compare)


    golden_check_parser = subparsers.add_parser(
        "golden-check",
        help="Compare current mock traces against checked-in golden snapshots.",
    )
    golden_check_parser.add_argument("specs", nargs="+", help="Spec YAML files to check.")
    golden_check_parser.add_argument(
        "--snapshot-dir",
        default=str(DEFAULT_GOLDEN_SNAPSHOT_DIR),
        help="Golden snapshot directory.",
    )
    golden_check_parser.add_argument("--json", action="store_true", help="Emit JSON output.")
    golden_check_parser.set_defaults(func=_cmd_golden_check)

    golden_update_parser = subparsers.add_parser(
        "golden-update",
        help="Update checked-in golden snapshots with explicit approval.",
    )
    golden_update_parser.add_argument("specs", nargs="+", help="Spec YAML files to update.")
    golden_update_parser.add_argument(
        "--snapshot-dir",
        default=str(DEFAULT_GOLDEN_SNAPSHOT_DIR),
        help="Golden snapshot directory.",
    )
    golden_update_parser.add_argument(
        "--approve",
        action="store_true",
        help="Required explicit approval to write/update golden snapshots.",
    )
    golden_update_parser.add_argument("--json", action="store_true", help="Emit JSON output.")
    golden_update_parser.set_defaults(func=_cmd_golden_update)

    run_log_list_parser = subparsers.add_parser("run-log-list", help="List persisted run records.")
    run_log_list_parser.add_argument("--run-log", required=True, help="Run-log JSONL path.")
    run_log_list_parser.add_argument("--json", action="store_true", help="Emit JSON output.")
    run_log_list_parser.set_defaults(func=_cmd_run_log_list)

    run_log_get_parser = subparsers.add_parser("run-log-get", help="Get a persisted run record.")
    run_log_get_parser.add_argument("--run-log", required=True, help="Run-log JSONL path.")
    run_log_get_parser.add_argument("--run-id", required=True, help="Run id to retrieve.")
    run_log_get_parser.add_argument("--json", action="store_true", help="Emit full JSON record.")
    run_log_get_parser.set_defaults(func=_cmd_run_log_get)

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
    except (
        TeamSpecLoadError,
        WorkflowRunError,
        ValidationError,
        ValueError,
        LLMAdapterError,
    ) as exc:
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
    if args.run_log:
        record = JsonlRunStore(args.run_log).append(
            result,
            metadata={"source": "cli.run-mock", "spec": args.spec},
        )
        if not args.json:
            print(f"persisted run {record.run_id} to {args.run_log}")
    if args.snapshot_out:
        snapshot = build_trace_snapshot(result)
        _write_snapshot(snapshot, args.snapshot_out)
        if not args.json:
            print(f"wrote trace snapshot {args.snapshot_out}")
    if args.json:
        print(result.model_dump_json(indent=2))
    else:
        print(result.final_output)
        print("Agent outputs:")
        for output in result.agent_outputs:
            print(f"- {output.agent_id}: {output.summary}")
    return 0


def _cmd_trace_snapshot(args: argparse.Namespace) -> int:
    spec = load_team_spec(args.spec)
    workflow = compile_workflow(spec, args.workflow_id)
    result = workflow.run(args.task)
    snapshot = build_trace_snapshot(result)
    _write_snapshot(snapshot, args.out)
    print(f"wrote trace snapshot {args.out} digest={snapshot.digest}")
    return 0


def _cmd_trace_compare(args: argparse.Namespace) -> int:
    expected = _read_snapshot(args.expected)
    actual = _read_snapshot(args.actual)
    comparison = compare_trace_snapshots(expected, actual)
    if args.json:
        print(comparison.model_dump_json(indent=2))
    else:
        status = "MATCH" if comparison.matches else "DIFF"
        print(f"{status} expected={comparison.expected_digest} actual={comparison.actual_digest}")
        for difference in comparison.differences:
            print(f"- {difference}")
    return 0 if comparison.matches else 2


def _cmd_golden_check(args: argparse.Namespace) -> int:
    results: list[GoldenSnapshotResult] = []
    for spec_path in args.specs:
        spec = load_team_spec(spec_path)
        results.extend(check_golden_snapshots(spec, snapshot_dir=args.snapshot_dir))
    return _print_golden_results(results, emit_json=args.json)


def _cmd_golden_update(args: argparse.Namespace) -> int:
    if not args.approve:
        raise ValueError("golden-update requires --approve to intentionally update snapshots")
    results: list[GoldenSnapshotResult] = []
    for spec_path in args.specs:
        spec = load_team_spec(spec_path)
        results.extend(update_golden_snapshots(spec, snapshot_dir=args.snapshot_dir))
    return _print_golden_results(results, emit_json=args.json)


def _cmd_run_log_list(args: argparse.Namespace) -> int:
    records = JsonlRunStore(args.run_log).list_records()
    if args.json:
        print(json.dumps([_run_log_summary(record) for record in records], indent=2))
    else:
        for record in records:
            print(
                f"{record.run_id} {record.run_result.team_id} "
                f"{record.run_result.workflow_id} {record.run_result.status} "
                f"digest={record.trace_snapshot.digest}"
            )
    return 0


def _cmd_run_log_get(args: argparse.Namespace) -> int:
    record = JsonlRunStore(args.run_log).get(args.run_id)
    if record is None:
        print(f"run id not found: {args.run_id}", file=sys.stderr)
        return 2
    if args.json:
        print(record.model_dump_json(indent=2))
    else:
        print(
            f"{record.run_id} {record.run_result.team_id} "
            f"{record.run_result.workflow_id} {record.run_result.status} "
            f"digest={record.trace_snapshot.digest}"
        )
        print(record.run_result.final_output)
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


def _cmd_llm_generate(args: argparse.Namespace) -> int:
    config = LLMAdapterConfig(
        provider=LLMProvider(args.provider),
        model=args.model,
        enable_real_llm=args.enable_real_llm,
        api_key_env=args.api_key_env,
        base_url=args.base_url,
        timeout_seconds=args.timeout_seconds,
        max_output_tokens=args.max_output_tokens,
        temperature=args.temperature,
        reasoning_effort=args.reasoning_effort,
    )
    adapter = build_llm_adapter(config)
    response = adapter.generate(
        LLMRequest(prompt=args.prompt, instructions=args.instructions, metadata={"source": "cli"})
    )
    if args.json:
        print(response.model_dump_json(indent=2))
    else:
        print(response.text)
    return 0


def _cmd_run_llm_smoke(args: argparse.Namespace) -> int:
    if not args.acknowledge_no_tools:
        raise ValueError("run-llm-smoke requires --acknowledge-no-tools")
    if not args.acknowledge_simulation_only:
        raise ValueError("run-llm-smoke requires --acknowledge-simulation-only")

    spec = load_team_spec(args.spec)
    config = LLMAdapterConfig(
        provider=LLMProvider(args.provider),
        model=args.model,
        enable_real_llm=args.enable_real_llm,
        api_key_env=args.api_key_env,
        base_url=args.base_url,
        timeout_seconds=args.timeout_seconds,
        max_output_tokens=args.max_output_tokens,
        temperature=args.temperature,
        reasoning_effort=args.reasoning_effort,
    )
    adapter = build_llm_adapter(config)
    result = run_single_agent_llm_smoke(
        team=spec,
        agent_id=args.agent_id,
        task=args.task,
        adapter=adapter,
        config=config,
    )
    if args.out:
        output_path = write_llm_smoke_result(result, args.out)
        if not args.json:
            print(f"wrote guarded LLM smoke result {output_path}")
    if args.json:
        print(result.model_dump_json(indent=2))
    else:
        print(result.output_text)
    return 0


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


def _print_golden_results(results: list[GoldenSnapshotResult], *, emit_json: bool) -> int:
    if emit_json:
        print(json.dumps([result.model_dump(mode="json") for result in results], indent=2))
    else:
        for result in results:
            digest = result.actual_digest or result.expected_digest or "no-digest"
            print(
                f"{result.status.value.upper():7} {result.team_id} "
                f"{result.workflow_id}/{result.scenario_id} digest={digest} "
                f"path={result.snapshot_path}"
            )
            if result.error:
                print(f"  error: {result.error}")
            for difference in result.differences[:5]:
                print(f"  - {difference}")
    return 0 if all(result.ok for result in results) else 2


def _write_snapshot(snapshot: RunTraceSnapshot, path: str | Path) -> Path:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(snapshot.model_dump_json(indent=2), encoding="utf-8")
    return output_path


def _read_snapshot(path: str | Path) -> RunTraceSnapshot:
    return RunTraceSnapshot.model_validate_json(Path(path).read_text(encoding="utf-8"))


def _run_log_summary(record) -> dict[str, Any]:
    return {
        "run_id": record.run_id,
        "team_id": record.run_result.team_id,
        "workflow_id": record.run_result.workflow_id,
        "status": record.run_result.status,
        "digest": record.trace_snapshot.digest,
        "recorded_at": record.recorded_at.isoformat(),
    }


def _parse_json_object(raw: str, label: str) -> dict[str, Any]:
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError(f"{label} must be valid JSON: {exc}") from exc
    if not isinstance(parsed, dict):
        raise ValueError(f"{label} must be a JSON object")
    return parsed
