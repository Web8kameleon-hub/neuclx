"""Standardized request schema and context isolation for NeuCLX reasoning."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
import time
import uuid
from typing import Any, Optional


class PolicyMode(StrEnum):
    STRICT = "strict"
    BALANCED = "balanced"
    CREATIVE = "creative"


@dataclass(slots=True)
class ReasoningRequest:
    """Normalized reasoning request payload for a single task."""

    task: str
    facts: list[str] = field(default_factory=list)
    prior_context: str | None = None
    constraints: list[str] = field(default_factory=list)
    policy_mode: PolicyMode = PolicyMode.BALANCED
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.task = (self.task or "").strip()
        self.facts = [str(item).strip() for item in self.facts if str(item).strip()]
        self.constraints = [str(item).strip() for item in self.constraints if str(item).strip()]
        if self.prior_context is not None:
            self.prior_context = self.prior_context.strip()

    def to_prompt(self) -> str:
        lines: list[str] = [f"Task: {self.task}"]
        if self.facts:
            lines.append("Facts:")
            for fact in self.facts:
                lines.append(f"- {fact}")
        if self.prior_context:
            lines.append(f"Prior Context: {self.prior_context}")
        if self.constraints:
            lines.append("Constraints: " + ", ".join(self.constraints))
        lines.append(f"Policy Mode: {self.policy_mode.value}")
        return "\n".join(lines)


class ContextIsolator:
    """Keeps each reasoning request isolated from prior tasks."""

    def __init__(self) -> None:
        self._active_contexts: dict[str, dict[str, Any]] = {}

    def start_new_context(self, request_id: str) -> str:
        context_id = f"ctx_{request_id}_{uuid.uuid4().hex[:8]}"
        self._active_contexts[context_id] = {
            "created_at": time.time(),
            "steps": [],
            "evidence": [],
            "final_answer": None,
            "request_id": request_id,
        }
        return context_id

    def add_step(self, context_id: str, step: dict[str, Any]) -> None:
        ctx = self._active_contexts.get(context_id)
        if ctx is not None:
            ctx["steps"].append(step)

    def add_evidence(self, context_id: str, evidence: dict[str, Any]) -> None:
        ctx = self._active_contexts.get(context_id)
        if ctx is not None:
            ctx["evidence"].append(evidence)

    def finalize_context(self, context_id: str, answer: str) -> None:
        ctx = self._active_contexts.get(context_id)
        if ctx is not None:
            ctx["final_answer"] = answer

    def clear_context(self, context_id: str) -> None:
        self._active_contexts.pop(context_id, None)

    def get_context(self, context_id: str) -> Optional[dict[str, Any]]:
        return self._active_contexts.get(context_id)

    def get_current_context_summary(self, context_id: str) -> str:
        ctx = self.get_context(context_id)
        if ctx is None:
            return ""
        return f"Steps: {len(ctx.get('steps', []))}, Evidence: {len(ctx.get('evidence', []))}"


__all__ = ["ContextIsolator", "PolicyMode", "ReasoningRequest"]
