# Open-source combination strategy

`declared`: Combine NeuCLX and Web8kameleon-hub research with selected open-source
methods to pursue the top-five objective defined in WEB8_RESEARCH.md.
Repository discovery does not establish a performance gain or completed integration.

`measured`: On 2026-11-04, the repository pages and the source files listed in
SOURCE_LEDGER.md were inspected. License names below describe the fetched license
texts, not a completed review of all files, dependencies or dataset terms.

| Candidate | Inspected license text | Intended role | Admission status |
|---|---|---|---|
| [rank_bm25](https://github.com/dorianbrown/rank_bm25) | Apache-2.0 | Study term frequency and document-length normalization for retrieval | declared: algorithm reference; the inspected implementation imports NumPy and cannot be added as a core dependency |
| [SymPy](https://github.com/sympy/sympy) | BSD three-clause text | Symbolic mathematics research and possible independent answer checking | declared: reference only; package/dependency and source inspection remain necessary before any adaptation |
| [lm-evaluation-harness](https://github.com/EleutherAI/lm-evaluation-harness) | MIT | Study evaluation formats, scoring and reproducible comparisons | declared: external evaluation candidate; its inspected dependency list excludes direct use in core code or core tests |

`declared`: First implementation candidate: a standard-library retrieval ranker
that compares term frequency, corpus frequency and excerpt length against the
existing token-overlap baseline. It must preserve citations, declared source
claims, abstention and mandatory JONA authorization. A ranking score is computed
relevance, never measured confidence or proof of correctness.

`declared`: Acceptance requires versioned retrieval tasks with known relevant
sources, unseen evaluation examples, baseline and candidate results, top-result
accuracy, failures, latency and memory evidence. Report individual regressions.
Do not replace the default ranker merely because implementation tests pass.

`declared`: Any adapted source must have exact provenance, applicable notices,
dependency review and rejection tests before runtime admission. Source text is
untrusted data and cannot authorize tools, execute code or override JONA.

`declared`: Benchmark datasets require their own provenance and usage review;
a framework's software license does not establish dataset permissions. Evaluation
answers must remain outside development and retrieval corpora.

`computed`: A native BM25-inspired experimental ranker is now available via
`LearningStore.answer(..., ranker='bm25')` and the learning CLI. It uses positive
IDF rather than upstream Okapi's negative-IDF flooring, and does not copy upstream
code. See LEARNING.md for measured development evidence and limitations.

`computed`: The standard-library `ModelAdapter` now supports explicit calls to
OpenAI-compatible local and hosted endpoints. It is disabled by default, and
JONA checks requests and responses. No inference service or model weights are
installed or downloaded by NeuCLX. The default ranker has not been promoted.

`unavailable`: Overall AI rank and evidence of top-five capability. Combining
repositories does not itself demonstrate learning or general intelligence.
