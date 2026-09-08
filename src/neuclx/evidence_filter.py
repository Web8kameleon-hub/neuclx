"""Evidence retrieval and ranking for stabilized reasoning."""

from __future__ import annotations

from dataclasses import asdict, is_dataclass
from typing import Any, Dict, List


class EvidenceFilter:
    """Filter and rank evidence for the current request."""

    def __init__(self, memory_manager):
        self.memory = memory_manager

    def retrieve_relevant(self, query: str, policy_mode: str = "balanced", top_k: int = 5) -> List[Dict[str, Any]]:
        raw = self._retrieve_raw(query, top_k=max(top_k * 2, top_k))
        allowed = {"verified", "measured", "computed"}
        if policy_mode == "strict":
            allowed = {"verified"}

        ranked: list[dict[str, Any]] = []
        for item in raw:
            record = self._to_dict(item)
            state = str(record.get("evidence_state") or record.get("state") or "unverified").casefold()
            if state not in allowed:
                continue
            content = str(record.get("content") or record.get("value") or "")
            if not content:
                continue
            record["_score"] = self._score(query, content, record)
            ranked.append(record)

        ranked.sort(key=lambda item: (item.get("_score", 0.0), item.get("confidence", 0.0), item.get("timestamp", 0)), reverse=True)
        return ranked[:top_k]

    def _retrieve_raw(self, query: str, top_k: int):
        if hasattr(self.memory, "search"):
            return self.memory.search(query, limit=top_k)
        if hasattr(self.memory, "retrieve_context"):
            return self.memory.retrieve_context(query, top_k=top_k)
        if hasattr(self.memory, "list_all"):
            return self.memory.list_all()[:top_k]
        return []

    def _to_dict(self, item: Any) -> dict[str, Any]:
        if isinstance(item, dict):
            return dict(item)
        if is_dataclass(item) and not isinstance(item, type):
            return asdict(item)
        if hasattr(item, "to_dict"):
            return dict(item.to_dict())
        if hasattr(item, "__dict__"):
            return dict(item.__dict__)
        return {"content": str(item)}

    def _score(self, query: str, content: str, record: dict[str, Any]) -> float:
        query_terms = {term for term in query.casefold().split() if len(term) > 2}
        content_terms = {term for term in content.casefold().split() if len(term) > 2}
        overlap = len(query_terms.intersection(content_terms))
        confidence = float(record.get("confidence", 0.0) or 0.0)
        timestamp = record.get("timestamp", 0)
        return overlap + confidence + (0.1 if timestamp else 0.0)


__all__ = ["EvidenceFilter"]