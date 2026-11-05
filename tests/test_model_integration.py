import json
from pathlib import Path

from neuclx.evidence import Datum, EvidenceState
from neuclx.web import NeuCLXApplication


class StubModel:
    enabled = True

    def __init__(self):
        self.prompts = []

    def generate(self, prompt):
        self.prompts.append(prompt)
        return Datum(
            "Përgjigje e gjeneruar.",
            EvidenceState.COMPUTED,
            source="local:test-model",
            method="test-model",
            metadata={"output_sha256": "test-digest"},
        )


def test_chat_and_reasoning_route_explicit_model_output(tmp_path):
    app = NeuCLXApplication(Path(tmp_path) / "journey.sqlite3")
    model = StubModel()
    app.model_adapter = model
    app.reasoning_engine.model = model
    try:
        chat = app.respond("Pyetje bisede", source_urls=[])
        assert chat["response"]["state"] == "computed"
        assert chat["response"]["value"] == "Përgjigje e gjeneruar."
        assert chat["response"]["metadata"]["retrieval_state"] == "unavailable"
        assert "Model-generated response" in chat["response"]["metadata"]["claim_status"]

        result = app.reason("Kush je ti?", source_urls=[])
        assert result["assistant_response"]["state"] == "computed"
        assert result["assistant_response"]["value"] == "Përgjigje e gjeneruar."
        assert "Kush je ti?" in json.loads(model.prompts[-1].split("context (JSON):\n", 1)[1])["question"]
        assert "Nuk ka evidencë të disponueshme" in result["conclusion"]
    finally:
        app.close()
