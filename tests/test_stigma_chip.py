import unittest

from neuclx.evidence import EvidenceState
from neuclx.stigma_chip import (
    MASK,
    MOMENTUM_BOOT,
    VDPA_INIT,
    StigmaCore,
    memory_step,
    momentum_step,
    vdpa_step,
)


class StigmaChipModelTests(unittest.TestCase):
    def test_memory_is_seven_eighths_iir(self):
        self.assertEqual(memory_step(0, 8_000), 1_000)
        self.assertEqual(memory_step(8_000, 8_000), (56_000 + 8_000) >> 3)

    def test_memory_converges_to_constant_input_from_below(self):
        mem, ndb = 0, 0xD9999999
        for _ in range(256):
            mem = memory_step(mem, ndb)
        self.assertLessEqual(mem, ndb)
        self.assertGreater(mem, ndb - 8)

    def test_momentum_wraps_when_memory_decreases(self):
        self.assertEqual(momentum_step(10, 4), 6)
        self.assertEqual(momentum_step(4, 10), (4 - 10) & MASK)

    def test_wrapped_momentum_floors_denominator_to_epsilon(self):
        wrapped = momentum_step(4, 10)
        value = vdpa_step(0xD9999999, wrapped, 0xFFFF0000)
        self.assertEqual(value, vdpa_step(0xD9999999, wrapped, 0xFFFF0000))
        self.assertGreater(value, vdpa_step(0xD9999999, 0, 0xFFFF0000))

    def test_vdpa_grows_with_momentum(self):
        low = vdpa_step(0xD9999999, 0, 0xFFFF0000)
        high = vdpa_step(0xD9999999, 1 << 31, 0xFFFF0000)
        self.assertEqual(high, low * 2)

    def test_reset_state_and_registered_pipeline(self):
        core = StigmaCore()
        self.assertEqual((core.mem, core.momentum, core.v_dpa), (0, MOMENTUM_BOOT, VDPA_INIT))
        core.clock(8_000)
        self.assertEqual(core.mem, 1_000)
        self.assertEqual(core.momentum, 0)
        core.clock(8_000)
        self.assertEqual(core.momentum, 1_000)

    def test_datum_declares_no_hardware_claim(self):
        datum = StigmaCore().clock(8_000).datum()
        self.assertEqual(datum.state, EvidenceState.COMPUTED)
        self.assertEqual(datum.metadata["hardware_speed"], "not_implemented")
        self.assertIn("not an RTL simulation", datum.method)


if __name__ == "__main__":
    unittest.main()
