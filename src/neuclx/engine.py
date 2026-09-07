"""Deterministic cognitive-cell engine; no external model or network fallback."""

from dataclasses import dataclass, field
from hashlib import sha256
from .evidence import Datum, EvidenceState
from .hvwo import Axis, CognitiveCell, HVWOLattice
from .jona import JonaSandbox


@dataclass(slots=True)
class CognitiveKernel:
    layers: int = 4
    sandbox: JonaSandbox = field(default_factory=JonaSandbox)
    lattice: HVWOLattice = field(init=False)
    knowledge: dict[str, tuple[str, ...]] = field(default_factory=dict)

    def __post_init__(self):
        self.lattice = HVWOLattice(self.layers)

    @staticmethod
    def _tokens(text: str) -> tuple[str, ...]:
        return tuple(word.strip(".,:;!?()[]{}\"'").casefold() for word in text.split() if word.strip(".,:;!?()[]{}\"'"))

    def ingest(self, source: str, text: str) -> Datum:
        tokens = self._tokens(text)
        digest = sha256(text.encode()).hexdigest()
        self.knowledge[digest] = tokens
        axes = tuple(Axis)
        for index, token in enumerate(tokens):
            axis = axes[index % len(axes)]
            activation = int.from_bytes(sha256(token.encode()).digest()[:2], "big") / 65535
            self.lattice.set(CognitiveCell(index % self.layers, axis, index, activation))
        return self.sandbox.release(Datum({"digest": digest, "tokens": len(tokens)}, EvidenceState.MEASURED, source=source, method="sha256+deterministic-tokenization"))

    def answer(self, query: str) -> Datum:
        wanted = set(self._tokens(query))
        if not self.knowledge:
            return self.sandbox.release(Datum(None, EvidenceState.UNAVAILABLE, method="knowledge-store-empty"))
        ranked = []
        for digest, tokens in self.knowledge.items():
            overlap = len(wanted.intersection(tokens))
            ranked.append((overlap, digest, tokens))
        overlap, digest, tokens = max(ranked, key=lambda row: (row[0], row[1]))
        if overlap == 0:
            return self.sandbox.release(Datum(None, EvidenceState.UNAVAILABLE, method="zero-token-overlap"))
        return self.sandbox.release(Datum({"source_digest": digest, "matching_terms": sorted(wanted.intersection(tokens)), "score": overlap / max(1, len(wanted))}, EvidenceState.COMPUTED, method="deterministic-token-overlap"))

    def external_llm(self, *_args, **_kwargs) -> Datum:
        return self.sandbox.release(Datum(None, EvidenceState.NOT_IMPLEMENTED, method="external-models-forbidden"))

