"""JONA guard for repository manifests and source evidence."""

from __future__ import annotations

from typing import Iterable, List

from .evidence_contract import ContractViolation, EvidenceContract
from .source_manifest import SourceManifest


class JonaGuard:
    """Accepts only manifests that pass the evidence contract."""

    def __init__(self, contract: EvidenceContract | None = None):
        self.contract = contract or EvidenceContract.default()

    def verify(self, manifest: SourceManifest) -> bool:
        try:
            self.contract.validate(manifest)
            return True
        except ContractViolation:
            return False

    def filter_manifests(self, manifests: Iterable[SourceManifest]) -> List[SourceManifest]:
        return [manifest for manifest in manifests if self.verify(manifest)]
