import asyncio
import unittest

from neuclx.agents import AgentOrchestrator, normalize_agent_identifier


class OrchestratorIntegrationTests(unittest.TestCase):
    def test_normalize_aliases(self):
        self.assertEqual(normalize_agent_identifier("Albi"), "albi")
        self.assertEqual(normalize_agent_identifier("ASI Trinity"), "asi-trinity")

    def test_orchestrator_registers_and_submits(self):
        async def run_test():
            orchestrator = AgentOrchestrator()
            await orchestrator.initialize()
            try:
                result = await orchestrator.submit("alba", {"action": "collect"})
                self.assertTrue(result.success)
                self.assertEqual(result.agent_id, result.agent_id)
                self.assertIn("metrics", result.result)

                health = await orchestrator.submit("jona", {"action": "recommend", "context": {"x": 1}})
                self.assertTrue(health.success)
                self.assertIn("recommendations", health.result)
            finally:
                await orchestrator.shutdown()

        asyncio.run(run_test())


if __name__ == "__main__":
    unittest.main()
