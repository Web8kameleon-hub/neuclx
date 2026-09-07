import unittest
from neuclx import Axis, CognitiveCell, Datum, EvidenceState, HVWOLattice, JonaSandbox, PolicyDecision


class ContractTests(unittest.TestCase):
    def test_measured_requires_source_and_method(self):
        with self.assertRaises(ValueError):
            Datum(1, EvidenceState.MEASURED, method="meter")

    def test_missing_state_cannot_carry_fake_value(self):
        with self.assertRaises(ValueError):
            Datum(42, EvidenceState.UNAVAILABLE, method="none")

    def test_declared_is_sandbox_only(self):
        datum = Datum("beyond frontier models", EvidenceState.DECLARED)
        self.assertEqual(JonaSandbox().evaluate(datum), PolicyDecision.SANDBOX_ONLY)

    def test_multilayer_hvwo_algebra(self):
        lattice = HVWOLattice(3)
        lattice.set(CognitiveCell(0, Axis.HORIZONTAL, 0, 0.5))
        lattice.set(CognitiveCell(2, Axis.VERTICAL, 0, 0.25))
        self.assertEqual(lattice.contract([Axis.HORIZONTAL, Axis.VERTICAL]), 0.75)
        self.assertEqual(len(lattice.wave_transform(0.2).project(Axis.WAVE)), 2)


if __name__ == "__main__":
    unittest.main()

