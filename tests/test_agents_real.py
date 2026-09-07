import unittest

from neuclx.agents import AlbaAgent, AlbiAgent, JonaAgent


class RealAgentTests(unittest.TestCase):
    def test_alba_answers_bridge_questions(self):
        answer = AlbaAgent().answer("Cila është bridge-layer në NeuCLX?")
        lowered = answer.lower()
        self.assertIn("bridge", lowered)
        self.assertIn("manifest", lowered)
        self.assertIn("jona", lowered)

    def test_albi_answers_ui_and_memory_questions(self):
        answer = AlbiAgent().answer("A ka UI dhe memory reale?")
        lowered = answer.lower()
        self.assertIn("ui", lowered)
        self.assertIn("memory", lowered)

    def test_jona_answers_policy_questions(self):
        answer = JonaAgent().answer("Cili është roli i JONA?")
        lowered = answer.lower()
        self.assertIn("sandbox", lowered)
        self.assertIn("policy", lowered)


if __name__ == "__main__":
    unittest.main()
