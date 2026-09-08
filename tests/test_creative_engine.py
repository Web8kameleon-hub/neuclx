from __future__ import annotations

import json
import threading
import unittest
from pathlib import Path
from urllib import request

from neuclx.creative_engine import CreativeEngine, ImageGenerator
from neuclx.evidence import EvidenceState
from neuclx.web import NeuCLXApplication, handler_factory


class CreativeEngineTests(unittest.TestCase):
    def test_image_generator_creates_svg(self):
        generator = ImageGenerator(output_dir="data/test_creative_outputs")
        output_path, output_hash = generator.generate("A blue circle and red bars", seed=7, style="bold", author="tester")
        try:
            svg = Path(output_path).read_text(encoding="utf-8")
            self.assertTrue(output_path.endswith(".svg"))
            self.assertTrue(output_hash)
            self.assertIn("<svg", svg)
            self.assertIn("prompt_hash", svg)
        finally:
            path = Path(output_path)
            if path.exists():
                path.unlink()
            if path.parent.exists() and not any(path.parent.iterdir()):
                path.parent.rmdir()

    def test_text_generation_includes_hvo_metadata(self):
        memory = object()
        engine = CreativeEngine(memory)
        result = engine.create("Write a short poetic note about a verifiable system", modality="text", seed=11, style="poetic", author="tester")
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["modality"], "text")
        self.assertIn("output_text", result)
        self.assertTrue(result["tensor"]["parameters"])
        self.assertIn("HVO profile", result["output_text"])
        self.assertEqual(result["tensor"]["state"], EvidenceState.DECLARED.value)

    def test_creative_engine_returns_declared_tensor(self):
        memory = object()
        engine = CreativeEngine(memory)
        result = engine.create("A blue circle and red bars", modality="image", seed=7, style="bold", author="tester")
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["modality"], "image")
        self.assertEqual(result["tensor"]["state"], EvidenceState.DECLARED.value)
        self.assertTrue(result["evidence_chain"])
        self.assertTrue(result["output_path"].endswith(".svg"))

    def test_audio_generation_creates_wav(self):
        memory = object()
        engine = CreativeEngine(memory)
        result = engine.create("Soothing ambient tone for a calm system", modality="audio", seed=21, style="ambient", author="tester")
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["modality"], "audio")
        self.assertTrue(result["output_path"].endswith(".wav"))
        self.assertEqual(result["tensor"]["state"], EvidenceState.DECLARED.value)

    def test_code_generation_creates_python_file(self):
        memory = object()
        engine = CreativeEngine(memory)
        result = engine.create("Create a safe helper that sums numbers", modality="code", seed=5, style="utility", author="tester")
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["modality"], "code")
        self.assertTrue(result["output_path"].endswith(".py"))
        self.assertEqual(result["tensor"]["state"], EvidenceState.DECLARED.value)

    def test_video_generation_creates_manifest(self):
        memory = object()
        engine = CreativeEngine(memory)
        result = engine.create("A calm orbiting shape sequence", modality="video", seed=9, style="loop", author="tester")
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["modality"], "video")
        self.assertTrue(result["output_path"].endswith("manifest.json"))
        self.assertEqual(result["tensor"]["state"], EvidenceState.DECLARED.value)

    def test_three_d_generation_creates_obj(self):
        memory = object()
        engine = CreativeEngine(memory)
        result = engine.create("A small verified cube", modality="3d", seed=13, style="mesh", author="tester")
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["modality"], "cad")
        self.assertTrue(result["output_path"].endswith(".obj"))
        self.assertEqual(result["tensor"]["state"], EvidenceState.DECLARED.value)

    def test_nsfw_prompt_is_rejected(self):
        memory = object()
        engine = CreativeEngine(memory)
        result = engine.create("explicit content", modality="image", seed=1)
        self.assertEqual(result["status"], "rejected_prompt")


