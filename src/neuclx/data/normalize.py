"""Normalize source records without changing their evidence state."""

from __future__ import annotations

import unicodedata
from collections.abc import Mapping
from typing import Any


class DataNormalizer:
    @staticmethod
    def normalize_record(record: Mapping[str, Any]) -> dict[str, Any]:
        if not isinstance(record, Mapping):
            raise TypeError("record must be a mapping")

        normalized = dict(record)
        content = record.get("content", record.get("text"))
        if not isinstance(content, str):
            raise ValueError("record content or text must be a string")
        normalized["content"] = " ".join(
            unicodedata.normalize("NFKC", content).split()
        )

        source_id = record.get("source_id", record.get("source"))
        if source_id is not None:
            if not isinstance(source_id, str):
                raise ValueError("record source_id must be a string")
            normalized["source_id"] = source_id.strip()
        return normalized
