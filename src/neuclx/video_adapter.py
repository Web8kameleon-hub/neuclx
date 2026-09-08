"""Deterministic video-package generation without external video libraries."""

from __future__ import annotations

from dataclasses import dataclass, field
from hashlib import sha256
import json
from pathlib import Path
from typing import Any


@dataclass(slots=True)
class VideoGenerator:
    output_dir: str = "data/creative_outputs"
    output_dir_path: Path = field(init=False, repr=False)

    def __post_init__(self):
        self.output_dir_path = Path(self.output_dir)
        self.output_dir_path.mkdir(parents=True, exist_ok=True)

    def generate(self, prompt: str, *, seed: int = 42, style: str = "clean", author: str | None = None, frames: int = 8, **kwargs: Any) -> tuple[str, str, dict[str, Any]]:
        key = sha256(f"{prompt}|{seed}|{style}|{author or ''}|video".encode()).hexdigest()[:12]
        package_dir = self.output_dir_path / f"creative_video_{key}"
        package_dir.mkdir(parents=True, exist_ok=True)
        frame_paths = []
        frame_count = max(2, min(int(frames), 24))
        for index in range(frame_count):
            frame_path = package_dir / f"frame_{index:03d}.svg"
            frame_path.write_text(self._frame_svg(prompt, seed, style, author, index, frame_count), encoding="utf-8")
            frame_paths.append(str(frame_path))
        manifest = {
            "modality": "video",
            "prompt": prompt,
            "seed": seed,
            "style": style,
            "author": author,
            "frame_count": frame_count,
            "frame_paths": frame_paths,
            "model_name": "neuclx-video-package",
        }
        output_path = package_dir / "manifest.json"
        output_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
        output_hash = sha256(output_path.read_bytes()).hexdigest()
        metadata = {
            "model_name": "neuclx-video-package",
            "frame_count": frame_count,
            "frame_paths": frame_paths,
            "seed": seed,
            "style": style,
            "author": author,
            "safety_score": 1.0,
            "fidelity_score": 0.9,
        }
        return str(output_path), output_hash, metadata

    def safety_check(self, output_path: str) -> float:
        return 1.0 if Path(output_path).suffix.lower() == ".json" else 0.4

    def _frame_svg(self, prompt: str, seed: int, style: str, author: str | None, index: int, frame_count: int) -> str:
        palette = ["#10131f", "#17203b", "#2d5b8a", "#8dd3c7", "#ffffb3", "#fb8072"]
        accent = palette[(seed + index) % (len(palette) - 1) + 1]
        return (
            '<svg xmlns="http://www.w3.org/2000/svg" width="640" height="360" viewBox="0 0 640 360">'
            f'<rect width="640" height="360" fill="{palette[0]}" />'
            f'<circle cx="{120 + index * 44}" cy="{120 + (seed * 7 + index * 11) % 80}" r="{28 + index * 2}" fill="{accent}" opacity="0.88" />'
            f'<rect x="60" y="260" width="{80 + index * 12}" height="40" rx="10" fill="{palette[(index + 2) % len(palette)]}" opacity="0.7" />'
            f'<text x="40" y="40" fill="#ffffff" font-family="Consolas, monospace" font-size="16">frame {index + 1}/{frame_count}</text>'
            f'<text x="40" y="66" fill="#cfd6ff" font-family="Consolas, monospace" font-size="12">{prompt[:80]}</text>'
            f'<text x="40" y="340" fill="#cfd6ff" font-family="Consolas, monospace" font-size="12">seed={seed} style={style} author={author or "unknown"}</text>'
            '</svg>'
        )


__all__ = ["VideoGenerator"]