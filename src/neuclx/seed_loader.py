"""Seed loader for base facts used by stabilized reasoning."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any

from .memory import MemoryEntry


class SeedLoader:
    """Load seed facts into any supported memory backend."""

    def __init__(self, memory_manager, seed_path: str = "data/seed_facts.json"):
        self.memory = memory_manager
        self.seed_path = seed_path

    def load(self, overwrite: bool = False) -> int:
        path = Path(self.seed_path)
        if not path.exists():
            return 0

        with path.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)

        existing_subjects = self._existing_subjects()
        count = 0
        for item in payload:
            subject = str(item.get("subject", "")).strip()
            if not subject:
                continue
            if not overwrite and subject.casefold() in existing_subjects:
                continue
            relation = str(item.get("relation", "is")).strip() or "is"
            object_value = str(item.get("object", "")).strip()
            confidence = float(item.get("confidence", 1.0))
            source = str(item.get("source", "seed")).strip() or "seed"
            self._store_fact(subject, relation, object_value, source, confidence)
            existing_subjects.add(subject.casefold())
            count += 1
        return count

    def _existing_subjects(self) -> set[str]:
        subjects: set[str] = set()
        semantic = getattr(self.memory, "semantic", None)
        if semantic is not None and hasattr(semantic, "get_all"):
            for item in semantic.get_all():
                subject = self._extract_subject(item)
                if subject:
                    subjects.add(subject.casefold())
        elif hasattr(self.memory, "list_all"):
            for item in self.memory.list_all():
                content = getattr(item, "content", "") or ""
                if content:
                    subjects.add(content.split(maxsplit=1)[0].casefold())
        return subjects

    def _extract_subject(self, item: Any) -> str:
        if isinstance(item, dict):
            return str(item.get("subject", "")).strip()
        return str(getattr(item, "subject", "")).strip()

    def _store_fact(self, subject: str, relation: str, object_value: str, source: str, confidence: float) -> None:
        if hasattr(self.memory, "add_fact"):
            self.memory.add_fact(
                subject=subject,
                relation=relation,
                object=object_value,
                source_id=source,
                confidence=confidence,
            )
            return

        if hasattr(self.memory, "store"):
            content = f"{subject} {relation} {object_value}".strip()
            digest = hashlib.sha256(f"{subject}|{relation}|{object_value}".encode("utf-8")).hexdigest()[:16]
            entry = MemoryEntry(
                key=f"seed:{digest}",
                content=content,
                source_id=source,
                evidence_state="computed",
                created_at="1970-01-01T00:00:00Z",
            )
            self.memory.store(entry)


__all__ = ["SeedLoader"]