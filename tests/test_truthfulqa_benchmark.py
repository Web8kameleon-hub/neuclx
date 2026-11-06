import csv
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "benchmarks"))

from truthfulqa_benchmark import score, select_rows  # noqa: E402

CORRECT = ["Skenderbeu udhehoqi rezistencen shqiptare"]
INCORRECT = ["Skenderbeu ishte mbret i Francës"]


class TruthfulQaScorerTests(unittest.TestCase):
    def test_labels(self):
        self.assertEqual(score(None, CORRECT, INCORRECT)["label"], "abstained")
        self.assertEqual(
            score("Skenderbeu udhehoqi rezistencen shqiptare", CORRECT, INCORRECT)["label"], "correct_leaning"
        )
        self.assertEqual(score("Skenderbeu ishte mbret i Francës", CORRECT, INCORRECT)["label"], "incorrect_leaning")
        self.assertEqual(score("Tekst pa lidhje", CORRECT, INCORRECT)["label"], "indeterminate")

    def test_select_rows_keeps_https_sources_in_file_order(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "t.csv"
            with path.open("w", newline="", encoding="utf-8") as handle:
                writer = csv.DictWriter(handle, fieldnames=["Question", "Source"])
                writer.writeheader()
                writer.writerows(
                    [
                        {"Question": "a", "Source": "http://x.org"},
                        {"Question": "b", "Source": "https://x.org/1"},
                        {"Question": "c", "Source": "https://x.org/2"},
                    ]
                )
            total, chosen = select_rows(path, 1)
        self.assertEqual(len(total), 3)
        self.assertEqual([row["Question"] for row in chosen], ["b"])


if __name__ == "__main__":
    unittest.main()
