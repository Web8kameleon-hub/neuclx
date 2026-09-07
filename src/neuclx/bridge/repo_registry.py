"""Registry for verified source manifests."""

from __future__ import annotations

import json
import os
from typing import Dict, List, Optional

from .evidence_contract import EvidenceContract
from .source_manifest import SourceManifest


class RepoRegistry:
    def __init__(self, storage_path: str = "./data/repo_registry.json"):
        self.storage_path = storage_path
        self.manifests: Dict[str, SourceManifest] = {}
        self._load()

    def register(self, manifest: SourceManifest, contract: Optional[EvidenceContract] = None) -> SourceManifest:
        contract = contract or EvidenceContract.default()
        contract.validate(manifest)
        self.manifests[manifest.id] = manifest
        self._save()
        return manifest

    def get(self, manifest_id: str) -> Optional[SourceManifest]:
        return self.manifests.get(manifest_id)

    def list_all(self) -> List[SourceManifest]:
        return list(self.manifests.values())

    def _load(self) -> None:
        if not os.path.exists(self.storage_path):
            return
        with open(self.storage_path, "r", encoding="utf-8") as handle:
            data = json.load(handle)
        for item in data:
            manifest = SourceManifest.from_dict(item)
            self.manifests[manifest.id] = manifest

    def _save(self) -> None:
        directory = os.path.dirname(self.storage_path)
        if directory:
            os.makedirs(directory, exist_ok=True)
        with open(self.storage_path, "w", encoding="utf-8") as handle:
            json.dump([manifest.to_dict() for manifest in self.manifests.values()], handle, indent=2, ensure_ascii=False)
