from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any, Mapping


class EvidenceState(StrEnum):
    MEASURED = "measured"
    COMPUTED = "computed"
    DECLARED = "declared"
    UNAVAILABLE = "unavailable"
    NOT_IMPLEMENTED = "not_implemented"


@dataclass(frozen=True, slots=True)
class Datum:
    value: Any
    state: EvidenceState
    source: str | None = None
    method: str | None = None
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if self.state in {EvidenceState.MEASURED, EvidenceState.COMPUTED} and not self.method:
            raise ValueError(f"{self.state} data requires a method")
        if self.state is EvidenceState.MEASURED and not self.source:
            raise ValueError("measured data requires a source")
        if self.state in {EvidenceState.UNAVAILABLE, EvidenceState.NOT_IMPLEMENTED} and self.value is not None:
            raise ValueError(f"{self.state} data must have value=None")

    def as_dict(self):
        return {"value": self.value, "state": self.state.value, "source": self.source, "method": self.method, "metadata": dict(self.metadata)}

