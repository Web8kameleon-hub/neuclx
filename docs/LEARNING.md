# Document learning

## Experimental retrieval ranking

`computed`: `LearningStore.answer(query, ranker='bm25')` provides native BM25
relevance scores with positive IDF, term-frequency saturation and excerpt-length
normalization. The implementation uses only the Python standard library. Scores
are not probabilities. Source claims remain `declared` and all answers, including
abstentions, pass through JONA. The existing 0.45 query-coverage threshold remains.
Equal scores sort by source and line for repeatability.

`declared`: The default remains `overlap`; corpus-wide quality has not been
established. Repeated terms count in excerpts but query terms count once.
Both rankers share the existing Albanian/English token normalization and stopwords.
BM25 rebuilds excerpt statistics per request; large-corpus cost is unmeasured.

```powershell
$env:PYTHONPATH = 'src'
python -m neuclx.learning --query 'JONA sandbox' --ranker bm25
python benchmarks/retrieval_benchmark.py --output evidence/retrieval-development.json
```

`measured`: The development fixture run recorded in
`evidence/retrieval-development.json` exercised six authored synthetic cases.
`computed`: baseline top-result/abstention accuracy was 4/6 and BM25 was 6/6.
These examples deliberately expose lexical ranking weaknesses; they are not an
unseen evaluation split. The report retains per-case outputs, source revisions,
fixture hash, timings and separately traced Python allocations. It does not
establish general quality, process memory use or comparative AI rank.

`unavailable`: Held-out retrieval accuracy and independent comparative ranking.

`declared`: This workflow builds a persistent retrieval corpus, not model weights or autonomous code changes. Retrieved passages retain `declared` status and citations. JONA gates writes and responses. No source is executed. No generated answer is recycled as verified evidence.

Run from the repository in PowerShell:

```powershell
$env:PYTHONPATH = 'src'
python -m neuclx.learning --query 'JONA sandbox'
python -m neuclx.learning --documents 'C:\approved\documents'
python -m neuclx.learning --snapshots data/pinned-learning-sources.json
```

The base import reads README, AGENTS, docs Markdown and public candidate snapshots whose SHA-256 matches the existing manifest. Explicit document directories support UTF-8 Markdown, text and reStructuredText, up to 1 MB per file. Hidden directories and data/build/dependency directories are excluded. Repeat imports update changed documents without duplicating unchanged sources. Deletions are not automatically propagated: the store is a retained source snapshot.

Repository snapshot JSON contains `repository`, `path`, full Git commit `revision`, and `content`. It is supplied by the operator from a verified repository read; the CLI does not itself authenticate remote content. Current main-branch README discovery is held separately under ignored `data/repository-discovery.json`; missing commit revisions are not promoted into the corpus. Private-source discovery stays local and is not published.

The running application uses the sibling `<ledger-stem>_learning.sqlite3`. `/api/respond` and context-free `/api/reason` retrieve cited excerpts. `/api/learning` exposes measured document count. Match scores are computed lexical relevance, not calibrated confidence or factual verification. Existing journey history is retained, including earlier placeholder results.

`not_implemented`: neural training, automatic repository crawling/scheduling, PDF/OCR ingestion, semantic embeddings, contradiction resolution, and autonomous implementation promotion. Full repository code audits and local server materials outside explicitly supplied paths are not covered by README discovery.
