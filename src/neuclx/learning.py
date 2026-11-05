"""Explicit, repeatable document ingestion and cited retrieval; never executes sources."""

from argparse import ArgumentParser
from contextlib import contextmanager
from hashlib import sha256
import json
from pathlib import Path
import re
import sqlite3
import unicodedata

from .evidence import Datum, EvidenceState
from .jona import JonaSandbox, PolicyDecision
from .retrieval import bm25_scores


@contextmanager
def connection(path):
    db = sqlite3.connect(path)
    try:
        with db:
            yield db
    finally:
        db.close()


def term_tokens(text):
    normalized = unicodedata.normalize('NFKD', text.casefold())
    normalized = ''.join(c for c in normalized if not unicodedata.combining(c))
    stop = set('the and for with from this that what how is are a an of in to ne nje dhe eshte cila cili roli si te e i kush je ti mund duket pse ku kur sa ka nuk jemi ketu'.split())
    words = re.findall(r'[a-zçëq]+', normalized)
    return [w for w in words if w not in stop and len(w) > 2]


def terms(text):
    return set(term_tokens(text))


class LearningStore:
    def __init__(self, path, sandbox=None):
        self.path = str(path)
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        self.sandbox = sandbox or JonaSandbox()
        with connection(self.path) as db:
            db.execute('CREATE TABLE IF NOT EXISTS documents (source TEXT PRIMARY KEY, revision TEXT, digest TEXT, content TEXT)')

    def ingest(self, source, revision, content):
        if not source or not revision or not content.strip():
            raise ValueError('source, revision and content are required')
        datum = Datum(content, EvidenceState.DECLARED, source, 'document-ingestion')
        if self.sandbox.evaluate(datum) is PolicyDecision.REJECT:
            raise PermissionError('JONA rejected source')
        self.sandbox.release(datum)
        digest = sha256(content.encode('utf-8')).hexdigest()
        with connection(self.path) as db:
            old = db.execute('SELECT digest, revision FROM documents WHERE source=?', (source,)).fetchone()
            if old == (digest, revision):
                return False
            db.execute('INSERT OR REPLACE INTO documents VALUES (?,?,?,?)', (source, revision, digest, content))
        return True

    def status(self):
        with connection(self.path) as db:
            count = db.execute('SELECT count(*) FROM documents').fetchone()[0]
        return self.sandbox.release(Datum({'documents': count}, EvidenceState.MEASURED, 'learning-store', 'sqlite-count'))

    def answer(self, query, limit=3, *, ranker='overlap'):
        if ranker not in {'overlap', 'bm25'}:
            raise ValueError('ranker must be overlap or bm25')
        wanted = terms(query)
        ranked = []
        excerpts = []
        with connection(self.path) as db:
            rows = db.execute('SELECT source,revision,digest,content FROM documents ORDER BY source').fetchall()
        for source, revision, digest, content in rows:
            lines = content.splitlines()
            for start in range(0, len(lines), 12):
                excerpt = '\n'.join(lines[start:start + 12]).strip()
                excerpts.append((source, revision, digest, start, excerpt, term_tokens(excerpt)))
        relevance = bm25_scores(wanted, [row[5] for row in excerpts]) if ranker == 'bm25' else None
        for index, (source, revision, digest, start, excerpt, tokens) in enumerate(excerpts):
            overlap = wanted & set(tokens)
            if not overlap:
                continue
            coverage = len(overlap) / max(1, len(wanted))
            if coverage < 0.45:
                continue
            score = relevance[index] if relevance is not None else coverage
            ranked.append((score, source, start, {'source': source, 'revision': revision, 'sha256': digest,
                'line': start + 1, 'excerpt': excerpt, 'state': 'declared', 'score': score,
                'score_state': 'computed', 'score_method': ranker,
                'query_coverage': coverage, 'query_coverage_state': 'computed'}))
        ranked.sort(key=lambda row: (-row[0], row[1], row[2]))
        hits = [row[3] for row in ranked[:max(1, min(limit, 10))]]
        if not hits:
            return self.sandbox.release(Datum(None, EvidenceState.UNAVAILABLE, method='document-retrieval', metadata={'evidence_chain': []}))
        value = '\n\n'.join(f"[{hit['source']} @ {hit['revision']}:{hit['line']}]\n{hit['excerpt']}" for hit in hits)
        return self.sandbox.release(Datum(value, EvidenceState.DECLARED, 'learning-store', 'cited-document-excerpts',
            {'evidence_chain': hits, 'jona_decision': 'sandbox_only', 'claim_status': 'Source declarations; not independently verified.'}))