class CreativeApiTests(unittest.TestCase):
    def _server_for(self):
        app = NeuCLXApplication(Path("/tmp/neuclx_test_creative.sqlite3"))
        handler = handler_factory(app)
        server = __import__("http.server").server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
        port = server.server_address[1]
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        return server, app, port, thread

    def test_create_endpoint(self):
        server, app, port, thread = self._server_for()
        try:
            payload = json.dumps({"prompt": "A blue circle and red bars", "modality": "image", "seed": 7, "style": "bold", "author": "tester"}).encode("utf-8")
            req = request.Request(
                f"http://127.0.0.1:{port}/api/v1/create",
                data=payload,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with request.urlopen(req, timeout=5) as response:
                result = json.loads(response.read().decode("utf-8"))
            self.assertEqual(response.status, 200)
            self.assertEqual(result["status"], "ok")
            self.assertEqual(result["modality"], "image")
            self.assertTrue(result["output_path"].endswith(".svg"))
            self.assertEqual(result["tensor"]["state"], EvidenceState.DECLARED.value)
        finally:
            server.shutdown()
            server.server_close()
            app.close()
            thread.join(timeout=5)

    def test_create_text_endpoint(self):
        server, app, port, thread = self._server_for()
        try:
            payload = json.dumps({"prompt": "Write a short poetic note about a verifiable system", "modality": "text", "seed": 11, "style": "poetic", "author": "tester"}).encode("utf-8")
            req = request.Request(
                f"http://127.0.0.1:{port}/api/v1/create",
                data=payload,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with request.urlopen(req, timeout=5) as response:
                result = json.loads(response.read().decode("utf-8"))
            self.assertEqual(response.status, 200)
            self.assertEqual(result["status"], "ok")
            self.assertEqual(result["modality"], "text")
            self.assertIn("output_text", result)
            self.assertEqual(result["tensor"]["state"], EvidenceState.DECLARED.value)
        finally:
            server.shutdown()
            server.server_close()
            app.close()
            thread.join(timeout=5)

    def test_create_audio_endpoint(self):
        server, app, port, thread = self._server_for()
        try:
            payload = json.dumps({"prompt": "Soothing ambient tone for a calm system", "modality": "audio", "seed": 21, "style": "ambient", "author": "tester"}).encode("utf-8")
            req = request.Request(
                f"http://127.0.0.1:{port}/api/v1/create",
                data=payload,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with request.urlopen(req, timeout=5) as response:
                result = json.loads(response.read().decode("utf-8"))
            self.assertEqual(response.status, 200)
            self.assertEqual(result["status"], "ok")
            self.assertEqual(result["modality"], "audio")
            self.assertTrue(result["output_path"].endswith(".wav"))
        finally:
            server.shutdown()
            server.server_close()
            app.close()
            thread.join(timeout=5)

    def test_create_code_endpoint(self):
        server, app, port, thread = self._server_for()
        try:
            payload = json.dumps({"prompt": "Create a safe helper that sums numbers", "modality": "code", "seed": 5, "style": "utility", "author": "tester"}).encode("utf-8")
            req = request.Request(
                f"http://127.0.0.1:{port}/api/v1/create",
                data=payload,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with request.urlopen(req, timeout=5) as response:
                result = json.loads(response.read().decode("utf-8"))
            self.assertEqual(response.status, 200)
            self.assertEqual(result["status"], "ok")
            self.assertEqual(result["modality"], "code")
            self.assertTrue(result["output_path"].endswith(".py"))
        finally:
            server.shutdown()
            server.server_close()
            app.close()
            thread.join(timeout=5)

    def test_create_video_endpoint(self):
        server, app, port, thread = self._server_for()
        try:
            payload = json.dumps({"prompt": "A calm orbiting shape sequence", "modality": "video", "seed": 9, "style": "loop", "author": "tester"}).encode("utf-8")
            req = request.Request(
                f"http://127.0.0.1:{port}/api/v1/create",
                data=payload,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with request.urlopen(req, timeout=5) as response:
                result = json.loads(response.read().decode("utf-8"))
            self.assertEqual(response.status, 200)
            self.assertEqual(result["status"], "ok")
            self.assertEqual(result["modality"], "video")
            self.assertTrue(result["output_path"].endswith("manifest.json"))
        finally:
            server.shutdown()
            server.server_close()
            app.close()
            thread.join(timeout=5)

    def test_create_three_d_endpoint(self):
        server, app, port, thread = self._server_for()
        try:
            payload = json.dumps({"prompt": "A small verified cube", "modality": "3d", "seed": 13, "style": "mesh", "author": "tester"}).encode("utf-8")
            req = request.Request(
                f"http://127.0.0.1:{port}/api/v1/create",
                data=payload,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with request.urlopen(req, timeout=5) as response:
                result = json.loads(response.read().decode("utf-8"))
            self.assertEqual(response.status, 200)
            self.assertEqual(result["status"], "ok")
            self.assertEqual(result["modality"], "cad")
            self.assertTrue(result["output_path"].endswith(".obj"))
        finally:
            server.shutdown()
            server.server_close()
            app.close()
            thread.join(timeout=5)


if __name__ == "__main__":
    unittest.main()