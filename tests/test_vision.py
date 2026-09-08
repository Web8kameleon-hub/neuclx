from __future__ import annotations

import base64
import json
import threading
import unittest
from pathlib import Path
from urllib import request

from neuclx.vision_encoder import VisionEncoder
from neuclx.web import NeuCLXApplication, handler_factory


PNG_1X1_BASE64 = (
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO5Y8ZkAAAAASUVORK5CYII="
)


class VisionEncoderTests(unittest.TestCase):
    def test_inspect_png_path(self):
        encoder = VisionEncoder()
        png_bytes = base64.b64decode(PNG_1X1_BASE64)
        temp_path = Path(__file__).with_name("_vision_fixture.png")
        temp_path.write_bytes(png_bytes)
        try:
            datum = encoder.inspect_path(temp_path, author="tester", task="inspect logo")
            self.assertEqual(datum.state.value, "measured")
            self.assertEqual(datum.method, "vision:header-inspection")
            self.assertEqual(datum.value["format"], "png")
            self.assertEqual(datum.value["width"], 1)
            self.assertEqual(datum.value["height"], 1)
            self.assertEqual(datum.metadata["format"], "png")
        finally:
            if temp_path.exists():
                temp_path.unlink()


class VisionApiTests(unittest.TestCase):
    def _server_for(self):
        app = NeuCLXApplication(Path("/tmp/neuclx_test_vision.sqlite3"))
        handler = handler_factory(app)
        server = __import__("http.server").server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
        port = server.server_address[1]
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        return server, app, port, thread

    def test_vision_inspect_route(self):
        png_bytes = base64.b64decode(PNG_1X1_BASE64)
        temp_path = Path(__file__).with_name("_vision_api_fixture.png")
        temp_path.write_bytes(png_bytes)
        server, app, port, thread = self._server_for()
        try:
            payload = json.dumps({"task": "Inspect image", "image_path": str(temp_path), "author": "tester"}).encode("utf-8")
            req = request.Request(
                f"http://127.0.0.1:{port}/api/v1/vision/inspect",
                data=payload,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with request.urlopen(req, timeout=5) as response:
                result = json.loads(response.read().decode("utf-8"))
            self.assertEqual(response.status, 200)
            self.assertEqual(result["status"], "ok")
            self.assertEqual(result["image"]["format"], "png")
            self.assertEqual(result["datum"]["state"], "measured")
            self.assertEqual(result["evidence_chain"][0]["metadata"]["format"], "png")
        finally:
            server.shutdown()
            server.server_close()
            app.close()
            thread.join(timeout=5)
            if temp_path.exists():
                temp_path.unlink()


if __name__ == "__main__":
    unittest.main()