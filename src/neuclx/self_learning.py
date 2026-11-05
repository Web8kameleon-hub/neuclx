"""Self-learning and self-memory.

Only cited source excerpts enter the retrieval corpus. Model output is remembered as
an immutable Stigma Film frame through the journey ledger but is never ingested as a
fact, so an unverified answer cannot poison later retrieval.
"""

from __future__ import annotations

from datetime import UTC, datetime
from hashlib import sha256

from .evidence import Datum, EvidenceState
from .learning import connection, term_tokens

BIG_BYTES = 256 * 1024
RARE_MAX_HITS = 1
TIER_METHOD = (
    "computed from stored size and retrieval hits: bigdata >= 256 KiB; "
    "seltendata <= 1 retrieval; otherwise standarddata"
)


def tier_of(size_bytes: int, hits: int) -> str:
    if size_bytes >= BIG_BYTES:
        return "bigdata"
    if hits <= RARE_MAX_HITS:
        return "seltendata"
    return "standarddata"


class SelfLearning:
    def __init__(self, learning, ledger, sandbox):
        self.learning = learning
        self.ledger = ledger
        self.sandbox = sandbox
        with connection(self.learning.path) as db:
            db.execute(
                "CREATE TABLE IF NOT EXISTS source_usage ("
                "source TEXT PRIMARY KEY, hits INTEGER NOT NULL, first_used TEXT NOT NULL, last_used TEXT NOT NULL)"
            )

    def learn_web_hits(self, hits) -> int:
        learned = 0
        for hit in hits:
            excerpt = (hit.get("excerpt") or "").strip()
            url = hit.get("source")
            page_digest = hit.get("sha256")
            if not excerpt or not url or not page_digest:
                continue
            key = f"{url}#{page_digest[:12]}:{sha256(excerpt.encode('utf-8')).hexdigest()[:8]}"
            if self.learning.ingest(key, "sha256:" + page_digest, excerpt):
                learned += 1
        return learned

    def record_use(self, hits) -> None:
        now = datetime.now(UTC).isoformat()
        sources = {hit["source"] for hit in hits if hit.get("source")}
        with connection(self.learning.path) as db:
            for source in sources:
                db.execute(
                    "INSERT INTO source_usage(source, hits, first_used, last_used) VALUES(?,1,?,?) "
                    "ON CONFLICT(source) DO UPDATE SET hits = hits + 1, last_used = excluded.last_used",
                    (source, now, now),
                )

    def tiers(self, limit: int = 20) -> Datum:
        with connection(self.learning.path) as db:
            rows = db.execute(
                "SELECT d.source, length(CAST(d.content AS BLOB)), COALESCE(u.hits, 0) "
                "FROM documents d LEFT JOIN source_usage u ON u.source = d.source ORDER BY d.source"
            ).fetchall()
        counts = {"seltendata": 0, "standarddata": 0, "bigdata": 0}
        listing = []
        for source, size, hits in rows:
            tier = tier_of(size, hits)
            counts[tier] += 1
            listing.append({"source": source, "bytes": size, "hits": hits, "tier": tier})
        listing.sort(key=lambda row: (-row["hits"], row["source"]))
        return Datum(
            {"documents": len(rows), "tiers": counts, "top": listing[: max(1, min(limit, 100))]},
            EvidenceState.COMPUTED,
            source="neuclx:self-learning",
            method="tier-classification",
            metadata={"tier_rule": TIER_METHOD},
        )

    @staticmethod
    def grounding(answer_text: str, hits) -> dict:
        evidence_terms = set()
        for hit in hits:
            evidence_terms.update(term_tokens(hit.get("excerpt") or ""))
        answer_terms = set(term_tokens(answer_text or ""))
        overlap = len(answer_terms & evidence_terms) / len(answer_terms) if answer_terms else 0.0
        cited = sorted({hit["source"] for hit in hits if hit.get("source") and hit["source"] in (answer_text or "")})
        return {
            "evidence_sources": len({hit.get("source") for hit in hits}),
            "grounded": bool(hits),
            "answer_term_overlap": round(overlap, 4),
            "cited_sources": cited,
            "state": EvidenceState.COMPUTED.value,
            "note": "Term-overlap index and literal source mentions; not a truth or correctness score.",
        }

    def remember_answer(self, question: str, answer: Datum, hits) -> dict:
        grounding = self.grounding(str(answer.value or ""), hits)
        claim = (
            "Model-generated response; sources were supplied as context but are declared, not verified."
            if grounding["grounded"]
            else "Model-generated response; no retrieved source supports it and it is not independently verified."
        )
        released = self.sandbox.release(
            Datum(
                answer.value,
                answer.state,
                answer.source,
                answer.method,
                {
                    **answer.metadata,
                    "claim_status": claim,
                    "grounding": grounding,
                    "evidence_chain": [
                        {key: hit.get(key) for key in ("source", "revision", "sha256", "line")} for hit in hits
                    ],
                },
            )
        )
        stone = self.ledger.record(question, released)
        return {"answer": released, "stone": stone, "grounding": grounding}
