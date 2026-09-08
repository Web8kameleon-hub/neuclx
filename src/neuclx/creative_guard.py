"""Prompt and output checks for creative generation."""

from __future__ import annotations

import re
from pathlib import Path
from typing import ClassVar

from .nsfw_detector import NSFWDetector


class JonaCreativeGuard:
    forbidden_terms: ClassVar[set[str]] = {
        "violence",
        "gore",
        "explicit",
        "hate",
        "self-harm",
        "porn",
        "nsfw",
    }

    def __init__(self):
        self.detector = NSFWDetector()

    def check_prompt(self, prompt: str) -> bool:
        lowered = (prompt or "").casefold()
        if not lowered.strip():
            return False
        if self.detector.check_text(lowered) > 0.5:
            return False
        return not any(term in lowered for term in self.forbidden_terms)

    def check_output_svg(self, svg_text: str, prompt: str) -> float:
        if not svg_text.strip().startswith("<svg"):
            return 0.0
        lowered = svg_text.casefold()
        if any(term in lowered for term in ["nsfw", "gore", "violence"]):
            return 0.0
        prompt_words = {word for word in re.findall(r"[\w']+", (prompt or "").casefold()) if len(word) > 2}
        svg_words = set(re.findall(r"[\w']+", lowered))
        overlap = len(prompt_words.intersection(svg_words))
        return 1.0 if overlap >= 1 else 0.85

    def check_fidelity(self, prompt: str, svg_text: str) -> float:
        prompt_words = {word for word in re.findall(r"[\w']+", (prompt or "").casefold()) if len(word) > 2}
        svg_words = set(re.findall(r"[\w']+", svg_text.casefold()))
        overlap = len(prompt_words.intersection(svg_words))
        if not prompt_words:
            return 0.5
        return min(1.0, 0.4 + 0.2 * overlap)

    def check_output_file(self, output_path: str, modality: str) -> float:
        score = self.detector.check_file(output_path, modality)
        if modality == "video":
            try:
                manifest = Path(output_path).read_text(encoding="utf-8")
            except OSError:
                return score
            if any(term in manifest.casefold() for term in self.forbidden_terms):
                return min(score, 0.2)
        return max(0.0, min(1.0, 1.0 - score))


__all__ = ["JonaCreativeGuard"]