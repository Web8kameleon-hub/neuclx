"""Development comparison only; does not establish held-out quality or AI rank."""

import argparse
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import platform
import statistics
import tempfile
import time
import tracemalloc

from neuclx.learning import LearningStore


def run(fixture):
    raw = fixture.read_bytes()
    dataset = json.loads(raw)
    results = []
    for case in dataset['cases']:
        with tempfile.TemporaryDirectory() as directory:
            store = LearningStore(Path(directory) / 'documents.sqlite3')
            for source, text in case['documents'].items():
                store.ingest(source, 'fixture:' + sha256(text.encode()).hexdigest(), text)
            row = {'state': 'measured', 'id': case['id'],
                   'expected_source': {'state': 'declared', 'value': case['expected_source']}}
            for ranker in ('overlap', 'bm25'):
                samples = []
                for _ in range(5):
                    start = time.perf_counter_ns()
                    answer = store.answer(case['query'], limit=1, ranker=ranker)
                    samples.append(time.perf_counter_ns() - start)
                tracemalloc.start()
                try:
                    store.answer(case['query'], limit=1, ranker=ranker)
                    _, peak = tracemalloc.get_traced_memory()
                finally:
                    tracemalloc.stop()
                hits = answer.metadata['evidence_chain']
                selected = hits[0]['source'] if hits else None
                row[ranker] = {'state': 'measured', 'selected_source': selected,
                               'correct': {'state': 'computed', 'value': selected == case['expected_source']},
                               'median_latency_ns': int(statistics.median(samples)),
                               'peak_traced_python_bytes': peak, 'answer': answer.as_dict()}
            results.append(row)
    summaries = {}
    for ranker in ('overlap', 'bm25'):
        correct = sum(row[ranker]['correct']['value'] for row in results)
        summaries[ranker] = {'state': 'computed', 'correct': correct, 'cases': len(results),
                             'top_result_or_abstention_accuracy': correct / len(results) if results else None}
    return {'state': 'measured', 'schema_version': '1.0',
            'captured_at': datetime.now(timezone.utc).isoformat(),
            'fixture_version': dataset['version'], 'fixture_sha256': sha256(raw).hexdigest(),
            'split': dataset['split'], 'python': platform.python_version(),
            'method': 'Five sequential calls per ranker per case; SQLite query and scoring included. '
                      'Separate tracemalloc call measures Python allocations, not process RSS.',
            'held_out_quality': {'state': 'unavailable', 'value': None},
            'summary': summaries, 'cases': results}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--fixture', type=Path, default=Path(__file__).with_name('fixtures') / 'retrieval_development.json')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    report = run(args.fixture)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    print(json.dumps(report['summary']))
