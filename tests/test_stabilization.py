"""Stabilization tests for rule-based reasoning modules."""

from __future__ import annotations

import json
import tempfile
import unittest
from dataclasses import dataclass
from pathlib import Path
from unittest.mock import MagicMock

from neuclx.context_isolator import ContextIsolator
from neuclx.evidence_filter import EvidenceFilter
from neuclx.jona_guard_enhanced import JonaGuardEnhanced
from neuclx.seed_loader import SeedLoader
from neuclx.simple_logic_engine import SimpleLogicEngine
from neuclx.stable_reasoning_engine import StableReasoningEngine


class SimpleLogicEngineTests(unittest.TestCase):
    def test_arithmetic(self):
        self.assertEqual(SimpleLogicEngine.detect_and_solve("2 + 2")[1], "4")
        self.assertEqual(SimpleLogicEngine.detect_and_solve("sqrt(16)")[1], "4")
        self.assertEqual(SimpleLogicEngine.detect_and_solve("10 / 2")[1], "5")

    def test_transfer_word_problem(self):
        solved, answer, confidence = SimpleLogicEngine.detect_and_solve(
            "If 3 students each have 2 books and one gives 1 book to someone without one, how many books are there in total?"
        )
        self.assertTrue(solved)
        self.assertEqual(answer, "6")
        self.assertGreaterEqual(confidence, 0.9)

    def test_classification(self):
        result = SimpleLogicEngine.detect_and_solve("7 është numër i thjeshtë")
        self.assertTrue(result[0])
        self.assertIn("Po", result[1])


class ContextIsolatorTests(unittest.TestCase):
    def test_isolation(self):
        isolator = ContextIsolator()
        cid1 = isolator.start_new_context("req1")
        isolator.add_step(cid1, {"step": 1})
        cid2 = isolator.start_new_context("req2")
        self.assertEqual(len(isolator.get_context(cid2)["steps"]), 0)


class EvidenceFilterTests(unittest.TestCase):
    def test_filter(self):
        mock_memory = MagicMock()
        mock_memory.search.return_value = [
            {"content": "fakt 1", "evidence_state": "computed", "confidence": 0.9, "timestamp": 10},
            {"content": "fakt 2", "evidence_state": "unverified", "confidence": 0.2, "timestamp": 20},
        ]
        ef = EvidenceFilter(mock_memory)
        result = ef.retrieve_relevant("fakt", "balanced", top_k=5)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["content"], "fakt 1")


class JonaGuardTests(unittest.TestCase):
    def test_verify(self):
        guard = JonaGuardEnhanced()
        evidence = [{"content": "Toka është e rrumbullakët"}]
        self.assertTrue(guard.verify_response("Toka është e rrumbullakët", evidence))
        self.assertFalse(guard.verify_response("Toka është e sheshtë dhe pa proof", evidence))


class SeedLoaderTests(unittest.TestCase):
    def test_load(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            seed_path = Path(tmpdir) / "seed.json"
            seed_path.write_text(json.dumps([{"subject": "test", "relation": "is", "object": "value"}]), encoding="utf-8")

            mock_memory = MagicMock()
            mock_memory.semantic.get_all.return_value = []
            loader = SeedLoader(mock_memory, str(seed_path))
            count = loader.load()

            self.assertEqual(count, 1)
            mock_memory.add_fact.assert_called()


class StableReasoningEngineTests(unittest.TestCase):
    def test_simple_logic_without_facts(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            memory = MagicMock()
            memory.store = MagicMock()
            engine = StableReasoningEngine(memory, model_adapter=None, seed_path=str(Path(tmpdir) / "seed.json"))
            result = engine.process(
                "If 3 students each have 2 books and one gives 1 book to someone without one, how many books are there in total?",
                facts=[],
            )

            self.assertEqual(result["status"], "ok")
            self.assertEqual(result["intent"], "arithmetic.word_problem")
            self.assertEqual(result["conclusion"], "6")
            self.assertEqual(result["confidence_breakdown"]["calculation"], 1.0)
            self.assertEqual(result["operations"][0]["reasoning_type"], "symbolic")
            self.assertEqual(result["operations"][0]["operation"], "3 × 2")
            self.assertEqual(result["operations"][0]["result"], "6")
            self.assertEqual(result["evidence_path"], [])

    def test_clean_reasoning_score(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            seed_path = Path(tmpdir) / "seed.json"
            seed_path.write_text(
                json.dumps([
                    {"subject": "JONA", "relation": "is", "object": "guardrail", "confidence": 1.0, "source": "seed"}
                ]),
                encoding="utf-8",
            )
            memory = MagicMock()
            memory.store = MagicMock()
            engine = StableReasoningEngine(memory, model_adapter=None, seed_path=str(seed_path))
            engine.process("What is JONA?", facts=[], policy_mode="balanced")
            score = engine.get_clean_reasoning_score()
            self.assertIn("clean_reasoning_score", score)
            self.assertGreaterEqual(score["clean_reasoning_score"], 0.0)


if __name__ == "__main__":
    unittest.main()