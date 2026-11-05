import tempfile
import unittest
from pathlib import Path

from neuclx.evidence import EvidenceState
from neuclx.jona import JonaSandbox, PolicyDecision
from neuclx.learning import LearningStore
from neuclx.retrieval import bm25_scores


class RetrievalTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.store = LearningStore(Path(directory.name) / 'documents.sqlite3')

    def test_short_relevant_excerpt_beats_alphabetical_distractor(self):
        self.store.ingest('a-long', 'v1', 'JONA sandbox ' + 'unrelated ' * 80)
        self.store.ingest('z-focused', 'v2', 'JONA sandbox policy')
        baseline = self.store.answer('JONA sandbox')
        candidate = self.store.answer('JONA sandbox', ranker='bm25')
        self.assertEqual(baseline.metadata['evidence_chain'][0]['source'], 'a-long')
        hit = candidate.metadata['evidence_chain'][0]
        self.assertEqual(hit['source'], 'z-focused')
        self.assertEqual(hit['revision'], 'v2')
        self.assertEqual(hit['state'], 'declared')
        self.assertEqual(hit['score_state'], 'computed')
        self.assertEqual(candidate.state, EvidenceState.DECLARED)
        self.assertEqual(candidate.metadata['jona_decision'], 'sandbox_only')

    def test_empty_unknown_and_low_coverage_abstain(self):
        self.assertEqual(self.store.answer('JONA', ranker='bm25').state, EvidenceState.UNAVAILABLE)
        self.store.ingest('doc', 'v1', 'JONA sandbox')
        for query in ['', 'volcanology', 'JONA unknown volcano lunar']:
            with self.subTest(query=query):
                self.assertEqual(self.store.answer(query, ranker='bm25').state, EvidenceState.UNAVAILABLE)
        self.assertEqual(bm25_scores(['jona'], [[], []]), [0.0, 0.0])

    def test_deterministic_ties_and_query_repetition(self):
        self.store.ingest('z-doc', 'v1', 'JONA sandbox')
        self.store.ingest('a-doc', 'v1', 'JONA sandbox')
        first = self.store.answer('JONA', ranker='bm25').as_dict()
        self.assertEqual(first, self.store.answer('JONA JONA', ranker='bm25').as_dict())
        self.assertEqual(first['metadata']['evidence_chain'][0]['source'], 'a-doc')

    def test_rejection_blocks_matching_and_unavailable_answers(self):
        self.store.ingest('doc', 'v1', 'JONA sandbox')

        class Reject(JonaSandbox):
            def evaluate(self, datum):
                return PolicyDecision.REJECT

        self.store.sandbox = Reject()
        for query in ['JONA', 'unknown']:
            with self.subTest(query=query), self.assertRaises(PermissionError):
                self.store.answer(query, ranker='bm25')

    def test_invalid_ranker_has_no_silent_fallback(self):
        with self.assertRaises(ValueError):
            self.store.answer('JONA', ranker='external')
