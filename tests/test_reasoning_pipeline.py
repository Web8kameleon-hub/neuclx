import unittest

from neuclx.engine import CognitiveKernel, ReasoningPipeline


class ReasoningPipelineTests(unittest.TestCase):
    def test_pipeline_builds_reasoned_response(self):
        kernel = CognitiveKernel(layers=4)
        kernel.ingest("memory", "JONA enforces sandbox policy")
        pipeline = ReasoningPipeline(kernel=kernel)

        result = pipeline.run(
            "Cila është roli i JONA në NeuCLX?",
            facts=["JONA enforces sandbox policy", "NeuCLX stores evidence-bound memory"],
        )

        self.assertEqual(result["pipeline"], "reasoning")
        self.assertIn("steps", result)
        self.assertGreaterEqual(len(result["steps"]), 3)
        self.assertIn(result["agent"], {"alba", "jona", "albi"})
        self.assertIn(result["state"], {"computed", "unavailable", "measured"})
        self.assertTrue(bool(result["answer"]))


if __name__ == "__main__":
    unittest.main()
