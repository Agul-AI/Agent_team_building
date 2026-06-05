"""Structured JSONL observability, traces, and replay run logs."""

from team_factory.observability.golden import (
    DEFAULT_GOLDEN_SNAPSHOT_DIR,
    GoldenSnapshotResult,
    GoldenSnapshotStatus,
    check_golden_snapshots,
    update_golden_snapshots,
)
from team_factory.observability.logger import JsonlEventLogger
from team_factory.observability.models import (
    AuditEvent,
    AuditStatus,
    ObservabilityEvent,
    ObservabilityEventType,
    RunLogRecord,
)
from team_factory.observability.run_store import JsonlRunStore, PersistedRunRecord
from team_factory.observability.traces import (
    RunTraceSnapshot,
    TraceComparison,
    build_trace_snapshot,
    compare_trace_snapshots,
)

__all__ = [
    "AuditEvent",
    "DEFAULT_GOLDEN_SNAPSHOT_DIR",
    "GoldenSnapshotResult",
    "GoldenSnapshotStatus",
    "AuditStatus",
    "JsonlEventLogger",
    "JsonlRunStore",
    "ObservabilityEvent",
    "ObservabilityEventType",
    "PersistedRunRecord",
    "RunLogRecord",
    "RunTraceSnapshot",
    "TraceComparison",
    "build_trace_snapshot",
    "check_golden_snapshots",
    "compare_trace_snapshots",
    "update_golden_snapshots",
]
