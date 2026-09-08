import asyncio
import unittest

from neuclx.mali import AnnouncementPriority, AnnouncementType, MaliCore


class MaliCoreTests(unittest.TestCase):
    def test_mali_cycle_runs_without_external_services(self):
        async def run_test():
            core = MaliCore()
            core.intake._fetch_json_with_failover = lambda source, urls: {"source": source, "status": "error", "error": "offline"}
            result = await core.run_intake_cycle()
            self.assertIn("cycle", result)
            self.assertIn("sources_reached", result)
            self.assertIn("patterns_found", result)
            self.assertIn("correlations", result)
            self.assertIn("timestamp", result)

            stats = core.get_stats()
            self.assertIn("cycle_interval", stats)
            self.assertIn("sources", stats)

        asyncio.run(run_test())

    def test_announcement_layers_work(self):
        core = MaliCore()
        item = core.announcements.announce(
            AnnouncementType.INSIGHT,
            AnnouncementPriority.MEDIUM,
            "Pattern test",
            "A small signal was accepted.",
            "unit-test",
            {"kind": "test"},
        )
        self.assertEqual(item.title, "Pattern test")
        self.assertFalse(item.acknowledged)


if __name__ == "__main__":
    unittest.main()
