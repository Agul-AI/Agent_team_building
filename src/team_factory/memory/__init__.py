"""Local memory foundation for Phase 4.

Phase 4 provides standalone local persistence, retention, and redaction helpers.
It does not add vector memory, embeddings, or automatic agent-runtime memory use.
"""

from team_factory.memory.models import MemoryCategory, MemoryRecord
from team_factory.memory.redaction import RedactionReport, redact_data
from team_factory.memory.store import SQLiteMemoryStore

__all__ = [
    "MemoryCategory",
    "MemoryRecord",
    "RedactionReport",
    "SQLiteMemoryStore",
    "redact_data",
]
