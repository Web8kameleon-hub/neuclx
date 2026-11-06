import unittest

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


class PipelineTests(unittest.TestCase):
    def test_pipeline_runs_registered_stages_and_preserves_provenance(self):
        definition = pipeline(
            PipelineStage("uppercase", "stage-v1", lambda item: Datum(
                item.value.upper(), EvidenceState.COMPUTED, method="uppercase"
            )),
            PipelineStage("suffix", "stage-v2", lambda item: Datum(
                item.value + "!", EvidenceState.COMPUTED, method="suffix"
            )),
        )

        result = PipelineRunner().run(definition, measured_input())

        self.assertEqual(result.value, "INPUT!")
        self.assertEqual(result.state, EvidenceState.COMPUTED)
        self.assertEqual(result.metadata["pipeline"], "test-pipeline")
        self.assertEqual(
            [stage["name"] for stage in result.metadata["stages"]],
            ["uppercase", "suffix"],
        )
        self.assertEqual(
            [stage["revision"] for stage in result.metadata["stages"]],
            ["stage-v1", "stage-v2"],
        )

    def test_jona_holds_unapproved_input_before_any_stage(self):
        called = []
        definition = pipeline(PipelineStage("stage", "v1", lambda item: called.append(item)))

        result = PipelineRunner().run(
            definition,
            Datum("user text", EvidenceState.DECLARED, "user", "input"),
        )

        self.assertEqual(result.state, EvidenceState.UNAVAILABLE)
        self.assertEqual(called, [])
        self.assertEqual(result.metadata["jona_decision"], PolicyDecision.SANDBOX_ONLY.value)

    def test_jona_rejection_stops_before_stage_execution(self):
        class RejectInput(JonaSandbox):
            def evaluate(self, datum):
                if datum.method == "fixture":
                    return PolicyDecision.REJECT
                return super().evaluate(datum)

        called = []
        runner = PipelineRunner(RejectInput())
        definition = pipeline(PipelineStage("stage", "v1", lambda item: called.append(item)))

        with self.assertRaises(PermissionError):
            runner.run(definition, measured_input())
        self.assertEqual(called, [])

    def test_jona_rejection_of_stage_output_prevents_following_stage(self):
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

        with self.assertRaises(PermissionError):
            PipelineRunner(RejectOutput()).run(definition, measured_input())
        self.assertEqual(called, [])

    def test_pipeline_surfaces_invalid_stage_results_and_exceptions(self):
        definition = pipeline(PipelineStage("invalid", "v1", lambda item: {"value": item.value}))
        with self.assertRaisesRegex(TypeError, "must return Datum"):
            PipelineRunner().run(definition, measured_input())

        def broken(item):
            raise RuntimeError("stage failed")

        definition = pipeline(PipelineStage("broken", "v1", broken))
        with self.assertRaisesRegex(RuntimeError, "stage failed"):
            PipelineRunner().run(definition, measured_input())

    def test_pipeline_definition_requires_unique_stages_and_pinned_bindings(self):
        with self.assertRaisesRegex(ValueError, "at least one"):
            pipeline()
        with self.assertRaisesRegex(ValueError, "unique"):
            pipeline(
                PipelineStage("same", "v1", lambda item: item),
                PipelineStage("same", "v2", lambda item: item),
            )
        with self.assertRaisesRegex(ValueError, "revision"):
            PipelineStage("stage", "", lambda item: item)


if __name__ == "__main__":
    unittest.main()
