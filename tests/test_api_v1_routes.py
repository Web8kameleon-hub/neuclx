import json
import threading
import unittest
import tempfile
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib import request, error

from neuclx.evidence import Datum, EvidenceState
from neuclx.hybrid_fluid import (
    AlphabetLayerAdapter,
    FluidEngineAdapter,
    HybridFluidPipeline,
)
from neuclx.megalayer import MegaLayerAdapter
from neuclx.web import NeuCLXApplication, handler_factory


class ApiV1RouteTests(unittest.TestCase):
    def _server_for(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        app = NeuCLXApplication(Path(directory.name) / "journey.sqlite3")
        handler = handler_factory(app)
        server = __import__("http.server").server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
        port = server.server_address[1]
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        return server, app, port, thread

    def test_legacy_and_v1_agent_routes_work(self):
        server, app, port, thread = self._server_for()
        try:
            url = f"http://127.0.0.1:{port}/api/v1/agents?agent=albi&question=hello"
            with request.urlopen(url, timeout=5) as response:
                payload = json.loads(response.read().decode("utf-8"))
            self.assertEqual(response.status, 200)
            self.assertEqual(payload["agent"], "albi")
            self.assertIn("answer", payload)

            post_url = f"http://127.0.0.1:{port}/api/v1/respond"
            data = json.dumps({"prompt": "hello", "facts": ["NeCLX is real"]}).encode("utf-8")
            req = request.Request(post_url, data=data, headers={"Content-Type": "application/json"}, method="POST")
            with request.urlopen(req, timeout=5) as response:
                payload = json.loads(response.read().decode("utf-8"))
            self.assertEqual(response.status, 200)
            self.assertIn("achievement", payload)
            self.assertIn("response", payload)
        finally:
            server.shutdown()
            server.server_close()
            app.close()
            thread.join(timeout=5)

    def test_platform_profile_and_multilingual_agents_are_exposed(self):
        server, app, port, thread = self._server_for()
        try:
            url = f"http://127.0.0.1:{port}/api/v1/platform"
            with request.urlopen(url, timeout=5) as response:
                payload = json.loads(response.read().decode("utf-8"))
            self.assertEqual(response.status, 200)
            self.assertTrue(payload["multilingual"])
            self.assertGreaterEqual(payload["layers"], 4)
            self.assertIn("hvo_axes", payload)
            self.assertIn("T", payload["hvo_axes"])
            self.assertTrue(payload["saas_api"]["enabled"])
            self.assertIn("asi", payload["agents"])
            self.assertIn("blerina", payload["agents"])

            asi = app.ask_agent("asi", "How do you route tasks between agents?")
            self.assertIn("ASI", asi["answer"])

            blerina = app.ask_agent("blerina", "Can you translate or work multilingual?")
            self.assertIn("multilingual", blerina["answer"].lower())
        finally:
            server.shutdown()
            server.server_close()
            app.close()
            thread.join(timeout=5)

    def test_reason_endpoint_reports_unconfigured_megalayer(self):
        server, app, port, thread = self._server_for()
        try:
            data = json.dumps({"task": "2 + 2", "facts": []}).encode("utf-8")
            req = request.Request(
                f"http://127.0.0.1:{port}/api/v1/reason",
                data=data,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with request.urlopen(req, timeout=5) as response:
                payload = json.loads(response.read().decode("utf-8"))
            self.assertEqual(payload["megalayer"]["state"], "not_implemented")
            self.assertEqual(payload["state"], "computed")
            self.assertEqual(payload["conclusion"], "4")
        finally:
            server.shutdown()
            server.server_close()
            app.close()
            thread.join(timeout=5)

    def test_hybrid_fluid_route_fails_explicitly_when_services_are_unconfigured(self):
        server, app, port, thread = self._server_for()
        app.hybrid_fluid = HybridFluidPipeline(
            app.reasoning_engine.jona,
            app.ledger,
            alphabet=AlphabetLayerAdapter(),
            megalayer=MegaLayerAdapter(),
            fluid=FluidEngineAdapter(),
        )
        try:
            data = json.dumps({"task": "Kush je ti?", "mode": "hybrid-fluid"}).encode("utf-8")
            req = request.Request(
                f"http://127.0.0.1:{port}/api/v1/reason",
                data=data,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with self.assertRaises(error.HTTPError) as raised:
                request.urlopen(req, timeout=5)
            self.assertEqual(raised.exception.code, 503)
            payload = json.loads(raised.exception.read().decode("utf-8"))
            self.assertEqual(payload["error"], "hybrid_fluid_not_configured")
            self.assertIn("NEUCLX_ALPHABET_URL", payload["detail"])
        finally:
            server.shutdown()
            server.server_close()
            app.close()
            thread.join(timeout=5)

    def test_hybrid_fluid_attaches_model_answer_labeled_unverified(self):
        server, app, port, thread = self._server_for()

        class StubPipeline:
            def run(self, task, facts):
                return Datum({"ledger": None}, EvidenceState.COMPUTED, "stub", "stub", {"stages": []})

        seen = {}

        def converse(task, context=(), instructions=""):
            seen["context"] = list(context)
            seen["instructions"] = instructions
            return Datum(
                "Skenderbeu udhehoqi rezistencen shqiptare kunder osmaneve [1]. Ai ishte gjithashtu astronaut [1].",
                EvidenceState.COMPUTED,
                "local:test",
                "stub",
                {},
            )

        app.hybrid_fluid = StubPipeline()
        app.model_adapter.enabled = True
        app.reasoning_engine.converse = converse
        app.learning.ingest(
            "https://example.org/skenderbeu#p:e", "sha256:" + "ab" * 32,
            "Skenderbeu udhehoqi rezistencen shqiptare kunder osmaneve.",
        )
        try:
            payload = app.reason("Kush eshte Skenderbeu rezistencen osmaneve?", mode="hybrid-fluid")
            answer = payload["assistant_response"]
            self.assertTrue(seen["context"][0].startswith("[1] https://example.org/skenderbeu"))
            self.assertIn("Answer ONLY", seen["instructions"])
            self.assertEqual(answer["value"], "Skenderbeu udhehoqi rezistencen shqiptare kunder osmaneve [1].")
            self.assertEqual(len(answer["metadata"]["refused_sentences"]), 1)
            self.assertIn("declared, not verified", answer["metadata"]["claim_status"])
        finally:
            server.shutdown()
            server.server_close()
            app.close()
            thread.join(timeout=5)

    def test_hybrid_fluid_refuses_without_source_and_skips_model(self):
        server, app, port, thread = self._server_for()

        class StubPipeline:
            def run(self, task, facts):
                return Datum({"ledger": None}, EvidenceState.COMPUTED, "stub", "stub", {"stages": []})

        def converse(*_args, **_kwargs):
            raise AssertionError("model must not be called without a source")

        app.hybrid_fluid = StubPipeline()
        app.model_adapter.enabled = True
        app.reasoning_engine.converse = converse
        try:
            payload = app.reason("Pyetje pa asnje burim", mode="hybrid-fluid")
            answer = payload["assistant_response"]
            self.assertEqual(answer["state"], "unavailable")
            self.assertEqual(answer["metadata"]["reason"], "no retrieved source")
        finally:
            server.shutdown()
            server.server_close()
            app.close()
            thread.join(timeout=5)

    def test_reason_endpoint_includes_local_megalayer_metrics(self):
        upstream_payload = {
            "unique_signature": "local-sig",
            "combinations_used": 72,
            "theoretical_max": 1000,
            "processing_ms": 4.5,
            "complexity_score": 0.7,
            "total_layers_engaged": 12,
        }

        class Handler(BaseHTTPRequestHandler):
            def do_POST(self):
                self.rfile.read(int(self.headers["Content-Length"]))
                body = json.dumps(upstream_payload).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def log_message(self, *_):
                pass

        upstream = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        upstream_thread = threading.Thread(target=upstream.serve_forever, daemon=True)
        upstream_thread.start()
        self.addCleanup(upstream.server_close)
        self.addCleanup(upstream_thread.join, 5)
        self.addCleanup(upstream.shutdown)

        server, app, port, thread = self._server_for()
        app.megalayer = MegaLayerAdapter(f"http://127.0.0.1:{upstream.server_port}/process")
        try:
            data = json.dumps({"task": "2 + 2", "facts": []}).encode("utf-8")
            req = request.Request(
                f"http://127.0.0.1:{port}/api/v1/reason",
                data=data,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with request.urlopen(req, timeout=5) as response:
                payload = json.loads(response.read().decode("utf-8"))
            self.assertEqual(payload["megalayer"]["state"], "computed")
            self.assertEqual(payload["megalayer"]["value"]["unique_signature"], "local-sig")
            self.assertEqual(payload["conclusion"], "4")
        finally:
            server.shutdown()
            server.server_close()
            app.close()
            thread.join(timeout=5)

    def test_reason_endpoint_surfaces_megalayer_upstream_failures(self):
        class Handler(BaseHTTPRequestHandler):
            def do_POST(self):
                self.rfile.read(int(self.headers["Content-Length"]))
                self.send_response(503)
                self.send_header("Content-Length", "0")
                self.end_headers()

            def log_message(self, *_):
                pass

        upstream = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        upstream_thread = threading.Thread(target=upstream.serve_forever, daemon=True)
        upstream_thread.start()
        self.addCleanup(upstream.server_close)
        self.addCleanup(upstream_thread.join, 5)
        self.addCleanup(upstream.shutdown)

        server, app, port, thread = self._server_for()
        app.megalayer = MegaLayerAdapter(f"http://127.0.0.1:{upstream.server_port}/process")
        try:
            data = json.dumps({"task": "2 + 2", "facts": []}).encode("utf-8")
            req = request.Request(
                f"http://127.0.0.1:{port}/api/v1/reason",
                data=data,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with self.assertRaises(error.HTTPError) as raised:
                request.urlopen(req, timeout=5)
            self.assertEqual(raised.exception.code, 502)
            payload = json.loads(raised.exception.read().decode("utf-8"))
            self.assertEqual(payload["error"], "megalayer_unavailable")
        finally:
            server.shutdown()
            server.server_close()
            app.close()
            thread.join(timeout=5)

    def test_chat_endpoint_accepts_public_source_urls(self):
        server, app, port, thread = self._server_for()
        url = "https://docs.example/python"
        excerpt = "Python standard library text parsing."
        app.web_reader.read = lambda query, source, count=1: Datum(
            f"[{source}]\n{excerpt}",
            EvidenceState.DECLARED,
            source=source,
            method="public-web:cited-excerpt",
            metadata={"evidence_chain": [{
                "source": source,
                "revision": "sha256:abc",
                "sha256": "abc",
                "excerpt": excerpt,
                "state": "declared",
            }]},
        )
        try:
            data = json.dumps({
                "prompt": "Python text parsing",
                "facts": [],
                "source_urls": [url],
            }).encode("utf-8")
            req = request.Request(
                f"http://127.0.0.1:{port}/api/v1/respond",
                data=data,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with request.urlopen(req, timeout=5) as response:
                payload = json.loads(response.read().decode("utf-8"))
            evidence = payload["response"]["metadata"]["evidence_chain"][0]
            self.assertEqual(payload["response"]["state"], "declared")
            self.assertEqual(evidence["source"], url)
            self.assertEqual(evidence["excerpt"], excerpt)
        finally:
            server.shutdown()
            server.server_close()
            app.close()
            thread.join(timeout=5)


if __name__ == "__main__":
    unittest.main()
