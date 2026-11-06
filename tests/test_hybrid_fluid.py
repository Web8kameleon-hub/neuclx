import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import threading
import unittest
from urllib.parse import urlparse

from neuclx.evidence import EvidenceState
from neuclx.hybrid_fluid import (
    AlphabetContractError,
    AlphabetLayerAdapter,
    FluidEngineAdapter,
    HybridFluidNotConfigured,
    HybridFluidPipeline,
)
from neuclx.jona import JonaSandbox, PolicyDecision
from neuclx.megalayer import MegaLayerAdapter


class RecordingLedger:
    def __init__(self):
        self.records = []

    def record(self, prompt, response):
        self.records.append((prompt, response.as_dict()))
        return {"number": len(self.records), "achievement": "success"}


def start_upstream(*, bad_alphabet=False):
    received = []
    query = "Kush je ti?"

    class Handler(BaseHTTPRequestHandler):
        def _send(self, payload):
            body = json.dumps(payload).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self):
            path = urlparse(self.path).path
            received.append(("GET", path))
            if path == "/health":
                self._send(
                    {
                        "status": "healthy",
                        "service": "alphabet-layers",
                        "letters": 60 if bad_alphabet else 61,
                        "layers": 61,
                    }
                )
            elif path == "/api/v1/alphabet/stats":
                self._send(
                    {
                        "total_layers": 63,
                        "base_layers": 61,
                        "greek_letters": 24 if bad_alphabet else 25,
                        "albanian_letters": 36,
                        "meta_layer": True,
                    }
                )
            elif path == "/api/v1/alphabet/consciousness":
                self._send(
                    {
                        "text_length": len(query),
                        "consciousness_level": 0.41,
                        "peak_consciousness": 0.9,
                        "variance": 0.02,
                        "harmony": 0.98,
                        "dominant_frequency": 2.0,
                        "phi_alignment": 0.7,
                    }
                )
            else:
                self.send_error(404)

        def do_POST(self):
            path = urlparse(self.path).path
            body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            received.append(("POST", path, body))
            if path == "/api/v1/alphabet/process":
                self._send(
                    {
                        "alphabet_size": 61,
                        "active_layers": 61,
                        "total_complexity": 0.5,
                    }
                )
            elif path == "/process":
                self._send(
                    {
                        "unique_signature": "fixture-signature",
                        "combinations_used": 72,
                        "theoretical_max": 1000,
                        "processing_ms": 4.5,
                        "complexity_score": 0.7,
                        "total_layers_engaged": 12,
                    }
                )
            elif path == "/api/fluid/execute":
                self._send({"result": {"status": "fixture-computed"}})
            else:
                self.send_error(404)

        def log_message(self, *_):
            pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server, thread, received


def make_pipeline(server, *, jona=None):
    origin = f"http://127.0.0.1:{server.server_port}"
    return HybridFluidPipeline(
        jona or JonaSandbox(),
        RecordingLedger(),
        alphabet=AlphabetLayerAdapter(origin),
        megalayer=MegaLayerAdapter(origin + "/process"),
        fluid=FluidEngineAdapter(origin, "FlowPipeline"),
    )


class HybridFluidTests(unittest.TestCase):
    def test_runs_all_eleven_real_service_stages(self):
        server, thread, received = start_upstream()
        try:
            pipeline = make_pipeline(server)
            result = pipeline.run("Kush je ti?")
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=5)

        self.assertEqual(result.state, EvidenceState.COMPUTED)
        self.assertEqual(len(result.metadata["stages"]), 11)
        self.assertEqual(result.metadata["stages"][-1]["name"], "11-jona-record")
        self.assertEqual(result.value["wave_indices"]["state"], "computed")
        self.assertTrue(result.value["wave_indices"]["metadata"]["interpretation"].startswith("computed indices"))
        self.assertEqual(result.value["megalayer"]["value"]["unique_signature"], "fixture-signature")
        self.assertEqual(result.value["fluid_engine"]["value"]["result"]["status"], "fixture-computed")
        self.assertEqual(pipeline.ledger.records[0][0], "Kush je ti?")
        fluid_request = next(entry[2] for entry in received if len(entry) == 3 and entry[1] == "/api/fluid/execute")
        fluid_input = json.loads(fluid_request["inputData"])
        self.assertEqual(fluid_request["pipelineName"], "FlowPipeline")
        self.assertEqual(
            fluid_input["megalayer"]["value"]["unique_signature"],
            "fixture-signature",
        )

    def test_alphabet_contract_mismatch_stops_before_other_engines(self):
        server, thread, received = start_upstream(bad_alphabet=True)
        try:
            pipeline = make_pipeline(server)
            with self.assertRaisesRegex(AlphabetContractError, "greek_letters=24"):
                pipeline.run("Kush je ti?")
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=5)

        paths = [entry[1] for entry in received]
        self.assertEqual(paths, ["/health", "/api/v1/alphabet/stats"])
        self.assertNotIn("/process", paths)
        self.assertNotIn("/api/fluid/execute", paths)

    def test_missing_upstream_configuration_stops_before_network_requests(self):
        ledger = RecordingLedger()
        pipeline = HybridFluidPipeline(
            JonaSandbox(),
            ledger,
            alphabet=AlphabetLayerAdapter(),
            megalayer=MegaLayerAdapter(),
            fluid=FluidEngineAdapter(),
        )

        with self.assertRaisesRegex(HybridFluidNotConfigured, "NEUCLX_ALPHABET_URL"):
            pipeline.run("Kush je ti?")

        self.assertEqual(ledger.records, [])

    def test_jona_rejection_blocks_outbound_service_request(self):
        server, thread, received = start_upstream()

        class RejectOutbound(JonaSandbox):
            def evaluate(self, datum):
                if datum.method and datum.method.startswith("http:"):
                    return PolicyDecision.REJECT
                return super().evaluate(datum)

        try:
            pipeline = make_pipeline(server, jona=RejectOutbound())
            with self.assertRaisesRegex(PermissionError, "JONA"):
                pipeline.run("Kush je ti?")
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=5)

        self.assertEqual(received, [])


if __name__ == "__main__":
    unittest.main()
