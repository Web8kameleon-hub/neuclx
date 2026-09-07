import unittest

from neuclx.bridge.evidence_contract import EvidenceContract, ContractViolation
from neuclx.bridge.jona_guard import JonaGuard
from neuclx.bridge.repo_registry import RepoRegistry
from neuclx.bridge.source_manifest import EvidenceState, SourceManifest
from neuclx.data.normalize import DataNormalizer
from neuclx.data.validate import DataValidator


class BridgeContractTests(unittest.TestCase):
    def test_manifest_requires_hash_and_source(self):
        manifest = SourceManifest(
            id="m-1",
            name="demo",
            source_type="repo",
            location="https://example.com/a",
            metadata={"owner": "demo"},
            hash="abc",
            evidence_state=EvidenceState.MEASURED,
            license="MIT",
            version="1.0.0",
        )
        self.assertIsNotNone(manifest)
        self.assertEqual(manifest.hash, "abc")

    def test_jona_guard_accepts_valid_manifest(self):
        manifest = SourceManifest(
            id="m-2",
            name="repo-valid",
            source_type="repo",
            location="https://example.com/repo",
            metadata={"kind": "git"},
            hash="hash-123",
            evidence_state=EvidenceState.MEASURED,
            license="MIT",
            version="1.0.0",
        )
        guard = JonaGuard(EvidenceContract.default())
        self.assertTrue(guard.verify(manifest))

    def test_registry_registers_manifest(self):
        registry = RepoRegistry(storage_path="./tmp/repo_registry_test.json")
        manifest = SourceManifest(
            id="m-3",
            name="registry-demo",
            source_type="repo",
            location="https://example.com/repo2",
            metadata={"kind": "git"},
            hash="hash-456",
            evidence_state=EvidenceState.COMPUTED,
            license="MIT",
            version="1.0.2",
        )
        registry.register(manifest)
        self.assertIn("m-3", registry.manifests)

    def test_data_normalize_and_validate(self):
        record = {"text": "  Hello world  ", "source": "repo-1", "license": "MIT"}
        normalized = DataNormalizer.normalize_record(record)
        self.assertEqual(normalized["content"], "Hello world")
        self.assertEqual(normalized["source_id"], "repo-1")

        validator = DataValidator(EvidenceContract.default())
        valid = validator.validate_record({
            "id": "r-1",
            "name": "demo-record",
            "source_type": "repo",
            "location": "https://example.com",
            "hash": "abc",
            "license": "MIT",
            "timestamp": "2026-01-01T00:00:00",
            "content": "hello world",
        })
        self.assertTrue(valid)


if __name__ == "__main__":
    unittest.main()
