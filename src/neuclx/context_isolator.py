"""Per-request context isolation for stabilized reasoning."""

from __future__ import annotations

from dataclasses import dataclass, field
import time
import uuid
from typing import Any, Optional


@dataclass(slots=True)
class ContextRecord:
    created_at: float = field(default_factory=time.time)
    steps: list[dict[str, Any]] = field(default_factory=list)
    evidence: list[dict[str, Any]] = field(default_factory=list)
    final_answer: str | None = None
    active: bool = True
    request_id: str | None = None


class ContextIsolator:
    """Keeps each request isolated and auditable."""

    def __init__(self) -> None:
        self._contexts: dict[str, ContextRecord] = {}

    def start_new_context(self, request_id: str) -> str:
        context_id = f"ctx_{request_id}_{uuid.uuid4().hex[:8]}"
        self._contexts[context_id] = ContextRecord(request_id=request_id)
        return context_id

    def add_step(self, context_id: str, step: dict[str, Any]) -> None:
        ctx = self._contexts.get(context_id)
        if ctx and ctx.active:
            ctx.steps.append(step)

    def add_evidence(self, context_id: str, evidence: dict[str, Any]) -> None:
        ctx = self._contexts.get(context_id)
        if ctx and ctx.active:
            ctx.evidence.append(evidence)

    def set_final_answer(self, context_id: str, answer: str) -> None:
        ctx = self._contexts.get(context_id)
        if ctx and ctx.active:
            ctx.final_answer = answer

    def finalize_context(self, context_id: str, answer: str) -> None:
        self.set_final_answer(context_id, answer)

    def clear_context(self, context_id: str) -> None:
        ctx = self._contexts.get(context_id)
        if ctx:
            ctx.active = False

    def get_context(self, context_id: str) -> Optional[dict[str, Any]]:
        ctx = self._contexts.get(context_id)
        if ctx is None:
            return None
        return {
            "created_at": ctx.created_at,
            "steps": list(ctx.steps),
            "evidence": list(ctx.evidence),
            "final_answer": ctx.final_answer,
            "active": ctx.active,
            "request_id": ctx.request_id,
        }

    def get_current_summary(self, context_id: str) -> str:
        ctx = self.get_context(context_id)
        if not ctx or not ctx.get("active"):
            return ""
        return f"Steps: {len(ctx.get('steps', []))}, Evidence: {len(ctx.get('evidence', []))}"


__all__ = ["ContextIsolator", "ContextRecord"]