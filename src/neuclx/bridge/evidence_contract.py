"""Evidence contract for verified metadata and data sources."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from .source_manifest import EvidenceState, SourceManifest


class ContractViolation(ValueError):
    """Raised when a source fails the evidence contract."""


@dataclass
class EvidenceContract:
    required_fields: List[str] = field(default_factory=lambda: [
        "id",
        "name",
        "source_type",
        "location",
        "hash",
        "timestamp",
        "license",
    ])
    allowed_states: List[EvidenceState] = field(default_factory=lambda: [
        EvidenceState.MEASURED,
        EvidenceState.COMPUTED,
    ])
    require_hash: bool = True
    require_license: bool = True
    require_timestamp: bool = True

    def validate(self, manifest: SourceManifest) -> bool:
        for field_name in self.required_fields:
            value = getattr(manifest, field_name, None)
            if value in (None, ""):
                raise ContractViolation(f"Field '{field_name}' is required.")

        if manifest.evidence_state not in self.allowed_states:
            raise ContractViolation(
                f"Evidence state '{manifest.evidence_state.value}' is not allowed."
            )

        if self.require_hash and manifest.hash is None:
            raise ContractViolation("Manifest hash is required.")
        if self.require_license and manifest.license is None:
            raise ContractViolation("Manifest license is required.")
        if self.require_timestamp and manifest.timestamp is None:
            raise ContractViolation("Manifest timestamp is required.")

        return True

    @classmethod
    def default(cls) -> "EvidenceContract":
        return cls()
