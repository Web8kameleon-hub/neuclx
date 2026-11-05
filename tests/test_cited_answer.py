import unittest

from neuclx.cited_answer import enforce, numbered_context
from neuclx.evidence import EvidenceState

HITS = [
    {
        "source": "https://example.org/a",
        "revision": "sha256:aa",
        "line": 1,
        "excerpt": "Skenderbeu udhehoqi rezistencen shqiptare kunder osmaneve.",
    }
]


class CitedAnswerTests(unittest.TestCase):
    def test_keeps_only_cited_supported_sentences(self):
        text = (
            "Skenderbeu udhehoqi rezistencen shqiptare [1]. "
            "Ai lindi ne Mars. "
            "Ai fitoi ne hhh gjuhe tjeter krejt [1]. "
            "Rezistenca ishte kunder osmaneve [2]."
        )
        result = enforce(text, HITS)
        self.assertEqual(result.state, EvidenceState.COMPUTED)
        self.assertEqual(result.value, "Skenderbeu udhehoqi rezistencen shqiptare [1].")
        reasons = [item["why"] for item in result.metadata["refused_sentences"]]
        self.assertEqual(len(reasons), 3)
        self.assertEqual(reasons.count("no valid citation"), 2)

    def test_refuses_without_hits_or_when_model_has_no_source(self):
        self.assertEqual(enforce("Tekst [1].", []).state, EvidenceState.UNAVAILABLE)
        self.assertEqual(enforce("NO_SOURCE_ANSWER", HITS).state, EvidenceState.UNAVAILABLE)
        self.assertEqual(enforce("Pa citim fare.", HITS).state, EvidenceState.UNAVAILABLE)

    def test_numbered_context_is_one_based(self):
        self.assertTrue(numbered_context(HITS)[0].startswith("[1] https://example.org/a @ sha256:aa:1\n"))


if __name__ == "__main__":
    unittest.main()
