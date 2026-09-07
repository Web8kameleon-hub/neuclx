"""Simple real agents for bridging user questions to NeuCLX policy and runtime facts."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AgentAnswer:
    text: str


class AlbaAgent:
    """Bridge-oriented agent for repository and manifest questions."""

    def answer(self, question: str) -> str:
        q = (question or "").lower()
        if "bridge" in q or "manifest" in q:
            return (
                "Bridge është shtresa e verifikimit të burimeve: ajo ruan manifestin, kontrollon "
                "hash-in, e vërteton evidencën dhe e kalon përmes JONA."
            )
        if "ui" in q or "frontend" in q:
            return "NeuCLX ka një UI të thjeshtë bazuar në server HTTP dhe një app.js të lidhur me /api/respond."
        return "Bridge është pjesa që verifikon burimin, manifestin dhe evidencën përpara se të hyjë në kernel."


class AlbiAgent:
    """Runtime-oriented agent for runtime and memory questions."""

    def answer(self, question: str) -> str:
        q = (question or "").lower()
        if "ui" in q or "frontend" in q:
            return "Po, ekziston UI në src/neuclx/static me index.html, app.js dhe app.css, dhe aplikacioni ka endpoint /api/respond. Memory është reale dhe përdor SQLite me shënime të verifikuara."
        if "memory" in q:
            return "Memory është reale dhe përdor SQLite me vetëm shënime të verifikuara me state measured/computed."
        if "bridge" in q:
            return "Bridge është shtresa për manifest dhe verifikim të burimit; Albi fokusohet te runtime dhe memory."
        return "NeuCLX ka një runtime real, memory SQLite dhe një UI të thjeshtë, por pa fallback të fshehur."


class JonaAgent:
    """Policy agent that explains the JONA sandbox boundary."""

    def answer(self, question: str) -> str:
        q = (question or "").lower()
        if "sandbox" in q or "policy" in q or "jona" in q:
            return "JONA është sandbox-i obligues i sigurisë dhe policy-ja e kufirit: ai e vlerëson çdo datum para lëshimit dhe ndalon të dhëna të padëshiruara ose jo të verifikuara."
        return "JONA është sandbox-i dhe policy-ja e kufirit të NeuCLX: çdo dalje duhet të kalojë kontrollin e evidencës."
