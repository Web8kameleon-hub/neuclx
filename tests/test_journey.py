import tempfile
import unittest
from pathlib import Path
from neuclx.web import NeuCLXApplication

class JourneyTests(unittest.TestCase):
    def test_success_stone_preserves_epistemic_truth(self):
        with tempfile.TemporaryDirectory() as directory:
            app = NeuCLXApplication(Path(directory)/"journey.sqlite3")
            try:
                first=app.respond("unknown")
                second=app.respond("sovereign",["NeuCLX is sovereign"])
                self.assertEqual(first["achievement"],"success")
                self.assertEqual(first["response"]["state"],"unavailable")
                self.assertEqual(second["response"]["state"],"computed")
                self.assertLessEqual(first["stigma_frame"]["compressed_bytes"],first["stigma_frame"]["original_bytes"])
                self.assertEqual(len(app.ledger.recent()),2)
            finally:
                app.close()
                del app

    def test_fact_ingestion_persists_verified_memory(self):
        with tempfile.TemporaryDirectory() as directory:
            app = NeuCLXApplication(Path(directory)/"journey.sqlite3")
            try:
                app.respond("what is neuclx", ["NeuCLX is sovereign and evidence-bound"])
                stored = app.memory.search("sovereign")
                self.assertTrue(any("sovereign" in item.content.lower() for item in stored))
                self.assertTrue(any(item.evidence_state == "computed" for item in stored))
            finally:
                app.close()
                del app

    def test_web_app_exposes_real_memory_and_adapter(self):
        with tempfile.TemporaryDirectory() as directory:
            app = NeuCLXApplication(Path(directory)/"journey.sqlite3")
            try:
                self.assertTrue(hasattr(app, "memory"))
                self.assertTrue(hasattr(app, "model_adapter"))
                response = app.respond("hello world")
                self.assertIn(response["response"]["state"], {"unavailable", "computed", "not_implemented"})
                self.assertGreaterEqual(len(app.memory.list_all()), 0)
            finally:
                app.close()
                del app

if __name__=="__main__": unittest.main()
