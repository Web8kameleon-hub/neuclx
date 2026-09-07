from neuclx.evidence import EvidenceState
from neuclx.model_adapter import ModelAdapter


def test_model_adapter_without_backend_is_not_implemented():
    adapter = ModelAdapter(provider="external", model_name=None, enabled=False)
    result = adapter.generate("hello")

    assert result.state is EvidenceState.NOT_IMPLEMENTED
    assert result.value is None


def test_model_adapter_returns_computed_output_for_local_backend():
    adapter = ModelAdapter(provider="local", model_name="hash-demo", enabled=True)
    result = adapter.generate("hello world")

    assert result.state is EvidenceState.COMPUTED
    assert isinstance(result.value, str)
    assert result.method == "sha256-deterministic"
