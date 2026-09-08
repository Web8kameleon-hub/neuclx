"""Local NSFW heuristics for creative outputs.

This stays stdlib-only and returns conservative scores rather than claiming
model-based detection.
"""

from __future__ import annotations

from pathlib import Path


class NSFWDetector:
    forbidden_terms = (
        "nsfw",
        "porn",
        "sexual",
        "explicit",
        "gore",
        "violence",
        "hate",
        "self-harm",
        "illegal",
    )

    def check_text(self, text: str) -> float:
        lowered = (text or "").casefold()
        if not lowered.strip():
            return 0.0
        hits = sum(1 for term in self.forbidden_terms if term in lowered)
        return min(1.0, hits / len(self.forbidden_terms))

    def check_file(self, path: str | Path, modality: str) -> float:
        file_path = Path(path)
        if not file_path.exists():
            return 0.0
        if modality in {"code", "text"}:
            try:
                content = file_path.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                return 0.5
            return self.check_text(content)
        if modality in {"video", "cad", "image", "audio"}:
            name = file_path.name.casefold()
            return self.check_text(name)
        return 0.0


__all__ = ["NSFWDetector"]