import json
import threading
import unittest
from pathlib import Path
from urllib import request, error

from neuclx.web import NeuCLXApplication, handler_factory


class ApiV1RouteTests(unittest.TestCase):
    def _server_for(self):
        app = NeuCLXApplication(Path("/tmp/neuclx_test_api.sqlite3"))
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


if __name__ == "__main__":
    unittest.main()
