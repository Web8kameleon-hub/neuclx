"""Bridge layer that registers verified repositories and exports a unified manifest."""

from __future__ import annotations

import json
from typing import List

from .jona_guard import JonaGuard
from .repo_registry import RepoRegistry
from .source_manifest import EvidenceState, SourceManifest


class RepoBridge:
    def __init__(self, registry_path: str = "./data/repo_registry.json"):
        self.registry = RepoRegistry(registry_path)
        self.guard = JonaGuard()

    def register_repo(self, repo_path: str, repo_name: str, *, license: str = "MIT") -> SourceManifest:
        manifest = SourceManifest(
            id=f"repo-{abs(hash(repo_path))}",
            name=repo_name,
            source_type="repo",
            location=repo_path,
            metadata={"kind": "git"},
            hash=f"sha256:{repo_path}",
            evidence_state=EvidenceState.COMPUTED,
            license=license,
            version="1.0.0",
        )
        if not self.guard.verify(manifest):
            raise PermissionError(f"Repository '{repo_name}' failed JONA verification.")
        self.registry.register(manifest)
        return manifest

    def get_verified_repos(self) -> List[SourceManifest]:
        return self.guard.filter_manifests(self.registry.list_all())

    def export_manifest(self, output_path: str = "./data/unified_manifest.json") -> None:
        verified = self.get_verified_repos()
        with open(output_path, "w", encoding="utf-8") as handle:
            json.dump([item.to_dict() for item in verified], handle, indent=2, ensure_ascii=False)
