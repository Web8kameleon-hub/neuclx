"""Sparse HVWO algebra.

HVWO is implemented here as a declared NeuCLX extension of verified HVO/HVOW
ideas. JP/JL and VP/VL are paired directional operators; WAVE carries phase.
No claim is made that these names were implemented in a source repository.
"""

from dataclasses import dataclass, field
from enum import StrEnum
from math import cos, sin
from typing import Iterable


class Axis(StrEnum):
    HORIZONTAL = "H"
    VERTICAL = "V"
    JP = "JP"
    JL = "JL"
    VP = "VP"
    VL = "VL"
    WAVE = "W"
    TIME = "T"
    SPACE = "S"
    AUTHOR = "A"


@dataclass(frozen=True, slots=True)
class CognitiveCell:
    layer: int
    axis: Axis
    coordinate: int
    activation: float
    phase: float = 0.0


@dataclass(slots=True)
class HVWOLattice:
    layers: int
    cells: dict[tuple[int, Axis, int], CognitiveCell] = field(default_factory=dict)

    def __post_init__(self):
        if self.layers < 1:
            raise ValueError("layers must be positive")

    def set(self, cell: CognitiveCell):
        if not 0 <= cell.layer < self.layers:
            raise ValueError("cell layer outside lattice")
        self.cells[(cell.layer, cell.axis, cell.coordinate)] = cell

    def project(self, axis: Axis, layer: int | None = None) -> tuple[float, ...]:
        selected = [c for c in self.cells.values() if c.axis is axis and (layer is None or c.layer == layer)]
        return tuple(c.activation for c in sorted(selected, key=lambda c: (c.layer, c.coordinate)))

    def wave_transform(self, frequency: float) -> "HVWOLattice":
        out = HVWOLattice(self.layers)
        for cell in self.cells.values():
            phase = cell.phase + frequency * (cell.layer + 1)
            amplitude = cell.activation * cos(phase) + cell.activation * sin(phase)
            out.set(CognitiveCell(cell.layer, Axis.WAVE, cell.coordinate, amplitude, phase))
        return out

    def contract(self, axes: Iterable[Axis]) -> float:
        allowed = frozenset(axes)
        return sum(c.activation for c in self.cells.values() if c.axis in allowed)

