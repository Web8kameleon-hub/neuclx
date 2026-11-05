import pytest

from neuclx.evidence import Datum, EvidenceState
from neuclx.jona import JonaSandbox, PolicyDecision
from neuclx.pipeline import PipelineDefinition, PipelineRunner, PipelineStage


def pipeline(*stages):
    return PipelineDefinition(
        name="test-pipeline",
        source="neuclx-native",
        revision="test-v1",
        stages=tuple(stages),
    )


def measured_input(value="input"):
    return Datum(value, EvidenceState.MEASURED, "test-source", "fixture")


def test_pipeline_runs_registered_stages_and_preserves_provenance():
    definition = pipeline(
        PipelineStage("uppercase", "stage-v1", lambda item: Datum(
            item.value.upper(), EvidenceState.COMPUTED, method="uppercase"
        )),
        PipelineStage("suffix", "stage-v2", lambda item: Datum(
            item.value + "!", EvidenceState.COMPUTED, method="suffix"
        )),
    )

    result = PipelineRunner().run(definition, measured_input())

    assert result.value == "INPUT!"
    assert result.state is EvidenceState.COMPUTED
    assert result.metadata["pipeline"] == "test-pipeline"
    assert [stage["name"] for stage in result.metadata["stages"]] == ["uppercase", "suffix"]
    assert [stage["revision"] for stage in result.metadata["stages"]] == ["stage-v1", "stage-v2"]


def test_jona_holds_unapproved_input_before_any_stage():
    called = []
    definition = pipeline(PipelineStage("stage", "v1", lambda item: called.append(item)))

    result = PipelineRunner().run(
        definition,
        Datum("user text", EvidenceState.DECLARED, "user", "input"),
    )

    assert result.state is EvidenceState.UNAVAILABLE
    assert called == []
    assert result.metadata["jona_decision"] == PolicyDecision.SANDBOX_ONLY.value


def test_jona_rejection_stops_before_stage_execution():
    class RejectInput(JonaSandbox):
        def evaluate(self, datum):
            if datum.method == "fixture":
                return PolicyDecision.REJECT
            return super().evaluate(datum)

    called = []
    runner = PipelineRunner(RejectInput())
    definition = pipeline(PipelineStage("stage", "v1", lambda item: called.append(item)))

    with pytest.raises(PermissionError):
        runner.run(definition, measured_input())
    assert called == []


def test_jona_rejection_of_stage_output_prevents_following_stage():
    class RejectOutput(JonaSandbox):
        def evaluate(self, datum):
            if datum.method == "rejected-output":
                return PolicyDecision.REJECT
            return super().evaluate(datum)

    called = []
    definition = pipeline(
        PipelineStage("first", "v1", lambda item: Datum(
            item.value, EvidenceState.COMPUTED, method="rejected-output"
        )),
        PipelineStage("second", "v1", lambda item: called.append(item)),
    )

    with pytest.raises(PermissionError):
        PipelineRunner(RejectOutput()).run(definition, measured_input())
    assert called == []


def test_pipeline_surfaces_invalid_stage_results_and_exceptions():
    definition = pipeline(PipelineStage("invalid", "v1", lambda item: {"value": item.value}))
    with pytest.raises(TypeError, match="must return Datum"):
        PipelineRunner().run(definition, measured_input())

    def broken(item):
        raise RuntimeError("stage failed")

    definition = pipeline(PipelineStage("broken", "v1", broken))
    with pytest.raises(RuntimeError, match="stage failed"):
        PipelineRunner().run(definition, measured_input())


def test_pipeline_definition_requires_unique_stages_and_pinned_bindings():
    with pytest.raises(ValueError, match="at least one"):
        pipeline()
    with pytest.raises(ValueError, match="unique"):
        pipeline(
            PipelineStage("same", "v1", lambda item: item),
            PipelineStage("same", "v2", lambda item: item),
        )
    with pytest.raises(ValueError, match="revision"):
        PipelineStage("stage", "", lambda item: item)
