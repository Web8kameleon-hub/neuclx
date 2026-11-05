"""Source-bound answers: every kept sentence must cite a supplied source.

The model receives only numbered excerpts and is told to cite them as [n]. The
output is then checked deterministically: a sentence is kept only when it cites a
valid source number and shares enough terms with that excerpt. Everything else is
refused and reported. Term overlap is a computed filter, not a proof of truth.
"""

from __future__ import annotations

import re

from .evidence import Datum, EvidenceState
from .learning import term_tokens

MIN_SENTENCE_OVERLAP = 0.3
CITATION_INSTRUCTION = (
    "Answer ONLY from the numbered sources in reference_context. End every factual "
    "sentence with the number of the supporting source in square brackets, e.g. [1]. "
    "Do not state anything the sources do not contain. If the sources do not answer "
    "the question, reply exactly: NO_SOURCE_ANSWER"
)
REFUSAL = "Nuk ka burim të mjaftueshëm për të përgjigjur; pohimet pa burim refuzohen."

_CITE = re.compile(r"\[(\d{1,2})\]")
_SPLIT = re.compile(r"(?<=[.!?])\s+")


def numbered_context(hits) -> list[str]:
    return [
        f"[{index}] {hit['source']} @ {hit['revision']}:{hit['line']}\n{hit['excerpt']}"
        for index, hit in enumerate(hits, start=1)
    ]


def refusal(reason: str) -> Datum:
    return Datum(
        None,
        EvidenceState.UNAVAILABLE,
        source="neuclx:cited-answer",
        method="citation-enforcement",
        metadata={"reason": reason, "message": REFUSAL, "kept_sentences": 0, "refused_sentences": []},
    )


def enforce(answer_text: str, hits) -> Datum:
    if not hits:
        return refusal("no retrieved source")
    text = (answer_text or "").strip()
    if not text or "NO_SOURCE_ANSWER" in text:
        return refusal("model reported no supporting source")
    kept, refused = [], []
    for sentence in _SPLIT.split(text):
        sentence = sentence.strip()
        if not sentence:
            continue
        numbers = [int(n) for n in _CITE.findall(sentence)]
        valid = [n for n in numbers if 1 <= n <= len(hits)]
        body_terms = set(term_tokens(_CITE.sub("", sentence)))
        if not valid:
            refused.append({"sentence": sentence, "why": "no valid citation"})
            continue
        best = max(
            len(body_terms & set(term_tokens(hits[n - 1]["excerpt"]))) / len(body_terms) if body_terms else 0.0
            for n in valid
        )
        if best < MIN_SENTENCE_OVERLAP:
            refused.append({"sentence": sentence, "why": f"overlap {best:.2f} < {MIN_SENTENCE_OVERLAP}"})
            continue
        kept.append(sentence)
    if not kept:
        result = refusal("no sentence passed citation check")
        result.metadata["refused_sentences"] = refused
        return result
    return Datum(
        " ".join(kept),
        EvidenceState.COMPUTED,
        source="neuclx:cited-answer",
        method="citation-enforcement",
        metadata={
            "kept_sentences": len(kept),
            "refused_sentences": refused,
            "min_sentence_overlap": MIN_SENTENCE_OVERLAP,
            "note": "Citation and term-overlap filter; kept sentences are source-linked, not independently verified.",
        },
    )
