import unittest
from scripts.validate_import_candidates import validate
class ImportCandidateTests(unittest.TestCase):
    def test_manifest_has_16_unique_provenance_bound_sources(self):self.assertEqual(validate(),[])
if __name__=="__main__":unittest.main()
