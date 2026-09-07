import unittest
from neuclx import CognitiveKernel, EvidenceState


class KernelTests(unittest.TestCase):
    def test_empty_store_reports_unavailable(self):
        self.assertEqual(CognitiveKernel().answer("unknown").state, EvidenceState.UNAVAILABLE)

    def test_ingest_and_answer_are_evidence_bound(self):
        kernel = CognitiveKernel()
        receipt = kernel.ingest("test:fixture", "NeuCLX uses sovereign cognitive cells")
        answer = kernel.answer("sovereign cells")
        self.assertEqual(receipt.state, EvidenceState.MEASURED)
        self.assertEqual(answer.state, EvidenceState.COMPUTED)
        self.assertEqual(answer.value["matching_terms"], ["cells", "sovereign"])

    def test_no_external_llm_fallback(self):
        self.assertEqual(CognitiveKernel().external_llm("hello").state, EvidenceState.NOT_IMPLEMENTED)


if __name__ == "__main__":
    unittest.main()

