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

from neuclx.stigma_chip import (
    CENTER_HZ_FX,
    MASK,
    MOMENTUM_BOOT,
    VDPA_INIT,
    StigmaCore,
    memory_step,
    momentum_step,
    vdpa_step,
)

TB = Path(__file__).parent / "rtl" / "stigma_core_tb.v"
RTL = os.environ.get("NEUCLX_STIGMA_RTL", "")
IVERILOG = shutil.which("iverilog") or str(
    Path(os.environ.get("ChocolateyInstall", r"C:\ProgramData\chocolatey")) / "bin" / "iverilog.exe"
)
VVP = shutil.which("vvp") or str(Path(IVERILOG).with_name("vvp.exe"))


def stimulus(seed: int, cycles: int) -> list[tuple[int, int]]:
    rng = random.Random(seed)
    rows = [(0xD9999999, 0xFFFF0000), (0xD9999999, 0xFFFF0000), (0, 0)]
    for _ in range(cycles - len(rows)):
        kind = rng.randrange(4)
        ndb = (
            rng.getrandbits(32)
            if kind == 0
            else rng.getrandbits(64) if kind == 1 else rng.choice((0, 1, 0xD9999999, MASK))
        )
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
            subprocess.run(
                [IVERILOG, "-g2012", "-o", str(vvp), str(TB), RTL], check=True, capture_output=True, text=True
            )
            out = subprocess.run(
                [VVP, str(vvp), f"+stim={stim}", f"+n={len(rows)}"], check=True, capture_output=True, text=True
            ).stdout
        return [
            line.split()
            for line in out.splitlines()
            if line.startswith("RESET") or len(line.split()) == 3 and not line.startswith("WARNING")
        ]

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


TOP_TB = Path(__file__).parent / "rtl" / "stigma_top_tb.v"
NDB_SCORE = 0x00000000_D9999999
CENTER_FREQ = (CENTER_HZ_FX >> 16) & 0xFFFFFFFF
CENTER_EPS = 0x8000


def top_stimulus(seed: int, cycles: int) -> list[tuple[int, int]]:
    rng = random.Random(seed)
    center_wave = (CENTER_FREQ << 32) | (0xFFFF << 16) | 0x1234
    outside_wave = ((CENTER_FREQ + 0x10000) << 32) | (0xFFFF << 16)
    rows = [
        (0xFF, center_wave),
        (0xFF, outside_wave),
        (0xFF, (CENTER_FREQ << 32) | 0x1234),
        (0x01, center_wave),
        (0x00, center_wave),
        (0xFF, center_wave),
    ]
    for _ in range(cycles - len(rows)):
        valid = rng.choice((0x00, 0x01, 0x03, 0x55, 0xFF))
        freq = rng.choice((CENTER_FREQ, CENTER_FREQ + 0x10000, 0, 0xFFFFFFFF))
        amp = rng.choice((0, 1, 0x7FFF, 0xFFFF))
        phase = rng.getrandbits(16)
        rows.append((valid, (freq << 32) | (amp << 16) | phase))
    return rows


class StigmaTopReference:
    """Test oracle for the RTL top-level registered pipeline."""

    def __init__(self):
        self.aggregate = 0
        self.ndb_score = NDB_SCORE
        self.mem = 0
        self.mem_prev = 0
        self.momentum = MOMENTUM_BOOT
        self.v_dpa = VDPA_INIT

    @staticmethod
    def gated(aggregate):
        freq = (aggregate >> 32) & 0xFFFFFFFF
        center = (CENTER_HZ_FX >> 16) & 0xFFFFFFFF
        diff = abs(freq - center)
        return (aggregate if diff <= CENTER_EPS else 0), diff

    def outputs(self):
        gated, diff = self.gated(self.aggregate)
        gate_pass = gated != 0
        resonant = gate_pass and self.ndb_score >= 0xC0000000
        if not gate_pass or self.v_dpa < (20 << 32):
            load_band = 0
        elif self.v_dpa < (50 << 32):
            load_band = 1
        elif self.v_dpa < (100 << 32):
            load_band = 2
        else:
            load_band = 3
        return [
            f"{self.mem:016x}",
            f"{self.momentum:016x}",
            f"{self.v_dpa:016x}",
            f"{int(gate_pass):x}",
            f"{(diff << 16) & MASK:016x}",
            f"{int(resonant):x}",
            f"{load_band:02x}",
            "ff",
            *([f"{NDB_SCORE:016x}"] * 8),
        ]

    def clock(self, valid, wave):
        gated, _ = self.gated(self.aggregate)
        old_ndb, old_mem, old_momentum = self.ndb_score, self.mem, self.momentum
        old_mem_prev = self.mem_prev
        self.v_dpa = vdpa_step(old_ndb, old_momentum, gated)
        self.momentum = momentum_step(old_mem, old_mem_prev)
        self.mem_prev = old_mem
        self.mem = memory_step(old_mem, old_ndb)
        self.ndb_score = NDB_SCORE if ((gated >> 16) & 0xFFFF) else 0

        count = valid.bit_count()
        if count:
            self.aggregate = ((wave * count) & MASK) >> 3


@unittest.skipUnless(
    RTL and Path(RTL).is_file() and Path(IVERILOG).is_file() and Path(VVP).is_file(),
    "Icarus Verilog or NEUCLX_STIGMA_RTL not available",
)
class StigmaTopRtlDifferentialTests(unittest.TestCase):
    def run_top(self, rows):
        with tempfile.TemporaryDirectory() as tmp:
            stim = Path(tmp) / "stim.hex"
            stim.write_text("".join(f"{valid:02x}{wave:016x}\n" for valid, wave in rows))
            vvp = Path(tmp) / "top.vvp"
            subprocess.run(
                [IVERILOG, "-g2012", "-o", str(vvp), str(TOP_TB), RTL],
                check=True,
                capture_output=True,
                text=True,
            )
            out = subprocess.run(
                [VVP, str(vvp), f"+stim={stim}", f"+n={len(rows)}"],
                check=True,
                capture_output=True,
                text=True,
            ).stdout
        return [line.split()[1:] for line in out.splitlines() if line.startswith("OUT ")]

    def test_top_reset_outputs_match_reference(self):
        got = self.run_top(top_stimulus(1, 1))[0]
        want = StigmaTopReference().outputs()
        self.assertEqual(got, want)

    def test_every_top_output_matches_registered_pipeline(self):
        rows = top_stimulus(731, 500)
        lines = self.run_top(rows)
        self.assertEqual(len(lines), len(rows) + 1)
        model = StigmaTopReference()
        self.assertEqual(lines[0], model.outputs())
        for cycle, ((valid, wave), got) in enumerate(zip(rows, lines[1:])):
            model.clock(valid, wave)
            self.assertEqual(got, model.outputs(), f"top-level cycle {cycle}")


if __name__ == "__main__":
    unittest.main()
