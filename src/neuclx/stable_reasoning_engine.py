"""Stable reasoning engine that prioritizes deterministic logic and evidence."""

from __future__ import annotations

import hashlib
import json
import re
import time
from typing import Any, Dict, List, Optional

from .context_isolator import ContextIsolator
from .evidence_filter import EvidenceFilter
from .jona_guard_enhanced import JonaGuardEnhanced
from .memory import MemoryEntry
from .seed_loader import SeedLoader
from .simple_logic_engine import SimpleLogicEngine


class StableReasoningEngine:
    """Deterministic reasoning engine with strict evidence discipline."""

    def __init__(self, memory_manager, model_adapter=None, seed_path: str = "data/seed_facts.json"):
        self.memory = memory_manager
        self.model = model_adapter
        self.isolator = ContextIsolator()
        self.evidence_filter = EvidenceFilter(memory_manager)
        self.guard = JonaGuardEnhanced()
        self.traces: list[dict[str, Any]] = []
        self.seed_loader = SeedLoader(memory_manager, seed_path)
        self.seed_loader.load()

    def process(self, task: str, facts: Optional[List[str]] = None, policy_mode: str = "balanced") -> Dict[str, Any]:
        task_text = (task or "").strip()
        if not task_text:
            raise ValueError("task is required")

        request_id = f"stable_{int(time.time() * 1000)}_{hashlib.sha1(task_text.encode('utf-8')).hexdigest()[:8]}"
        context_id = self.isolator.start_new_context(request_id)
        input_facts = [str(item).strip() for item in (facts or []) if str(item).strip()]
        for fact in input_facts:
            self.isolator.add_evidence(context_id, {"content": fact, "evidence_state": "declared"})

        is_simple, simple_answer, simple_confidence = SimpleLogicEngine.detect_and_solve(task_text)
        if is_simple and simple_answer is not None:
            symbolic_step = {
                "id": f"step-{request_id}",
                "description": "Rule-based symbolic solving.",
                "reasoning_type": "symbolic",
                "prompt": task_text,
                "context": "\n".join(input_facts),
                "hypothesis": simple_answer,
                "confidence": simple_confidence,
                "status": "success",
                "evidence": input_facts[:],
                "operation": self._infer_operation(task_text),
                "result": simple_answer,
                "rule": self._infer_rule(task_text),
                "created_at": time.time(),
                "error": None,
            }
            self.isolator.add_step(context_id, symbolic_step)
            self.isolator.set_final_answer(context_id, simple_answer)
            self.isolator.clear_context(context_id)
            payload: dict[str, Any] = {
                "task": task_text,
                "intent": "arithmetic.word_problem" if symbolic_step["operation"] else "general",
                "conclusion": simple_answer,
                "confidence": simple_confidence,
                "confidence_breakdown": {
                    "parse": 1.0,
                    "calculation": 1.0,
                    "rule_match": 1.0,
                    "evidence_relevance": 1.0 if input_facts else 0.85,
                },
                "input_evidence": input_facts,
                "derived_facts": [simple_answer],
                "operations": [symbolic_step],
                "evidence_path": input_facts,
                "trace": {
                    "task_id": request_id,
                    "task": task_text,
                    "intent": "arithmetic.word_problem" if symbolic_step["operation"] else "general",
                    "steps": [symbolic_step],
                    "conclusion": simple_answer,
                    "confidence": simple_confidence,
                    "evidence_path": input_facts,
                    "created_at": time.time(),
                },
                "status": "ok",
                "task_id": request_id,
            }
            self._persist_trace(task_text, simple_answer, input_facts, payload)
            self.traces.append(payload)
            return payload

        evidence = self.evidence_filter.retrieve_relevant(task_text, policy_mode=policy_mode, top_k=5)
        for item in evidence:
            self.isolator.add_evidence(context_id, item)

        if policy_mode == "strict" and not evidence:
            self.isolator.clear_context(context_id)
            payload: dict[str, Any] = {
                "task": task_text,
                "conclusion": "Refuzuar: nuk ka evidence të verifikuar për këtë pyetje.",
                "confidence": 0.0,
                "input_evidence": input_facts,
                "derived_facts": [],
                "operations": [],
                "evidence_path": [],
                "trace": {"task_id": request_id, "task": task_text, "steps": [], "confidence": 0.0, "created_at": time.time()},
                "status": "rejected_no_evidence",
                "task_id": request_id,
            }
            self.traces.append(payload)
            return payload

        if evidence:
            response = self._synthesize_response(task_text, input_facts, evidence)
        else:
            response = "Refuzuar: nuk ka evidence të verifikuar për këtë pyetje."

        if not self.guard.verify_response(response, evidence):
            self.isolator.clear_context(context_id)
            payload: dict[str, Any] = {
                "task": task_text,
                "conclusion": "Përgjigja nuk kaloi verifikimin JONA. Refuzuar.",
                "confidence": 0.0,
                "input_evidence": input_facts,
                "derived_facts": [],
                "operations": [],
                "evidence_path": [self._content_of(item) for item in evidence],
                "trace": {"task_id": request_id, "task": task_text, "steps": [], "confidence": 0.0, "created_at": time.time()},
                "status": "rejected_jona",
                "task_id": request_id,
            }
            self.traces.append(payload)
            return payload

        confidence = self._estimate_confidence(response, evidence, input_facts)
        evidence_path = input_facts + [self._content_of(item) for item in evidence]
        step = {
            "id": f"step-{request_id}",
            "description": "Evidence-guided synthesis.",
            "reasoning_type": "inductive",
            "prompt": task_text,
            "context": "\n".join(evidence_path),
            "hypothesis": response,
            "confidence": confidence,
            "status": "success",
            "evidence": evidence_path[:],
            "operation": None,
            "result": response,
            "rule": "evidence_to_summary",
            "created_at": time.time(),
            "error": None,
        }
        self.isolator.add_step(context_id, step)
        self.isolator.set_final_answer(context_id, response)
        self.isolator.clear_context(context_id)

        payload: dict[str, Any] = {
            "task": task_text,
            "intent": self._classify_intent(task_text),
            "conclusion": response,
            "confidence": confidence,
            "confidence_breakdown": {
                "parse": 0.9,
                "calculation": 0.0,
                "rule_match": 0.85 if evidence else 0.0,
                "evidence_relevance": min(1.0, 0.5 + 0.1 * len(evidence)),
            },
            "input_evidence": input_facts,
            "derived_facts": [self._content_of(item) for item in evidence[:3]],
            "operations": [step],
            "evidence_path": evidence_path,
            "trace": {
                "task_id": request_id,
                "task": task_text,
                "intent": self._classify_intent(task_text),
                "steps": [step],
                "conclusion": response,
                "confidence": confidence,
                "evidence_path": evidence_path,
                "created_at": time.time(),
                "policy_mode": policy_mode,
            },
            "status": "ok",
            "task_id": request_id,
        }
        self._persist_trace(task_text, response, evidence_path, payload)
        self.traces.append(payload)
        return payload

    def get_clean_reasoning_score(self) -> Dict[str, Any]:
        total = len(self.traces)
        if total == 0:
            return {"score": 0.0, "details": "No traces yet."}

        success = sum(1 for trace in self.traces if trace.get("status") == "ok")
        avg_conf = sum(float(trace.get("confidence", 0.0) or 0.0) for trace in self.traces) / total
        evidence_used = sum(1 for trace in self.traces if trace.get("evidence_path"))
        policy_respected = sum(1 for trace in self.traces if "rejected" not in str(trace.get("status", "")))

        score = (
            0.25 * (success / total)
            + 0.25 * avg_conf
            + 0.25 * (evidence_used / total)
            + 0.25 * (policy_respected / total)
        )
        return {
            "clean_reasoning_score": round(score, 3),
            "total_requests": total,
            "success_rate": success / total,
            "average_confidence": avg_conf,
            "evidence_usage_rate": evidence_used / total,
            "policy_respect_rate": policy_respected / total,
        }

    def _classify_intent(self, task: str) -> str:
        lowered = task.casefold()
        if any(token in lowered for token in ["pse", "si", "çfarë", "kush", "kur", "how", "what"]):
            return "exploratory"
        if any(token in lowered for token in ["analiz", "vlerëso", "krahaso", "kategorizo"]):
            return "analytical"
        return "general"

    def _synthesize_response(self, task: str, facts: List[str], evidence: List[Dict[str, Any]]) -> str:
        combined = " ".join([task, *facts, *(self._content_of(item) for item in evidence)])
        lowered = combined.casefold()
        for item in evidence:
            content = self._content_of(item)
            content_lower = content.casefold()
            if "jona" in lowered and ("jona" in content_lower or "policy" in content_lower or "guardrail" in content_lower):
                return content
            if any(token in content_lower for token in ["provenance", "memory", "evidence", "seed"]):
                return content
        if evidence:
            return self._content_of(evidence[0])
        return "Refuzuar: nuk ka evidence të verifikuar për këtë pyetje."

    def _estimate_confidence(self, response: str, evidence: List[Dict[str, Any]], facts: List[str]) -> float:
        score = 0.5
        if evidence:
            score += min(len(evidence) / 5, 0.2)
        if len(response.split()) < 5:
            score -= 0.2
        uncertain = ["ndoshta", "mbase", "sipas meje", "nuk jam i sigurt"]
        if any(word in response.casefold() for word in uncertain):
            score -= 0.2
        if facts:
            score += 0.1
        return max(0.0, min(1.0, score))

    def _infer_operation(self, task: str) -> str | None:
        lowered = task.casefold()
        if any(token in lowered for token in ["student", "book", "libra", "libër"]):
            numbers = re.findall(r"\d+", task)
            if len(numbers) >= 2:
                return f"{numbers[0]} × {numbers[1]}"
        return None

    def _infer_rule(self, task: str) -> str | None:
        lowered = task.casefold()
        if any(token in lowered for token in ["student", "book", "libra", "libër"]):
            return "transfer_preserves_total"
        return None

    def _persist_trace(self, task: str, conclusion: str, evidence: List[str], payload: Dict[str, Any]) -> None:
        if not hasattr(self.memory, "store"):
            return
        serialized = json.dumps({"task": task, "conclusion": conclusion, "evidence": evidence[:5]}, ensure_ascii=False, sort_keys=True)
        digest = hashlib.sha256(serialized.encode("utf-8")).hexdigest()[:16]
        entry = MemoryEntry(
            key=f"stable:{digest}",
            content=serialized,
            source_id="stable_reasoning_engine",
            evidence_state="computed",
            created_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        )
        try:
            self.memory.store(entry)
        except Exception:
            pass

    def _content_of(self, item: Any) -> str:
        if isinstance(item, dict):
            return str(item.get("content") or item.get("value") or item.get("text") or "")
        return str(getattr(item, "content", item) or "")


__all__ = ["StableReasoningEngine"]