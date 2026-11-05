import hashlib
import socket
import unittest

from neuclx.evidence import EvidenceState
from neuclx.jona import PolicyDecision, JonaSandbox
from neuclx.web_evidence import MAX_EXCERPT_CHARACTERS, PublicWebReadError, PublicWebReader


def public_resolver(host, port, *, type):
    return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("8.8.8.8", port))]


class PublicWebReaderTests(unittest.TestCase):
    def setUp(self):
        self.body = (
            b"<html><head><title>Python Guide</title><script>hidden secret</script></head>"
            b"<body><nav>ignore navigation</nav><h1>Python standard library guide</h1>"
            b"<p>The Python standard library includes modules for safe arithmetic and text processing.</p>"
            b"<p>Another unrelated paragraph about ocean weather.</p></body></html>"
        )
        self.requests = []

    def make_reader(self, *, status=200, content_type="text/html; charset=utf-8", sandbox=None):
        def transport(parsed, address):
            self.requests.append((parsed.geturl(), address))
            return status, {"content-type": content_type}, self.body

        return PublicWebReader(
            sandbox=sandbox,
            resolver=public_resolver,
            transport=transport,
        )

    def test_reads_matching_excerpt_with_source_digest_and_declared_state(self):
        datum = self.make_reader().read(
            "Python standard library arithmetic",
            "https://docs.example/python",
        )

        self.assertEqual(datum.state, EvidenceState.DECLARED)
        self.assertIn("Python standard library", datum.value)
        self.assertNotIn("hidden secret", datum.value)
        self.assertNotIn("ignore navigation", datum.value)
        hit = datum.metadata["evidence_chain"][0]
        self.assertEqual(hit["source"], "https://docs.example/python")
        self.assertEqual(hit["sha256"], hashlib.sha256(self.body).hexdigest())
        self.assertEqual(hit["state"], "declared")
        self.assertEqual(hit["digest_state"], "computed")
        self.assertLessEqual(len(hit["excerpt"]), MAX_EXCERPT_CHARACTERS)

    def test_rejects_non_https_and_embedded_credentials(self):
        reader = self.make_reader()
        for url in ("http://docs.example/python", "https://user:pass@docs.example/python"):
            with self.subTest(url=url), self.assertRaises(PublicWebReadError):
                reader.read("python", url)
        self.assertEqual(self.requests, [])

    def test_rejects_private_dns_answers(self):
        reader = PublicWebReader(
            resolver=lambda *_args, **_kwargs: [
                (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("127.0.0.1", 443))
            ],
            transport=lambda *_: self.fail("transport must not run"),
        )

        with self.assertRaisesRegex(PublicWebReadError, "non-public"):
            reader.read("python", "https://docs.example/python")

    def test_rejects_empty_dns_answers(self):
        reader = PublicWebReader(
            resolver=lambda *_args, **_kwargs: [],
            transport=lambda *_: self.fail("transport must not run"),
        )

        with self.assertRaisesRegex(PublicWebReadError, "no addresses"):
            reader.read("python", "https://docs.example/python")

    def test_jona_rejection_blocks_web_request(self):
        class Deny(JonaSandbox):
            def evaluate(self, datum):
                return PolicyDecision.REJECT

        reader = PublicWebReader(
            sandbox=Deny(),
            resolver=lambda *_args, **_kwargs: self.fail("DNS must not run before JONA"),
            transport=lambda *_: self.fail("transport must not run"),
        )
        with self.assertRaises(PermissionError):
            reader.read("python", "https://docs.example/python")
        self.assertEqual(self.requests, [])

    def test_redirect_is_not_followed(self):
        reader = self.make_reader(status=302)

        with self.assertRaisesRegex(PublicWebReadError, "HTTP 302"):
            reader.read("python", "https://docs.example/python")

    def test_rejects_encoded_credential_query_keys(self):
        with self.assertRaisesRegex(PublicWebReadError, "credential-like"):
            self.make_reader().read(
                "python",
                "https://docs.example/python?%61pi_key=not-a-real-key",
            )

    def test_no_matching_text_is_unavailable_as_explicit_error(self):
        with self.assertRaisesRegex(PublicWebReadError, "no query-matching"):
            self.make_reader().read("volcanology", "https://docs.example/python")


if __name__ == "__main__":
    unittest.main()
