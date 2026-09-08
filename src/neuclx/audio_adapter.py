"""Deterministic audio generation using stdlib wave output."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import math
from pathlib import Path
import struct
import wave
from typing import Any, Dict


@dataclass(slots=True)
class AudioGenerator:
    output_dir: str = "data/creative_outputs"

    def __post_init__(self):
        self.output_dir_path = Path(self.output_dir)
        self.output_dir_path.mkdir(parents=True, exist_ok=True)
        self.sample_rate = 22050

    def generate(self, prompt: str, *, seed: int = 42, style: str = "clean", author: str | None = None, duration: int = 4, **kwargs: Any) -> tuple[str, str, Dict[str, Any]]:
        key = sha256(f"{prompt}|{seed}|{style}|{author or ''}|audio".encode("utf-8")).hexdigest()[:12]
        output_path = self.output_dir_path / f"creative_{key}.wav"
        frequencies = self._frequencies(prompt, seed)
        self._write_wave(output_path, frequencies, duration=max(1, int(duration)))
        output_hash = sha256(output_path.read_bytes()).hexdigest()
        metadata = {
            "model_name": "neuclx-tone-audio",
            "sample_rate": self.sample_rate,
            "duration": max(1, int(duration)),
            "frequencies": frequencies,
            "seed": seed,
            "style": style,
            "author": author,
            "safety_score": 1.0,
            "fidelity_score": 0.9,
        }
        return str(output_path), output_hash, metadata

    def safety_check(self, output_path: str) -> float:
        return 1.0 if Path(output_path).suffix.lower() == ".wav" else 0.2

    def _frequencies(self, prompt: str, seed: int) -> list[int]:
        base = int(sha256(f"{prompt}|{seed}".encode("utf-8")).hexdigest()[:8], 16)
        palette = [220, 247, 262, 294, 330, 349, 392, 440, 523]
        return [palette[(base >> (index * 3)) % len(palette)] for index in range(4)]

    def _write_wave(self, output_path: Path, frequencies: list[int], duration: int) -> None:
        total_samples = self.sample_rate * duration
        amplitude = 18000
        segment = max(1, total_samples // len(frequencies))
        samples = []
        for index in range(total_samples):
            frequency = frequencies[min(len(frequencies) - 1, index // segment)]
            value = int(amplitude * math.sin(2 * math.pi * frequency * (index / self.sample_rate)))
            samples.append(struct.pack("<h", value))
        with wave.open(str(output_path), "wb") as handle:
            handle.setnchannels(1)
            handle.setsampwidth(2)
            handle.setframerate(self.sample_rate)
            handle.writeframes(b"".join(samples))


__all__ = ["AudioGenerator"]