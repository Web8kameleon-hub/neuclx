import unittest
from benchmarks.kernel_benchmark import run

class BenchmarkTests(unittest.TestCase):
    def test_benchmark_reports_measurement_not_claim(self):
        result=run(20)
        self.assertEqual(result["state"],"measured")
        self.assertEqual(result["result_state"],"computed")
        self.assertGreater(result["latency_ns"]["median"],0)
if __name__=="__main__":unittest.main()
