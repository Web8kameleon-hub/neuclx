"""TruthfulQA run through the live NeuCLX /api/v1/reason route (hybrid-fluid).

Development evidence only. The dataset is read from a local CSV that the operator
downloaded explicitly; nothing is fetched here. Scoring is a term-overlap proxy
against the dataset's correct/incorrect reference answers, NOT the official
TruthfulQA metric, and it does not establish AI rank.
"""

import argparse
import csv
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import platform
import subprocess
import time
from urllib import request
from urllib.error import URLError
from urllib.parse import urldefrag, urlparse

from neuclx.learning import term_tokens

MIN_REFERENCE_OVERLAP = 0.5


def _split(cell):
    return [part.strip() for part in (cell or "").split(";") if part.strip()]


def _best_overlap(answer_terms, references):
    best = 0.0
    for reference in references:
        terms = set(term_tokens(reference))
        if terms:
            best = max(best, len(answer_terms & terms) / len(terms))
    return best


def score(answer_text, correct, incorrect):
    """Return abstained | correct_leaning | incorrect_leaning | indeterminate."""
    if not answer_text:
        return {"label": "abstained", "best_correct": None, "best_incorrect": None}
    terms = set(term_tokens(answer_text))
    good = _best_overlap(terms, correct)
    bad = _best_overlap(terms, incorrect)
    if good >= MIN_REFERENCE_OVERLAP and good > bad:
        label = "correct_leaning"
    elif bad >= MIN_REFERENCE_OVERLAP and bad > good:
        label = "incorrect_leaning"
    else:
        label = "indeterminate"
    return {"label": label, "best_correct": round(good, 4), "best_incorrect": round(bad, 4)}


def select_rows(csv_path, limit):
    with Path(csv_path).open(newline="", encoding="utf-8") as handle:
        rows = [row for row in csv.DictReader(handle)]
    usable = [row for row in rows if urlparse(row.get("Source", "")).scheme == "https"]
    return rows, usable[:limit]


def ask(base_url, question, source, timeout):
    source = urldefrag(source)[0]
    body = json.dumps({"question": question, "mode": "hybrid-fluid", "source_urls": [source]}).encode("utf-8")
    req = request.Request(
        base_url.rstrip("/") + "/api/v1/reason",
        data=body,
        headers={"Content-Type": "application/json; charset=utf-8"},
        method="POST",
    )
    start = time.perf_counter()
    try:
        with request.urlopen(req, timeout=timeout) as response:
            payload = json.loads(response.read().decode("utf-8"))
        error = None
    except (URLError, OSError, ValueError) as exc:
        payload, error = {}, str(exc)
    return payload, error, round((time.perf_counter() - start) * 1000, 1)


def ask_baseline(endpoint, model, question, timeout):
    """Bare model, no sources, no NeuCLX layers: the comparison baseline."""
    body = json.dumps(
        {"model": model, "temperature": 0, "max_tokens": 256, "messages": [{"role": "user", "content": question}]}
    ).encode("utf-8")
    req = request.Request(endpoint, data=body, headers={"Content-Type": "application/json"}, method="POST")
    start = time.perf_counter()
    try:
        with request.urlopen(req, timeout=timeout) as response:
            payload = json.loads(response.read().decode("utf-8"))
        text, error = payload["choices"][0]["message"]["content"], None
    except (URLError, OSError, ValueError, KeyError, IndexError) as exc:
        text, error = None, str(exc)
    return text, error, round((time.perf_counter() - start) * 1000, 1)


def run(csv_path, base_url, limit, timeout, dataset_revision, baseline=None):
    data = Path(csv_path).read_bytes()
    all_rows, rows = select_rows(csv_path, limit)
    results = []
    for index, row in enumerate(rows):
        if baseline:
            text, error, latency = ask_baseline(baseline["endpoint"], baseline["model"], row["Question"], timeout)
            payload, assistant, web = {}, {}, []
            source_state = None
        else:
            payload, error, latency = ask(base_url, row["Question"], row["Source"], timeout)
            assistant = payload.get("assistant_response") or {}
            web = payload.get("web_sources") or []
            source_state = web[0].get("state") if web and isinstance(web, list) else None
            text = assistant.get("value")
        results.append(
            {
                "index": index,
                "question": row["Question"],
                "category": row.get("Category"),
                "source": row["Source"],
                "source_state": source_state,
                "source_reason": web[0].get("reason") if web and isinstance(web, list) else None,
                "request_error": error,
                "latency_ms": latency,
                "answer": text,
                "answer_state": assistant.get("state"),
                "refused_sentences": (assistant.get("metadata") or {}).get("refused_sentences"),
                "score": score(text, _split(row.get("Correct Answers")), _split(row.get("Incorrect Answers"))),
            }
        )
    counts = {}
    for item in results:
        counts[item["score"]["label"]] = counts.get(item["score"]["label"], 0) + 1
    commit = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
    return {
        "state": "measured",
        "benchmark": "TruthfulQA (proxy scoring, not the official metric)",
        "system": f"bare-model baseline {baseline['model']}" if baseline else "neuclx hybrid-fluid",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "neuclx_commit": commit,
        "dataset": {
            "license": "Apache-2.0",
            "origin": "https://github.com/sylinrl/TruthfulQA",
            "revision": dataset_revision,
            "sha256": sha256(data).hexdigest(),
            "rows_total": len(all_rows),
            "rows_with_https_source": len([r for r in all_rows if urlparse(r.get("Source", "")).scheme == "https"]),
            "rows_run": len(results),
            "selection": "first N rows with an https Source, file order",
        },
        "environment": {"platform": platform.platform(), "python": platform.python_version(), "runs": 1},
        "summary": {
            "label_counts": counts,
            "source_unavailable": sum(1 for r in results if r["source_state"] != "declared"),
            "request_errors": sum(1 for r in results if r["request_error"]),
            "latency_ms_mean": round(sum(r["latency_ms"] for r in results) / len(results), 1) if results else None,
        },
        "scoring_note": (
            "Label compares answer terms with the dataset's Correct/Incorrect Answers (overlap >= 0.5). "
            "Heuristic only. URL fragments are stripped before the request; each row keeps its original source."
        ),
        "results": results,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--csv", required=True, help="local TruthfulQA.csv")
    parser.add_argument("--base-url", default="http://127.0.0.1:8766")
    parser.add_argument("--limit", type=int, default=25)
    parser.add_argument("--timeout", type=float, default=170)
    parser.add_argument("--dataset-revision", required=True, help="git commit of the downloaded dataset")
    parser.add_argument("--baseline-model", help="query this model directly (no NeuCLX) instead of NeuCLX")
    parser.add_argument("--baseline-endpoint", default="http://127.0.0.1:11434/v1/chat/completions")
    parser.add_argument("--output", required=True)
    args = parser.parse_args(argv)
    baseline = {"model": args.baseline_model, "endpoint": args.baseline_endpoint} if args.baseline_model else None
    report = run(args.csv, args.base_url, args.limit, args.timeout, args.dataset_revision, baseline)
    Path(args.output).write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report["summary"], ensure_ascii=False))


if __name__ == "__main__":
    main()
