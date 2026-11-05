"""Bit-exact software model of the OS-CLX Stigma Center Core datapath.

This models the integer semantics declared in OS-CLX `docs/hardware/stigma_center_core.v`
(memory accumulator, momentum engine, V_dpa unit) on unsigned 64-bit words. It is a
computed software model of a declared design. It is NOT a simulation of the RTL, and it
says nothing about silicon speed, power or area: those are `not_implemented` until the
RTL is simulated or synthesised with a real tool.
"""

from __future__ import annotations

from dataclasses import dataclass

from .evidence import Datum, EvidenceState

WIDTH = 64
MASK = (1 << WIDTH) - 1
ONE_Q32 = 1 << 32
MOMENTUM_BOOT = 0x00000000_10B02010
CENTER_HZ_FX = 0x00000132_FFFE3B9A
VDPA_INIT = 0x00000055_97AE147B
SOURCE = "os-clx:docs/hardware/stigma_center_core.v@2026-05-29 (declared)"


def memory_step(mem: int, ndb: int) -> int:
    """mem' = (7*mem + ndb) >> 3, truncated to 64 bits as in the RTL register."""
    return (((mem * 7) + ndb) & MASK) >> 3


def momentum_step(mem: int, mem_prev: int) -> int:
    """momentum = mem - mem_prev modulo 2**64 (wraps when memory decreases)."""
    return (mem - mem_prev) & MASK


def vdpa_step(ndb: int, momentum: int, wave: int) -> int:
    amp = (wave >> 16) & 0xFFFF
    numerator = ((CENTER_HZ_FX >> 16) * (amp >> 8) * (ndb >> 24)) & MASK
    denom = (ONE_Q32 - momentum) if momentum < ONE_Q32 else 1
    return numerator // denom if denom else VDPA_INIT


@dataclass
class StigmaCore:
    mem: int = 0
    mem_prev: int = 0
    momentum: int = MOMENTUM_BOOT
    v_dpa: int = VDPA_INIT

    def clock(self, ndb: int, wave: int = 0) -> "StigmaCore":
        """One clock edge. Non-blocking assignments: every stage reads the old state."""
        ndb &= MASK
        old_mem, old_momentum = self.mem, self.momentum
        self.v_dpa = vdpa_step(ndb, old_momentum, wave)
        self.momentum = momentum_step(old_mem, self.mem_prev)
        self.mem_prev = old_mem
        self.mem = memory_step(old_mem, ndb)
        return self

    def datum(self) -> Datum:
        return Datum(
            {"mem": self.mem, "momentum": self.momentum, "v_dpa": self.v_dpa},
            EvidenceState.COMPUTED,
            source=SOURCE,
            method="bit-exact uint64 software model; not an RTL simulation",
            metadata={"hardware_speed": "not_implemented", "silicon": "not_implemented"},
        )
