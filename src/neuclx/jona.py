from dataclasses import dataclass
from enum import StrEnum

from .evidence import Datum, EvidenceState


class PolicyDecision(StrEnum):
    ALLOW = "allow"
    SANDBOX_ONLY = "sandbox_only"
    REJECT = "reject"


@dataclass(frozen=True, slots=True)
class JonaSandbox:
    """The single mandatory boundary for NeuCLX output."""

    def evaluate(self, datum: Datum) -> PolicyDecision:
        if datum.state in {EvidenceState.UNAVAILABLE, EvidenceState.NOT_IMPLEMENTED}:
            return PolicyDecision.SANDBOX_ONLY
        if datum.state is EvidenceState.MEASURED and datum.source and datum.method:
            return PolicyDecision.ALLOW
        if datum.state is EvidenceState.COMPUTED and datum.method:
            return PolicyDecision.ALLOW
        if datum.state is EvidenceState.DECLARED:
            return PolicyDecision.SANDBOX_ONLY
        return PolicyDecision.REJECT

    def release(self, datum: Datum) -> Datum:
        decision = self.evaluate(datum)
        if decision is PolicyDecision.REJECT:
            raise PermissionError("JONA rejected datum")
        return datum

