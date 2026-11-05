import json
from urllib.error import HTTPError
from unittest.mock import patch

import pytest

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


def test_model_adapter_without_backend_is_not_implemented():
    adapter = ModelAdapter(provider="external", model_name=None, enabled=False)
    result = adapter.generate("hello")

    assert result.state is EvidenceState.NOT_IMPLEMENTED
    assert result.value is None


def test_environment_configuration_is_opt_in_and_explicit(monkeypatch):
    for name in (
        "NEUCLX_MODEL_ENABLED",
        "NEUCLX_MODEL_PROVIDER",
        "NEUCLX_MODEL_NAME",
        "NEUCLX_MODEL_ENDPOINT",
        "NEUCLX_MODEL_API_KEY_ENV",
        "NEUCLX_MODEL_TIMEOUT",
    ):
        monkeypatch.delenv(name, raising=False)
    assert ModelAdapter.from_environment().enabled is False

    monkeypatch.setenv("NEUCLX_MODEL_ENABLED", "true")
    with pytest.raises(ValueError, match="NAME and NEUCLX_MODEL_ENDPOINT"):
        ModelAdapter.from_environment()

    monkeypatch.setenv("NEUCLX_MODEL_PROVIDER", "hosted")
    monkeypatch.setenv("NEUCLX_MODEL_NAME", "test-model")
    monkeypatch.setenv("NEUCLX_MODEL_ENDPOINT", "https://models.example/v1/chat/completions")
    monkeypatch.setenv("NEUCLX_MODEL_API_KEY_ENV", "NEUCLX_TEST_API_KEY")
    adapter = ModelAdapter.from_environment()
    assert adapter.enabled is True
    assert adapter.provider == "hosted"
    assert adapter.api_key_env == "NEUCLX_TEST_API_KEY"


def test_local_endpoint_is_explicit_and_output_is_jona_checked():
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

    assert result.state is EvidenceState.COMPUTED
    assert result.value == "hello"
    assert result.method == "openai-compatible-chat-completions-v1"
    assert [datum.method for datum in sandbox.checked] == [
        "openai-compatible-request-v1",
        "openai-compatible-chat-completions-v1",
        "openai-compatible-chat-completions-v1",
    ]
    assert json.loads(opener.requests[0][0].data)["messages"][0]["content"] == "prompt"
    assert opener.requests[0][1] == 30.0


def test_hosted_endpoint_requires_explicit_https_and_keeps_secret_out_of_result(monkeypatch):
    monkeypatch.setenv("NEUCLX_TEST_API_KEY", "never-return-this")
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
    assert request.get_header("Authorization") == "Bearer never-return-this"
    assert result.value == "answer"
    assert "never-return-this" not in repr(result.as_dict())


def test_disabled_adapter_never_contacts_an_endpoint():
    adapter = ModelAdapter(
        provider="hosted",
        model_name="hosted-model",
        enabled=False,
        endpoint="https://models.example/v1/chat/completions",
    )
    opener = FakeOpener(FakeResponse({"choices": []}))
    adapter._opener = opener

    result = adapter.generate("question")

    assert result.state is EvidenceState.NOT_IMPLEMENTED
    assert opener.requests == []


def test_enabled_adapter_rejects_missing_model_name():
    adapter = ModelAdapter(
        provider="local",
        enabled=True,
        endpoint="http://127.0.0.1:8000/v1/chat/completions",
    )
    with pytest.raises(ValueError, match="model_name is required"):
        adapter.generate("question")


def test_jona_rejection_prevents_request():
    class RejectRequest(JonaSandbox):
        def evaluate(self, datum):
            if datum.method == "openai-compatible-request-v1":
                return PolicyDecision.REJECT
            return super().evaluate(datum)

    adapter = enabled_local_adapter(RejectRequest())
    opener = FakeOpener(FakeResponse({"choices": [{"message": {"content": "no"}}]}))
    adapter._opener = opener

    with pytest.raises(PermissionError):
        adapter.generate("prompt")
    assert opener.requests == []


def test_jona_can_hold_request_or_reject_model_output():
    class HoldRequest(JonaSandbox):
        def evaluate(self, datum):
            if datum.method == "openai-compatible-request-v1":
                return PolicyDecision.SANDBOX_ONLY
            return super().evaluate(datum)

    held_adapter = enabled_local_adapter(HoldRequest())
    held_opener = FakeOpener(FakeResponse({"choices": [{"message": {"content": "no"}}]}))
    held_adapter._opener = held_opener
    held = held_adapter.generate("prompt")
    assert held.state is EvidenceState.UNAVAILABLE
    assert held_opener.requests == []

    class RejectOutput(JonaSandbox):
        def evaluate(self, datum):
            if datum.method == "openai-compatible-chat-completions-v1":
                return PolicyDecision.REJECT
            return super().evaluate(datum)

    rejected_adapter = enabled_local_adapter(RejectOutput())
    rejected_adapter._opener = FakeOpener(
        FakeResponse({"choices": [{"message": {"content": "unsafe"}}]})
    )
    with pytest.raises(PermissionError):
        rejected_adapter.generate("prompt")


@pytest.mark.parametrize(
    ("provider", "endpoint"),
    [
        ("local", "http://192.0.2.1/v1/chat/completions"),
        ("local", "https://models.example/v1/chat/completions"),
        ("hosted", "http://models.example/v1/chat/completions"),
        ("hosted", "https://user:pass@models.example/v1/chat/completions"),
        ("hosted", "https://models.example/v1/chat/completions?key=secret"),
    ],
)
def test_endpoint_policy_rejects_untrusted_config(provider, endpoint):
    adapter = ModelAdapter(provider, "model", True, endpoint=endpoint)
    with pytest.raises(ValueError):
        adapter.generate("prompt")


def test_endpoint_errors_are_explicit_and_do_not_fall_back():
    adapter = enabled_local_adapter()
    adapter._opener = FakeOpener(error=HTTPError(
        adapter.endpoint, 429, "rate limited", hdrs=None, fp=None
    ))

    with pytest.raises(RuntimeError, match="HTTP 429"):
        adapter.generate("prompt")


def test_invalid_response_contract_is_not_replaced():
    adapter = enabled_local_adapter()
    adapter._opener = FakeOpener(FakeResponse({"choices": []}))

    with pytest.raises(ValueError, match="chat-completions contract"):
        adapter.generate("prompt")
