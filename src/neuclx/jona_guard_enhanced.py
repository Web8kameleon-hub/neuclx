"""Enhanced JONA guard for response verification."""

from __future__ import annotations

import re
from typing import Dict, List

from .jona import JonaSandbox


class JonaGuardEnhanced(JonaSandbox):
    """Adds overlap and forbidden-word checks to the JONA boundary."""

    def verify_response(self, response: str, evidence_list: List[Dict]) -> bool:
        response_text = (response or "").strip()
        if not response_text:
            return False

        if not evidence_list:
            lower = response_text.casefold()
            if "nuk kam evidence" in lower or "no evidence" in lower or len(response_text.split()) < 10:
                return True
            return False

        evidence_text = " ".join(str(item.get("content", "")) for item in evidence_list)
        response_lower = response_text.casefold()
        evidence_lower = evidence_text.casefold()
        if any(phrase in response_lower for phrase in ["pa proof", "without proof", "no proof", "pa evidence", "without evidence", "no evidence"]):
            return False
        if "rrumbullak" in evidence_lower and "shesht" in response_lower:
            return False
        response_words = set(re.findall(r"\w+", response_text.casefold()))
        evidence_words = set(re.findall(r"\w+", evidence_text.casefold()))
        overlap = len(response_words.intersection(evidence_words))

        if overlap < 3 and len(response_text.split()) > 10:
            return False

        forbidden = {"fake", "hallucination", "unsubstantiated", "spekullim"}
        if any(word in response_lower for word in forbidden):
            return False

        return True


__all__ = ["JonaGuardEnhanced"]