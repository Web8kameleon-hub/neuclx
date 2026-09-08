import unittest

from neuclx.reasoning_engine import ReasoningEngine, ReasoningType


class ReasoningEngineTests(unittest.TestCase):
    def test_reasoning_engine_builds_evidence_path_and_tree(self):
        engine = ReasoningEngine()
        result = engine.reason(
            "Cila është roli i JONA në NeuCLX?",
            context=[
                "JONA është kufiri i policy-s dhe sandbox-it.",
                "NeuCLX verifikon çdo përgjigje me evidencë të matur ose të llogaritur.",
                "Bridge kontrollon burimet para se të hyjnë në kernel.",
            ],
            max_iterations=3,
        )

        self.assertEqual(result["status"], "ok")
        self.assertIn(result["intent"], {"exploratory", "analytical", "general"})
        self.assertIn("conclusion", result)
        self.assertIn("evidence_path", result)
        self.assertIsInstance(result["trace"]["steps"], list)
        self.assertTrue(len(result["trace"]["steps"]) >= 2)
        self.assertIn(result["trace"]["steps"][0]["reasoning_type"], {rt.value for rt in ReasoningType})

    def test_reasoning_engine_rejects_unverified_answers(self):
        engine = ReasoningEngine()
        result = engine.reason(
            "Çfarë dihet rreth deklaratës së pa-verifikuar?",
            context=["Vetëm pohime të matura ose të llogaritura mund të dalin jashtë sandbox-it."],
            max_iterations=2,
        )

        self.assertEqual(result["status"], "ok")
        self.assertTrue(result["conclusion"])
        self.assertTrue(result["evidence_path"])

    def test_reasoning_engine_refuses_empty_evidence(self):
        engine = ReasoningEngine()
        result = engine.reason("kush je ti", context=[], max_iterations=2)

        self.assertEqual(result["status"], "ok")
        self.assertIn("Nuk ka evidencë të disponueshme", result["conclusion"])
        self.assertEqual(result["confidence"], 0.0)
        self.assertEqual(result["evidence_path"], [])

    def test_reasoning_engine_isolates_context_between_tasks(self):
        engine = ReasoningEngine()

        first = engine.reason(
            "Sa është ora dhe data e saktë sot?",
            context=["Koha e tanishme duhet të përputhet me orën lokale të sistemit."],
            max_iterations=1,
        )
        second = engine.reason(
            "Nëse 3 studentë kanë 2 libra secili dhe njëri i jep 1 libër atij që nuk ka, sa libra ka në total?",
            context=["Këtu duhet të llogaritet sasia totale e objekteve të dhëna."],
            max_iterations=1,
        )

        self.assertEqual(first["status"], "ok")
        self.assertEqual(second["status"], "ok")
        self.assertNotIn("ora dhe data", second["conclusion"].lower())
        self.assertNotIn("sa është ora", second["conclusion"].lower())

    def test_reasoning_engine_solves_simple_numeric_logic(self):
        engine = ReasoningEngine()
        result = engine.reason(
            "Nëse 3 studentë kanë 2 libra secili dhe njëri i jep 1 libër atij që nuk ka, sa libra ka në total?",
            context=["Sasia totale nuk ndryshon kur një libër kalon nga një person te tjeter."],
            max_iterations=2,
        )

        self.assertEqual(result["status"], "ok")
        self.assertIn("6", result["conclusion"])
        self.assertTrue(result["confidence"] >= 0.9)

    def test_reasoning_engine_solves_english_simple_numeric_logic(self):
        engine = ReasoningEngine()
        result = engine.reason(
            "If 3 students each have 2 books and one gives 1 book to someone without one, how many books are there in total?",
            context=[],
            max_iterations=2,
        )

        self.assertEqual(result["status"], "ok")
        self.assertIn("6", result["conclusion"])
        self.assertTrue(result["confidence"] >= 0.9)
        self.assertEqual(result["intent"], "arithmetic.word_problem")
        self.assertEqual(result["confidence_breakdown"]["calculation"], 1.0)
        self.assertEqual(result["operations"][0]["reasoning_type"], "symbolic")
        self.assertEqual(result["operations"][0]["operation"], "3 × 2")
        self.assertEqual(result["operations"][0]["result"], "6")
        self.assertEqual(result["evidence_path"], [])

    def test_web_application_exposes_reason_api(self):
        from neuclx.web import NeuCLXApplication

        app = NeuCLXApplication("data/test_reason_api.sqlite3")
        try:
            result = app.reason("Cila është roli i JONA?", ["JONA është kufiri i policy-s dhe sandbox-it."])
            self.assertEqual(result["status"], "ok")
            self.assertIn("conclusion", result)
            self.assertIn("trace", result)
        finally:
            app.close()


if __name__ == "__main__":
    unittest.main()
