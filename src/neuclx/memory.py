"""Real memory layer for verified records and retrieval."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
import json
import sqlite3
from typing import List, Optional

from .bridge.source_manifest import EvidenceState


@dataclass(frozen=True)
class MemoryEntry:
    key: str
    content: str
    source_id: str
    evidence_state: str
    created_at: str

    def to_row(self):
        return (
            self.key,
            self.content,
            self.source_id,
            self.evidence_state,
            self.created_at,
        )


class EvidenceMemory:
    """Stores only verified and measurable records in SQLite."""

    def __init__(self, path: str = "data/neuclx_memory.sqlite3"):
        self.path = path
        self._connection = sqlite3.connect(self.path)
        self._initialize()

    def close(self):
        if getattr(self, "_connection", None) is not None:
            self._connection.close()
            self._connection = None

    def __del__(self):
        try:
            self.close()
        except Exception:
            pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        self.close()
        return False

    def _initialize(self):
        self._connection.execute(
            """
            CREATE TABLE IF NOT EXISTS memory_entries (
                key TEXT PRIMARY KEY,
                content TEXT NOT NULL,
                source_id TEXT NOT NULL,
                evidence_state TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        self._connection.commit()

    def _connect(self) -> sqlite3.Connection:
        if self._connection is None:
            self._connection = sqlite3.connect(self.path)
        return self._connection

    def _entry_from_datum(self, datum) -> MemoryEntry:
        if datum.state.value not in {"measured", "computed"}:
            raise ValueError("Only measured/computed data can be persisted to memory.")
        value = datum.value
        if value is None:
            content = ""
        elif isinstance(value, (dict, list, tuple, set)):
            content = json.dumps(value, ensure_ascii=False, sort_keys=True)
        else:
            content = str(value)
        payload = json.dumps({"value": value, "source": datum.source, "method": datum.method}, ensure_ascii=False, sort_keys=True)
        key = f"{datum.method or 'datum'}:{abs(hash(payload))}"
        created_at = datetime.now(UTC).isoformat()
        return MemoryEntry(
            key=key,
            content=content,
            source_id=datum.source or datum.method or "unknown",
            evidence_state=datum.state.value,
            created_at=created_at,
        )

    def _validate_entry(self, entry: MemoryEntry) -> None:
        if not entry.key or not entry.content or not entry.source_id:
            raise ValueError("Memory entry requires key, content, and source_id.")
        if entry.evidence_state not in {"measured", "computed"}:
            raise ValueError("Memory only accepts measured/computed evidence states.")

    def store(self, entry: MemoryEntry) -> MemoryEntry:
        self._validate_entry(entry)
        with self._connect() as connection:
            connection.execute(
                "INSERT OR REPLACE INTO memory_entries(key, content, source_id, evidence_state, created_at) VALUES(?,?,?,?,?)",
                entry.to_row(),
            )
        return entry

    def get(self, key: str) -> Optional[MemoryEntry]:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT key, content, source_id, evidence_state, created_at FROM memory_entries WHERE key=?",
                (key,),
            ).fetchone()
        if row is None:
            return None
        return MemoryEntry(*row)

    def search(self, query: str, limit: int = 20) -> List[MemoryEntry]:
        needle = f"%{query.lower()}%"
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT key, content, source_id, evidence_state, created_at FROM memory_entries WHERE lower(content) LIKE ? ORDER BY created_at DESC LIMIT ?",
                (needle, limit),
            ).fetchall()
        return [MemoryEntry(*row) for row in rows]

    def list_all(self) -> List[MemoryEntry]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT key, content, source_id, evidence_state, created_at FROM memory_entries ORDER BY created_at DESC"
            ).fetchall()
        return [MemoryEntry(*row) for row in rows]
