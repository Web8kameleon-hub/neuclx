"""Native stdlib BM25 scoring; relevance is not calibrated confidence.

Algorithm reference and adaptation decision: docs/SOURCE_LEDGER.md.
No upstream source code or runtime dependency is imported.
"""

from collections import Counter
from math import log1p


def bm25_scores(query, documents):
    """Score pre-tokenized excerpts with positive IDF and fixed k1=1.5, b=.75.

    All excerpts, including nonmatching ones, contribute to corpus statistics.
    Empty corpora and queries yield zero scores. Repeated query terms count once.
    """
    frequencies = [Counter(document) for document in documents]
    lengths = [sum(counts.values()) for counts in frequencies]
    total = len(frequencies)
    average = sum(lengths) / total if total else 0
    scores = [0.0] * total
    if not average:
        return scores
    wanted = set(query)
    document_counts = Counter()
    for counts in frequencies:
        document_counts.update(wanted.intersection(counts))
    for index, counts in enumerate(frequencies):
        normalization = 1.5 * (0.25 + 0.75 * lengths[index] / average)
        for word in sorted(wanted.intersection(counts)):
            frequency = counts[word]
            idf = log1p((total - document_counts[word] + 0.5) /
                        (document_counts[word] + 0.5))
            scores[index] += idf * frequency * 2.5 / (frequency + normalization)
    return scores
