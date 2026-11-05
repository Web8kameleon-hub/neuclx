import tempfile
import unittest
from pathlib import Path

from neuclx.evidence import Datum, EvidenceState
from neuclx.journey import JourneyLedger
from neuclx.jona import JonaSandbox
from neuclx.learning import LearningStore
from neuclx.self_learning import BIG_BYTES, SelfLearning, tier_of


def web_hit(url="https://example.org/skenderbeu", excerpt="Skenderbeu udhehoqi rezistencen shqiptare kunder osmaneve."):
    return {"source": url, "sha256": "ab" * 32, "revision": "sha256:" + "ab" * 32, "excerpt": excerpt}


class SelfLearningTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        root = Path(directory.name)
        self.jona = JonaSandbox()
        self.learning = LearningStore(root / "learning.sqlite3", self.jona)
        self.ledger = JourneyLedger(str(root / "ledger.sqlite3"))
        self.addCleanup(self.ledger.close)
        self.sl = SelfLearning(self.learning, self.ledger, self.jona)

    def test_tier_rule(self):
        self.assertEqual(tier_of(BIG_BYTES, 99), "bigdata")
        self.assertEqual(tier_of(10, 1), "seltendata")
        self.assertEqual(tier_of(10, 2), "standarddata")

    def test_web_excerpt_is_learned_once_and_retrievable_with_citation(self):
        self.assertEqual(self.sl.learn_web_hits([web_hit()]), 1)
        self.assertEqual(self.sl.learn_web_hits([web_hit()]), 0)
        answer = self.learning.answer("Kush udhehoqi rezistencen kunder osmaneve Skenderbeu")
        chain = answer.metadata["evidence_chain"]
        self.assertTrue(chain)
        self.assertTrue(chain[0]["source"].startswith("https://example.org/skenderbeu#"))

    def test_usage_moves_a_document_from_seltendata_to_standarddata(self):
        self.sl.learn_web_hits([web_hit()])
        hit = self.learning.answer("Skenderbeu rezistencen osmaneve").metadata["evidence_chain"][0]
        self.sl.record_use([hit])
        self.assertEqual(self.sl.tiers().value["tiers"], {"seltendata": 1, "standarddata": 0, "bigdata": 0})
        self.sl.record_use([hit])
        self.assertEqual(self.sl.tiers().value["tiers"], {"seltendata": 0, "standarddata": 1, "bigdata": 0})

    def test_answer_is_remembered_as_frame_but_not_ingested_as_fact(self):
        before = self.learning.status().value["documents"]
        generated = Datum("Skenderbeu udhehoqi rezistencen.", EvidenceState.COMPUTED, "local:test", "stub", {})
        memory = self.sl.remember_answer("Kush ishte Skenderbeu?", generated, [])
        self.assertEqual(self.learning.status().value["documents"], before)
        self.assertFalse(memory["grounding"]["grounded"])
        self.assertIn("no retrieved source", memory["answer"].metadata["claim_status"])
        recalled = self.ledger.recent(1)[0]
        self.assertEqual(recalled["response"]["value"], "Skenderbeu udhehoqi rezistencen.")

    def test_grounding_reports_overlap_and_literal_citation(self):
        hit = web_hit()
        text = "Sipas " + hit["source"] + " Skenderbeu udhehoqi rezistencen shqiptare."
        grounding = SelfLearning.grounding(text, [hit])
        self.assertTrue(grounding["grounded"])
        self.assertEqual(grounding["cited_sources"], [hit["source"]])
        self.assertGreaterEqual(grounding["answer_term_overlap"], 0.5)


    def test_newdata_flags_first_occurrence_only_and_stays_out_of_corpus(self):
        before = self.learning.status().value["documents"]
        facets = {"mode": "hybrid-fluid", "model": "local:x", "sources": "example.org"}
        first = self.sl.observe_novelty("Skenderbeu udhehoqi rezistencen", facets)
        again = self.sl.observe_novelty("rezistencen udhehoqi Skenderbeu", facets)
        other = self.sl.observe_novelty("Tekst i ri krejt tjeter", {**facets, "model": "local:y"})
        self.assertTrue(first["first_seen_answer"] and first["new_combination"])
        self.assertFalse(again["first_seen_answer"] or again["new_combination"])
        self.assertTrue(other["first_seen_answer"] and other["new_combination"])
        self.assertEqual(self.sl.newdata(), {"first_seen_answer": 2, "new_combination": 2})
        self.assertEqual(self.learning.status().value["documents"], before)
        self.assertTrue(first["quarantine"])


if __name__ == "__main__":
    unittest.main()
