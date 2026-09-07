"""Source manifest and evidence state definitions."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional


class EvidenceState(str, Enum):
    MEASURED = "measured"
    COMPUTED = "computed"
    DECLARED = "declared"
    UNAVAILABLE = "unavailable"
    NOT_IMPLEMENTED = "not_implemented"


@dataclass
class SourceManifest:
    id: str
    name: str
    source_type: str
    location: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    hash: Optional[str] = None
    evidence_state: EvidenceState = EvidenceState.DECLARED
    timestamp: datetime = field(default_factory=datetime.utcnow)
    license: Optional[str] = None
    version: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "source_type": self.source_type,
            "location": self.location,
            "metadata": self.metadata,
            "hash": self.hash,
            "evidence_state": self.evidence_state.value,
            "timestamp": self.timestamp.isoformat(),
            "license": self.license,
            "version": self.version,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SourceManifest":
        return cls(
            id=data["id"],
            name=data["name"],
            source_type=data["source_type"],
            location=data["location"],
            metadata=data.get("metadata", {}),
            hash=data.get("hash"),
            evidence_state=EvidenceState(data.get("evidence_state", EvidenceState.DECLARED.value)),
            timestamp=datetime.fromisoformat(data["timestamp"]),
            license=data.get("license"),
            version=data.get("version"),
        )
