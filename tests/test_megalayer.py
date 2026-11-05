import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import threading
import unittest

from neuclx.evidence import EvidenceState
from neuclx.jona import JonaSandbox, PolicyDecision
from neuclx.megalayer import MegaLayerAdapter, MegaLayerError


class MegaLayerAdapterTests(unittest.TestCase):
    def test_unconfigured_adapter_reports_not_implemented(self):
        result = MegaLayerAdapter().analyze("hello", JonaSandbox())

        self.assertIsNone(result.value)
        self.assertEqual(result.state, EvidenceState.NOT_IMPLEMENTED)

    def test_adapter_rejects_non_loopback_endpoints(self):
        with self.assertRaisesRegex(ValueError, "loopback"):
            MegaLayerAdapter("https://inference.example/process")

    def test_processes_query_through_jona_and_returns_computed_metrics(self):
        received = {}
        payload = {
            "unique_signature": "sig-123",
            "combinations_used": 72,
            "theoretical_max": 1000,
            "processing_ms": 4.5,
            "complexity_score": 0.7,
            "total_layers_engaged": 12,
        }

        class Handler(BaseHTTPRequestHandler):
            def do_POST(self):
                received["path"] = self.path
                received["body"] = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
                body = json.dumps(payload).encode()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def log_message(self, *_):
                pass

        server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        self.addCleanup(server.server_close)
        self.addCleanup(thread.join, 5)
        self.addCleanup(server.shutdown)

        adapter = MegaLayerAdapter(f"http://127.0.0.1:{server.server_port}/process")
        result = adapter.analyze("Sa është 2 + 2?", JonaSandbox())

        self.assertEqual(received, {"path": "/process", "body": {"query": "Sa është 2 + 2?"}})
        self.assertEqual(result.state, EvidenceState.COMPUTED)
        self.assertEqual(result.value["unique_signature"], "sig-123")
        self.assertEqual(result.metadata["upstream_revision"], "f120457ab2c38c5bac9d23b62fca5d4ea6f17a0e")

    def test_jona_rejection_blocks_outbound_request(self):
        class RejectingSandbox:
            def evaluate(self, datum):
                return PolicyDecision.REJECT

            def release(self, datum):
                raise PermissionError("JONA rejected datum")

        adapter = MegaLayerAdapter("http://127.0.0.1:1/process")

        with self.assertRaises(PermissionError):
            adapter.analyze("private input", RejectingSandbox())

    def test_invalid_upstream_payload_is_an_explicit_error(self):
        class Handler(BaseHTTPRequestHandler):
            def do_POST(self):
                body = b'{"success": true}'
                self.send_response(200)
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def log_message(self, *_):
                pass

        server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        self.addCleanup(server.server_close)
        self.addCleanup(thread.join, 5)
        self.addCleanup(server.shutdown)

        adapter = MegaLayerAdapter(f"http://127.0.0.1:{server.server_port}/process")

        with self.assertRaises(MegaLayerError):
            adapter.analyze("hello", JonaSandbox())

    def test_upstream_redirect_is_rejected(self):
        class Handler(BaseHTTPRequestHandler):
            def do_POST(self):
                self.send_response(302)
                self.send_header("Location", "https://inference.example/process")
                self.end_headers()

            def log_message(self, *_):
                pass

        server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        self.addCleanup(server.server_close)
        self.addCleanup(thread.join, 5)
        self.addCleanup(server.shutdown)

        adapter = MegaLayerAdapter(f"http://127.0.0.1:{server.server_port}/process")

        with self.assertRaisesRegex(MegaLayerError, "HTTP 302"):
            adapter.analyze("hello", JonaSandbox())


if __name__ == "__main__":
    unittest.main()
