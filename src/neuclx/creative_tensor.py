"""Creative tensor model for declared NeuCLX creations."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from hashlib import sha256
from typing import Any, Dict

from .evidence import EvidenceState


class CreativeModality(StrEnum):
    TEXT = "text"
    IMAGE = "image"
    AUDIO = "audio"
    VIDEO = "video"
    CODE = "code"
    CAD = "cad"


@dataclass(slots=True)
class CreativeTensor:
    prompt: str
    seed: int = 42
    modality: CreativeModality = CreativeModality.TEXT
    model_name: str = "neuclx-creative-local"
    safety_score: float = 1.0
    fidelity_score: float = 1.0
    output_hash: str = ""
    output_path: str | None = None
    parameters: Dict[str, Any] = field(default_factory=dict)
    state: EvidenceState = EvidenceState.DECLARED

    def __post_init__(self):
        if not self.output_hash:
            self.output_hash = self._compute_tensor_hash()

    def _compute_tensor_hash(self) -> str:
        payload = f"{self.prompt}|{self.seed}|{self.modality}|{self.model_name}|{self.safety_score}|{self.fidelity_score}|{self.output_path or ''}"
        return sha256(payload.encode("utf-8")).hexdigest()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "prompt": self.prompt,
            "seed": self.seed,
            "modality": self.modality.value,
            "model_name": self.model_name,
            "safety_score": self.safety_score,
            "fidelity_score": self.fidelity_score,
            "output_hash": self.output_hash,
            "output_path": self.output_path,
            "parameters": dict(self.parameters),
            "state": self.state.value,
        }


__all__ = ["CreativeModality", "CreativeTensor"]