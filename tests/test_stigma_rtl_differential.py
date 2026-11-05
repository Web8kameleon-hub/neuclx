"""Differential test: OS-CLX RTL (Icarus Verilog) vs the Python model, cycle by cycle.

Skipped, never faked, when Icarus Verilog or the RTL file is unavailable. The RTL lives in
the private OS-CLX repo and is not vendored: point NEUCLX_STIGMA_RTL at a local copy of
docs/hardware/stigma_center_core.v. The testbench compiles with `-g2012` because the
RTL uses unpacked-array ports.
"""

import os
import random
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from neuclx.stigma_chip import MASK, MOMENTUM_BOOT, VDPA_INIT, StigmaCore

TB = Path(__file__).parent / "rtl" / "stigma_core_tb.v"
RTL = os.environ.get("NEUCLX_STIGMA_RTL", "")
IVERILOG = shutil.which("iverilog") or str(Path(os.environ.get("ChocolateyInstall", r"C:\ProgramData\chocolatey")) / "bin" / "iverilog.exe")
VVP = shutil.which("vvp") or str(Path(IVERILOG).with_name("vvp.exe"))


def stimulus(seed: int, cycles: int) -> list[tuple[int, int]]:
    rng = random.Random(seed)
    rows = [(0xD9999999, 0xFFFF0000), (0xD9999999, 0xFFFF0000), (0, 0)]
    for _ in range(cycles - len(rows)):
        kind = rng.randrange(4)
        ndb = rng.getrandbits(32) if kind == 0 else rng.getrandbits(64) if kind == 1 else rng.choice((0, 1, 0xD9999999, MASK))
        rows.append((ndb, rng.getrandbits(64)))
    return rows


@unittest.skipUnless(
    RTL and Path(RTL).is_file() and Path(IVERILOG).is_file() and Path(VVP).is_file(),
    "Icarus Verilog or NEUCLX_STIGMA_RTL not available",
)
class StigmaRtlDifferentialTests(unittest.TestCase):
    def run_rtl(self, rows):
        with tempfile.TemporaryDirectory() as tmp:
            stim = Path(tmp) / "stim.hex"
            stim.write_text("".join(f"{ndb:016x}{wave:016x}\n" for ndb, wave in rows))
            vvp = Path(tmp) / "tb.vvp"
            subprocess.run([IVERILOG, "-g2012", "-o", str(vvp), str(TB), RTL], check=True, capture_output=True, text=True)
            out = subprocess.run([VVP, str(vvp), f"+stim={stim}", f"+n={len(rows)}"], check=True, capture_output=True, text=True).stdout
        return [line.split() for line in out.splitlines() if line.startswith("RESET") or len(line.split()) == 3 and not line.startswith("WARNING")]

    def test_reset_state_matches_model(self):
        lines = self.run_rtl(stimulus(1, 3))
        self.assertEqual(lines[0], ["RESET", "0000000000000000", f"{MOMENTUM_BOOT:016x}", f"{VDPA_INIT:016x}"])

    def test_every_cycle_matches_model(self):
        for seed in (1, 2, 3):
            rows = stimulus(seed, 400)
            lines = self.run_rtl(rows)[1:]
            self.assertEqual(len(lines), len(rows))
            core = StigmaCore()
            for cycle, ((ndb, wave), got) in enumerate(zip(rows, lines)):
                core.clock(ndb, wave)
                want = [f"{core.mem:016x}", f"{core.momentum:016x}", f"{core.v_dpa:016x}"]
                self.assertEqual(got, want, f"seed {seed} cycle {cycle}")


if __name__ == "__main__":
    unittest.main()