def ingest_project(store, root, extra_roots=()):
    root = Path(root).resolve()
    report = {'state': 'measured', 'imported': 0, 'unchanged': 0, 'unavailable': []}

    def add(path, source, revision, expected=None):
        try:
            if path.is_symlink() or not path.resolve().is_relative_to(root) and not any(path.resolve().is_relative_to(p) for p in extra_roots):
                raise ValueError('source outside approved roots')
            with path.open('rb') as handle:
                raw = handle.read(1_000_001)
            if len(raw) > 1_000_000:
                raise ValueError('source exceeds 1 MB')
            if expected and sha256(raw).hexdigest() != expected:
                raise ValueError('manifest digest mismatch')
            content = raw.decode('utf-8-sig')
            if '\x00' in content:
                raise ValueError('binary content')
            changed = store.ingest(source, revision or 'sha256:' + sha256(raw).hexdigest(), content)
            report['imported' if changed else 'unchanged'] += 1
        except (OSError, UnicodeError, ValueError, PermissionError) as exc:
            report['unavailable'].append({'source': source, 'state': 'unavailable', 'reason': str(exc)})

    for path in [root / 'README.md', root / 'AGENTS.md', *sorted((root / 'docs').glob('*.md'))]:
        add(path, 'local:neuclx/' + path.relative_to(root).as_posix(), None)
    manifest = json.loads((root / 'imports/manifest.json').read_text(encoding='utf-8'))
    for item in manifest['sources']:
        if item['decision'] == 'copy' and item['visibility'] == 'public':
            add(root / item['destination'], item['repository'] + '/' + item['candidate'], item['revision'], item['sha256'])
        else:
            report['unavailable'].append({'source': item['repository'], 'state': 'unavailable', 'reason': item['reason']})
    for folder in extra_roots:
        if not folder.is_dir():
            report['unavailable'].append({'source': str(folder), 'state': 'unavailable', 'reason': 'missing directory'})
            continue
        for path in sorted(folder.rglob('*')):
            relative = path.relative_to(folder)
            if any(p.startswith('.') or p in {'node_modules', 'data', 'dist', '__pycache__'} for p in relative.parts):
                continue
            if path.is_file() and path.suffix.lower() in {'.md', '.txt', '.rst'}:
                add(path, 'local:' + path.as_posix(), None)
    report['store'] = store.status().as_dict()
    return report


def main():
    parser = ArgumentParser(description=__doc__)
    parser.add_argument('--root', default='.')
    parser.add_argument('--store', default='data/neuclx_learning.sqlite3')
    parser.add_argument('--documents', action='append', default=[])
    parser.add_argument('--query')
    parser.add_argument('--ranker', choices=('overlap', 'bm25'), default='overlap',
                        help='Experimental BM25 is opt-in; overlap remains the default')
    parser.add_argument('--snapshots', help='Explicit JSON snapshot file with pinned repository revisions')
    args = parser.parse_args()
    store = LearningStore(args.store)
    report = ingest_project(store, args.root, tuple(Path(p).resolve() for p in args.documents))
    if args.snapshots:
        for item in json.loads(Path(args.snapshots).read_text(encoding='utf-8')):
            if not re.fullmatch(r'[0-9a-f]{40}', item.get('revision') or ''):
                raise ValueError('Repository snapshots require a full Git commit revision')
            changed = store.ingest(item['repository'] + '/' + item['path'], item['revision'], item['content'])
            report['imported' if changed else 'unchanged'] += 1
        report['store'] = store.status().as_dict()
    if args.query:
        report['answer'] = store.answer(args.query, ranker=args.ranker).as_dict()
    print(json.dumps(report, ensure_ascii=True, indent=2))


if __name__ == '__main__':
    main()
