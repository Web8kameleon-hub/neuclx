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

    def test_unavailable_and_not_implemented_are_not_public_output(self):
        unavailable = Datum(None, EvidenceState.UNAVAILABLE, method="knowledge-store-empty")
        not_impl = Datum(None, EvidenceState.NOT_IMPLEMENTED, method="external-models-forbidden")
        self.assertEqual(JonaSandbox().evaluate(unavailable), PolicyDecision.SANDBOX_ONLY)
        self.assertEqual(JonaSandbox().evaluate(not_impl), PolicyDecision.SANDBOX_ONLY)

    def test_multilayer_hvwo_algebra(self):
        lattice = HVWOLattice(3)
        lattice.set(CognitiveCell(0, Axis.HORIZONTAL, 0, 0.5))
        lattice.set(CognitiveCell(2, Axis.VERTICAL, 0, 0.25))
        self.assertEqual(lattice.contract([Axis.HORIZONTAL, Axis.VERTICAL]), 0.75)
        self.assertEqual(len(lattice.wave_transform(0.2).project(Axis.WAVE)), 2)

    def test_directional_derivative_opposite_directions(self):
        lat_up = HVWOLattice(1)
        for i in range(5):
            lat_up.set(CognitiveCell(0, Axis.VERTICAL, i, float(i)))
        d_up = lat_up.directional_derivative(Axis.VERTICAL, 0)

        lat_down = HVWOLattice(1)
        for i in range(5):
            lat_down.set(CognitiveCell(0, Axis.VERTICAL, i, float(4 - i)))
        d_down = lat_down.directional_derivative(Axis.VERTICAL, 0)

        self.assertLess(d_up * d_down, 0, "drejtimet duhet të jenë të kundërta")
        self.assertGreater(d_up, 0, "lart duhet të jetë pozitiv")
        self.assertLess(d_down, 0, "poshtë duhet të jetë negativ")

    def test_directional_derivative_single_cell_returns_zero(self):
        lat = HVWOLattice(1)
        lat.set(CognitiveCell(0, Axis.VERTICAL, 0, 1.0))
        self.assertEqual(lat.directional_derivative(Axis.VERTICAL, 0), 0.0)


if __name__ == "__main__":
    unittest.main()
