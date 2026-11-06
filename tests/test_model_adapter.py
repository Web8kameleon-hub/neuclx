import json
import os
from urllib.error import HTTPError
import unittest
from unittest.mock import patch

from neuclx.evidence import EvidenceState
from neuclx.jona import JonaSandbox, PolicyDecision
from neuclx.model_adapter import ModelAdapter


class FakeResponse:
    def __init__(self, value):
        self.body = json.dumps(value).encode("utf-8")

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self, size):
        return self.body[:size]


class FakeOpener:
    def __init__(self, response=None, error=None):
        self.response = response
        self.error = error
        self.requests = []

    def open(self, request, timeout):
        self.requests.append((request, timeout))
        if self.error:
            raise self.error
        return self.response


def enabled_local_adapter(sandbox=None):
    return ModelAdapter(
        provider="local",
        model_name="test-model",
        enabled=True,
        endpoint="http://127.0.0.1:8000/v1/chat/completions",
        sandbox=sandbox,
    )


class ModelAdapterTests(unittest.TestCase):
    def test_model_adapter_without_backend_is_not_implemented(self):
        adapter = ModelAdapter(provider="external", model_name=None, enabled=False)
        result = adapter.generate("hello")

        self.assertEqual(result.state, EvidenceState.NOT_IMPLEMENTED)
        self.assertIsNone(result.value)

    def test_environment_configuration_is_opt_in_and_explicit(self):
        with patch.dict(os.environ, {}, clear=True):
            self.assertFalse(ModelAdapter.from_environment().enabled)

            os.environ["NEUCLX_MODEL_ENABLED"] = "true"
            with self.assertRaisesRegex(ValueError, "NAME and NEUCLX_MODEL_ENDPOINT"):
                ModelAdapter.from_environment()

            os.environ["NEUCLX_MODEL_PROVIDER"] = "hosted"
            os.environ["NEUCLX_MODEL_NAME"] = "test-model"
            os.environ["NEUCLX_MODEL_ENDPOINT"] = "https://models.example/v1/chat/completions"
            os.environ["NEUCLX_MODEL_API_KEY_ENV"] = "NEUCLX_TEST_API_KEY"
            adapter = ModelAdapter.from_environment()
            self.assertTrue(adapter.enabled)
            self.assertEqual(adapter.provider, "hosted")
            self.assertEqual(adapter.api_key_env, "NEUCLX_TEST_API_KEY")

    def test_local_endpoint_is_explicit_and_output_is_jona_checked(self):
        class TrackingSandbox(JonaSandbox):
            def __init__(self):
                object.__setattr__(self, "checked", [])

            def evaluate(self, datum):
                self.checked.append(datum)
                return super().evaluate(datum)

        sandbox = TrackingSandbox()
        adapter = enabled_local_adapter(sandbox)
        opener = FakeOpener(FakeResponse({"choices": [{"message": {"content": "hello"}}]}))
        adapter._opener = opener

        result = adapter.generate("prompt")

        self.assertEqual(result.state, EvidenceState.COMPUTED)
        self.assertEqual(result.value, "hello")
        self.assertEqual(result.method, "openai-compatible-chat-completions-v1")
        self.assertEqual(
            [datum.method for datum in sandbox.checked],
            [
                "openai-compatible-request-v1",
                "openai-compatible-chat-completions-v1",
                "openai-compatible-chat-completions-v1",
            ],
        )
        self.assertEqual(
            json.loads(opener.requests[0][0].data)["messages"][0]["content"],
            "prompt",
        )
        self.assertEqual(opener.requests[0][1], 30.0)

    def test_hosted_endpoint_requires_explicit_https_and_keeps_secret_out_of_result(self):
        with patch.dict(os.environ, {"NEUCLX_TEST_API_KEY": "never-return-this"}):
            adapter = ModelAdapter(
                provider="hosted",
                model_name="hosted-model",
                enabled=True,
                endpoint="https://models.example/v1/chat/completions",
                api_key_env="NEUCLX_TEST_API_KEY",
            )
            opener = FakeOpener(FakeResponse({"choices": [{"message": {"content": "answer"}}]}))
            adapter._opener = opener

            result = adapter.generate("question")

        request = opener.requests[0][0]
        self.assertEqual(request.get_header("Authorization"), "Bearer never-return-this")
        self.assertEqual(result.value, "answer")
        self.assertNotIn("never-return-this", repr(result.as_dict()))

    def test_disabled_adapter_never_contacts_an_endpoint(self):
        adapter = ModelAdapter(
            provider="hosted",
            model_name="hosted-model",
            enabled=False,
            endpoint="https://models.example/v1/chat/completions",
        )
        opener = FakeOpener(FakeResponse({"choices": []}))
        adapter._opener = opener

        result = adapter.generate("question")

        self.assertEqual(result.state, EvidenceState.NOT_IMPLEMENTED)
        self.assertEqual(opener.requests, [])

    def test_enabled_adapter_rejects_missing_model_name(self):
        adapter = ModelAdapter(
            provider="local",
            enabled=True,
            endpoint="http://127.0.0.1:8000/v1/chat/completions",
        )
        with self.assertRaisesRegex(ValueError, "model_name is required"):
            adapter.generate("question")

    def test_jona_rejection_prevents_request(self):
        class RejectRequest(JonaSandbox):
            def evaluate(self, datum):
                if datum.method == "openai-compatible-request-v1":
                    return PolicyDecision.REJECT
                return super().evaluate(datum)

        adapter = enabled_local_adapter(RejectRequest())
        opener = FakeOpener(FakeResponse({"choices": [{"message": {"content": "no"}}]}))
        adapter._opener = opener

        with self.assertRaises(PermissionError):
            adapter.generate("prompt")
        self.assertEqual(opener.requests, [])

    def test_jona_can_hold_request_or_reject_model_output(self):
        class HoldRequest(JonaSandbox):
            def evaluate(self, datum):
                if datum.method == "openai-compatible-request-v1":
                    return PolicyDecision.SANDBOX_ONLY
                return super().evaluate(datum)

        held_adapter = enabled_local_adapter(HoldRequest())
        held_opener = FakeOpener(FakeResponse({"choices": [{"message": {"content": "no"}}]}))
        held_adapter._opener = held_opener
        held = held_adapter.generate("prompt")
        self.assertEqual(held.state, EvidenceState.UNAVAILABLE)
        self.assertEqual(held_opener.requests, [])

        class RejectOutput(JonaSandbox):
            def evaluate(self, datum):
                if datum.method == "openai-compatible-chat-completions-v1":
                    return PolicyDecision.REJECT
                return super().evaluate(datum)

        rejected_adapter = enabled_local_adapter(RejectOutput())
        rejected_adapter._opener = FakeOpener(FakeResponse({"choices": [{"message": {"content": "unsafe"}}]}))
        with self.assertRaises(PermissionError):
            rejected_adapter.generate("prompt")

    def test_endpoint_policy_rejects_untrusted_config(self):
        cases = [
            ("local", "http://192.0.2.1/v1/chat/completions"),
            ("local", "https://models.example/v1/chat/completions"),
            ("hosted", "http://models.example/v1/chat/completions"),
            ("hosted", "******models.example/v1/chat/completions"),
            ("hosted", "https://models.example/v1/chat/completions?key=secret"),
        ]
        for provider, endpoint in cases:
            with self.subTest(provider=provider, endpoint=endpoint):
                adapter = ModelAdapter(provider, "model", True, endpoint=endpoint)
                with self.assertRaises(ValueError):
                    adapter.generate("prompt")

    def test_endpoint_errors_are_explicit_and_do_not_fall_back(self):
        adapter = enabled_local_adapter()
        adapter._opener = FakeOpener(error=HTTPError(adapter.endpoint, 429, "rate limited", hdrs=None, fp=None))

        with self.assertRaisesRegex(RuntimeError, "HTTP 429"):
            adapter.generate("prompt")

    def test_invalid_response_contract_is_not_replaced(self):
        adapter = enabled_local_adapter()
        adapter._opener = FakeOpener(FakeResponse({"choices": []}))

        with self.assertRaisesRegex(ValueError, "chat-completions contract"):
            adapter.generate("prompt")


if __name__ == "__main__":
    unittest.main()
