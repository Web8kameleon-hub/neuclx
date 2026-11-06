import json
from pathlib import Path
import tempfile
import unittest
import zipfile
from scripts.build_release import build

class ReleaseTests(unittest.TestCase):
    def test_release_contains_artifacts_checksums_sbom_and_truth_manifest(self):
        with tempfile.TemporaryDirectory() as directory:
            build("0.1.0","a"*40,"Web8kameleon-hub/neuclx","test-run",directory)
            files={p.name for p in Path(directory).iterdir()}
            self.assertIn("neuclx-0.1.0-py3-none-any.whl",files)
            self.assertIn("neuclx-0.1.0.tar.gz",files)
            self.assertIn("SHA256SUMS",files)
            with zipfile.ZipFile(Path(directory) / "neuclx-0.1.0-py3-none-any.whl") as wheel:
                self.assertIn("neuclx/data/__init__.py", wheel.namelist())
                self.assertIn("neuclx/data/normalize.py", wheel.namelist())
                self.assertIn("neuclx/data/validate.py", wheel.namelist())
            manifest=json.loads((Path(directory)/"neuclx-0.1.0.release-manifest.json").read_text())
            self.assertEqual(manifest["claims"]["candidate_status"],"built_pending_attestation")
            self.assertEqual(manifest["builder"]["provenance_status"],"pending")
            self.assertNotIn("tag", manifest["git"])
            self.assertNotIn("tests", manifest["verification"])
            sbom=json.loads((Path(directory)/"neuclx-0.1.0.sbom.spdx.json").read_text())
            self.assertIn("/neuclx-candidates/", sbom["documentNamespace"])

    def test_tag_and_project_version_must_match(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(ValueError): build("9.9.9","a"*40,"Web8kameleon-hub/neuclx","test",directory)

if __name__=="__main__": unittest.main()
