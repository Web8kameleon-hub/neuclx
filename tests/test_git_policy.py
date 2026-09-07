import unittest
from scripts.enforce_main_only import validate


class SingleTreePolicyTests(unittest.TestCase):
    def test_main_push_passes(self):
        self.assertTrue(validate("refs/heads/main", "push")[0])

    def test_parallel_branch_fails(self):
        self.assertFalse(validate("refs/heads/feature/x", "push")[0])

    def test_pull_request_ref_fails(self):
        self.assertFalse(validate("refs/pull/2/merge", "pull_request")[0])

    def test_semantic_release_tag_passes(self):
        self.assertTrue(validate("refs/tags/v0.1.0", "push")[0])

    def test_malformed_or_moving_tag_names_fail(self):
        self.assertFalse(validate("refs/tags/latest", "push")[0])
        self.assertFalse(validate("refs/tags/v01.2.3", "push")[0])


if __name__ == "__main__":
    unittest.main()
