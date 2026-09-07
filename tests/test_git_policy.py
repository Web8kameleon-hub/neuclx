import unittest
from scripts.enforce_main_only import validate


class SingleTreePolicyTests(unittest.TestCase):
    def test_main_push_passes(self):
        self.assertTrue(validate("refs/heads/main", "push")[0])

    def test_parallel_branch_fails(self):
        self.assertFalse(validate("refs/heads/feature/x", "push")[0])

    def test_pull_request_ref_fails(self):
        self.assertFalse(validate("refs/pull/2/merge", "pull_request")[0])


if __name__ == "__main__":
    unittest.main()
