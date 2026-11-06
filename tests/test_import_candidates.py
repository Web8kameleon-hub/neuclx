import unittest
from scripts.validate_import_candidates import canonical_content_sha256, validate


class ImportCandidateTests(unittest.TestCase):
    def test_manifest_has_16_unique_provenance_bound_sources(self):
        self.assertEqual(validate(), [])

    def test_candidate_digest_is_stable_across_crlf_checkouts(self):
        self.assertEqual(
            canonical_content_sha256(b"one\r\ntwo\r\n"),
            canonical_content_sha256(b"one\ntwo\n"),
        )


if __name__=="__main__":unittest.main()
