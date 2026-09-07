import tempfile
import unittest
from pathlib import Path
from neuclx.web import NeuCLXApplication

class JourneyTests(unittest.TestCase):
    def test_success_stone_preserves_epistemic_truth(self):
        with tempfile.TemporaryDirectory() as directory:
            app=NeuCLXApplication(Path(directory)/"journey.sqlite3")
            first=app.respond("unknown")
            second=app.respond("sovereign",["NeuCLX is sovereign"])
            self.assertEqual(first["achievement"],"success")
            self.assertEqual(first["response"]["state"],"unavailable")
            self.assertEqual(second["response"]["state"],"computed")
            self.assertLessEqual(first["stigma_frame"]["compressed_bytes"],first["stigma_frame"]["original_bytes"])
            self.assertEqual(len(app.ledger.recent()),2)

if __name__=="__main__": unittest.main()
