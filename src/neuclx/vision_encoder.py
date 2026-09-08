"""Stdlib-only image evidence inspection for NeuCLX."""

from __future__ import annotations

import base64
import hashlib
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .evidence import Datum, EvidenceState


class VisionEncoder:
    """Deterministically inspects image files and returns measured evidence."""

    def inspect_path(self, image_path: str | Path, *, author: str | None = None, task: str | None = None) -> Datum:
        path = Path(image_path)
        if not path.is_file():
            raise FileNotFoundError(f"image not found: {path}")
        return self.inspect_bytes(path.read_bytes(), source=str(path), author=author, task=task)

    def inspect_bytes(self, image_bytes: bytes, *, source: str, author: str | None = None, task: str | None = None) -> Datum:
        if not isinstance(image_bytes, (bytes, bytearray)):
            raise TypeError("image_bytes must be bytes")

        data = bytes(image_bytes)
        format_name, width, height = self._decode_header(data)
        digest = hashlib.sha256(data).hexdigest()
        aspect_ratio = round(width / height, 6) if width and height else None
        confidence = 1.0 if width and height else 0.8 if format_name != "unknown" else 0.5

        value: dict[str, Any] = {
            "kind": "image_evidence",
            "source": source,
            "format": format_name,
            "byte_size": len(data),
            "sha256": digest,
            "width": width,
            "height": height,
            "aspect_ratio": aspect_ratio,
            "author": author,
            "task": task,
            "confidence": confidence,
            "captured_at": datetime.now(UTC).isoformat(),
        }
        return Datum(
            value,
            EvidenceState.MEASURED,
            source=source,
            method="vision:header-inspection",
            metadata={
                "format": format_name,
                "width": width,
                "height": height,
                "aspect_ratio": aspect_ratio,
                "sha256": digest,
                "confidence": confidence,
            },
        )

    def inspect_base64(self, image_b64: str, *, source: str, author: str | None = None, task: str | None = None) -> Datum:
        return self.inspect_bytes(base64.b64decode(image_b64), source=source, author=author, task=task)

    @staticmethod
    def _decode_header(data: bytes) -> tuple[str, int | None, int | None]:
        if data.startswith(b"\x89PNG\r\n\x1a\n") and len(data) >= 24:
            width = int.from_bytes(data[16:20], "big")
            height = int.from_bytes(data[20:24], "big")
            return "png", width, height
        if data.startswith(b"GIF87a") or data.startswith(b"GIF89a"):
            if len(data) >= 10:
                width = int.from_bytes(data[6:8], "little")
                height = int.from_bytes(data[8:10], "little")
                return "gif", width, height
        if data.startswith(b"\xff\xd8"):
            return VisionEncoder._decode_jpeg(data)
        return "unknown", None, None

    @staticmethod
    def _decode_jpeg(data: bytes) -> tuple[str, int | None, int | None]:
        sof_markers = {
            0xC0,
            0xC1,
            0xC2,
            0xC3,
            0xC5,
            0xC6,
            0xC7,
            0xC9,
            0xCA,
            0xCB,
            0xCD,
            0xCE,
            0xCF,
        }
        index = 2
        size = len(data)
        while index < size:
            while index < size and data[index] == 0xFF:
                index += 1
            if index >= size:
                break
            marker = data[index]
            index += 1
            if marker in {0xD8, 0xD9}:
                continue
            if index + 2 > size:
                break
            segment_length = int.from_bytes(data[index:index + 2], "big")
            if segment_length < 2:
                break
            segment_start = index + 2
            if marker in sof_markers and segment_start + 5 <= size:
                height = int.from_bytes(data[segment_start + 1:segment_start + 3], "big")
                width = int.from_bytes(data[segment_start + 3:segment_start + 5], "big")
                return "jpeg", width, height
            index = segment_start + segment_length - 2
        return "jpeg", None, None


__all__ = ["VisionEncoder"]