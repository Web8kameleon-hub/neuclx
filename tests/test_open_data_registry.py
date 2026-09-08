import tempfile
import unittest
from pathlib import Path

from neuclx.web import NeuCLXApplication


class OpenDataRegistryTests(unittest.TestCase):
    def test_registry_exposes_real_free_sources(self):
        with tempfile.TemporaryDirectory() as directory:
            app = NeuCLXApplication(Path(directory) / "registry.sqlite3")
            try:
                sources = app.source_registry.list_sources()
                self.assertGreater(len(sources), 8)
                names = {entry["name"] for entry in sources}
                self.assertIn("World Bank Open Data", names)
                self.assertIn("Data.gov USA", names)
                self.assertIn("Open-Meteo", names)
                self.assertIn("OpenStreetMap Overpass", names)
            finally:
                app.close()
                del app

    def test_registry_summary_includes_region_counts(self):
        with tempfile.TemporaryDirectory() as directory:
            app = NeuCLXApplication(Path(directory) / "registry.sqlite3")
            try:
                summary = app.source_registry.summary()
                self.assertIn("total_sources", summary)
                self.assertIn("regions", summary)
                self.assertGreater(summary["total_sources"], 8)
            finally:
                app.close()
                del app


if __name__ == "__main__":
    unittest.main()
