import unittest
from scripts.check_service_levels import evaluate

POLICY={"slo":{"p95_latency_ns_max":100,"error_rate_max":0.0,"provenance_coverage_min":1.0},"sla":{"status":"not_offered"},"cd":{"status":"not_configured"}}
class ServiceLevelTests(unittest.TestCase):
    def test_passing_measurement(self):
        report=evaluate({"iterations":10,"errors":0,"provenance_tagged":10,"latency_ns":{"p95":90}},POLICY)
        self.assertTrue(report["passed"]);self.assertEqual(report["cd"]["status"],"not_configured")
    def test_latency_failure_is_not_hidden(self):
        self.assertFalse(evaluate({"iterations":10,"errors":0,"provenance_tagged":10,"latency_ns":{"p95":101}},POLICY)["passed"])
if __name__=="__main__":unittest.main()
