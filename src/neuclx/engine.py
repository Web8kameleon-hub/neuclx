"""Deterministic cognitive-cell engine; no external model or network fallback."""

from dataclasses import dataclass, field
from hashlib import sha256
from typing import Any

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
        axes: tuple[Axis, ...] = tuple(Axis)
        for index, token in enumerate(tokens):
            axis = Axis(axes[index % len(axes)])
            activation = int.from_bytes(sha256(token.encode()).digest()[:2], "big") / 65535
            self.lattice.set(CognitiveCell(index % self.layers, axis, index, activation))
        return self.sandbox.release(
            Datum(
                {"digest": digest, "tokens": len(tokens)},
                EvidenceState.MEASURED,
                source=source,
                method="sha256+deterministic-tokenization",
                metadata={"axes": [str(axis) for axis in Axis], "token_count": len(tokens)},
            )
        )

    def answer(self, query: str) -> Datum:
        wanted = set(self._tokens(query))
        if not self.knowledge:
            return self.sandbox.release(Datum(None, EvidenceState.UNAVAILABLE, method="knowledge-store-empty", metadata={"evidence_chain": []}))
        ranked = []
        for digest, tokens in self.knowledge.items():
            overlap = len(wanted.intersection(tokens))
            ranked.append((overlap, digest, tokens))
        overlap, digest, tokens = max(ranked, key=lambda row: (row[0], row[1]))
        if overlap == 0:
            return self.sandbox.release(Datum(None, EvidenceState.UNAVAILABLE, method="zero-token-overlap", metadata={"evidence_chain": []}))
        matching_terms = sorted(wanted.intersection(tokens))
        score = overlap / max(1, len(wanted))
        return self.sandbox.release(
            Datum(
                {"source_digest": digest, "matching_terms": matching_terms, "score": score},
                EvidenceState.COMPUTED,
                method="deterministic-token-overlap",
                metadata={"evidence_chain": [{"source_digest": digest, "matching_terms": matching_terms, "score": score}]},
            )
        )

    def external_llm(self, *_args, **_kwargs) -> Datum:
        return self.sandbox.release(Datum(None, EvidenceState.NOT_IMPLEMENTED, method="external-models-forbidden"))


@dataclass(slots=True)
class ReasoningPipeline:
    kernel: CognitiveKernel = field(default_factory=CognitiveKernel)

    @staticmethod
    def _normalize(question: str) -> str:
        return " ".join(word.strip(".,:;!?()[]{}\"'") for word in (question or "").split() if word.strip(".,:;!?()[]{}\"'"))

    @staticmethod
    def _choose_agent(question: str, facts: list[str]) -> str:
        text = (question or "") + " " + " ".join(facts or [])
        lowered = text.casefold()
        if any(token in lowered for token in ["jona", "sandbox", "policy", "security", "governance"]):
            return "jona"
        if any(token in lowered for token in ["bridge", "manifest", "source", "evidence", "hash"]):
            return "alba"
        if any(token in lowered for token in ["ui", "frontend", "memory", "runtime", "database", "sqlite"]):
            return "albi"
        return "alba"

    @staticmethod
    def _build_answer(question: str, facts: list[str], state: EvidenceState) -> str:
        lowered = (question or "").casefold()
        if "jona" in lowered or "sandbox" in lowered or "policy" in lowered:
            if any("sandbox" in fact.casefold() for fact in facts):
                return "JONA është kufiri i policy-s dhe sandbox-it: ai rregullon çfarë lejohet të dalë nga sistemi dhe ndalon të dhëna të pa-verifikuara."
            return "JONA është kufiri i sigurisë së NeuCLX: çdo dalje duhet të kalojë kontrollin e evidencës dhe policy-s."
        if "bridge" in lowered or "manifest" in lowered or "evidence" in lowered:
            return "Bridge e kontrollon burimin, manifestin dhe evidencën përpara se të hyjë në kernel; kjo e bën rrjedhën e vendimeve të verifikueshme."
        if "ui" in lowered or "frontend" in lowered or "memory" in lowered:
            return "NeuCLX ka një UI të thjeshtë dhe memory reale në SQLite, me të dhëna të ruajtura vetëm kur janë measured ose computed."
        if state is EvidenceState.UNAVAILABLE:
            return "Nuk ka pasur mbivendosje të qartë midis pyetjes dhe evidencës së ruajtur; kërkesa mbetet e pa-verifikuar."
        if facts:
            return "Rrjedha e arsyetimit bazon përgjigjen në përputhje me faktet e dhëna dhe në kontrollin e evidencës së vetme."
        return "Përgjigja është e bazuar në verifikimin e hapave të rrjedhës: nxjerrja, përshtatja dhe kontrolli i JONA."

    def run(self, question: str, facts: list[str] | None = None, *, context: dict[str, Any] | None = None) -> dict[str, Any]:
        cleaned_question = self._normalize(question)
        fact_list = [fact.strip() for fact in (facts or []) if isinstance(fact, str) and fact.strip()]
        context = context or {}
        steps: list[dict[str, Any]] = [
            {"step": "normalize", "question": cleaned_question, "status": "ok"},
        ]

        for fact in fact_list:
            self.kernel.ingest("reasoning:pipeline", fact)
            steps.append({"step": "ingest_fact", "fact": fact, "status": "ok"})

        evidence = self.kernel.answer(cleaned_question)
        steps.append({"step": "kernel_match", "state": evidence.state.value, "value": evidence.value, "method": evidence.method})

        agent_name = self._choose_agent(cleaned_question, fact_list)
        answer = self._build_answer(cleaned_question, fact_list, evidence.state)

        if context.get("require_jona_gate"):
            gate = self.kernel.sandbox.evaluate(Datum(answer, EvidenceState.COMPUTED, source="pipeline", method="reasoning_pipeline"))
            steps.append({"step": "jona_gate", "decision": gate.value})

        return {
            "pipeline": "reasoning",
            "agent": agent_name,
            "question": cleaned_question,
            "state": evidence.state.value,
            "answer": answer,
            "facts": fact_list,
            "steps": steps,
            "evidence": evidence.value,
        }

