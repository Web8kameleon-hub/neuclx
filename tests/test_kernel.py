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
        self.assertIn("evidence_chain", answer.metadata)
        self.assertEqual(answer.metadata["evidence_chain"][0]["matching_terms"], ["cells", "sovereign"])

    def test_hvo_has_extended_dimensions(self):
        from neuclx.hvwo import Axis

        axes = tuple(Axis)
        self.assertIn(Axis.TIME, axes)
        self.assertIn(Axis.SPACE, axes)
        self.assertIn(Axis.AUTHOR, axes)

    def test_no_external_llm_fallback(self):
        self.assertEqual(CognitiveKernel().external_llm("hello").state, EvidenceState.NOT_IMPLEMENTED)


if __name__ == "__main__":
    unittest.main()

