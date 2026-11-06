"""Explicit, JONA-gated pipeline stages with no dynamic code loading."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from .evidence import Datum, EvidenceState
from .jona import JonaSandbox, PolicyDecision


@dataclass(frozen=True, slots=True)
class PipelineStage:
    name: str
    revision: str
    execute: Callable[[Datum], Datum]

    def __post_init__(self):
        if not isinstance(self.name, str) or not self.name.strip():
            raise ValueError("stage name is required")
        if not isinstance(self.revision, str) or not self.revision.strip():
            raise ValueError("stage revision is required")
        if not callable(self.execute):
            raise TypeError("stage execute binding must be callable")


@dataclass(frozen=True, slots=True)
class PipelineDefinition:
    name: str
    source: str
    revision: str
    stages: tuple[PipelineStage, ...]

    def __post_init__(self):
        for field_name in ("name", "source", "revision"):
            value = getattr(self, field_name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"pipeline {field_name} is required")
        if not isinstance(self.stages, tuple) or not self.stages:
            raise ValueError("pipeline requires at least one stage")
        if any(not isinstance(stage, PipelineStage) for stage in self.stages):
            raise TypeError("pipeline stages must be PipelineStage values")
        names = [stage.name for stage in self.stages]
        if len(set(names)) != len(names):
            raise ValueError("pipeline stage names must be unique")


class PipelineRunner:
    """Run only explicitly registered callables; every stage crosses JONA."""

    def __init__(self, sandbox: JonaSandbox | None = None):
        self.sandbox = sandbox if sandbox is not None else JonaSandbox()

    def run(self, pipeline: PipelineDefinition, value: Datum) -> Datum:
        if not isinstance(pipeline, PipelineDefinition):
            raise TypeError("PipelineDefinition is required")
        if not isinstance(value, Datum):
            raise TypeError("pipeline input must be a Datum")

        current = value
        trace = []
        for stage in pipeline.stages:
            input_decision = self.sandbox.evaluate(current)
            if input_decision is PolicyDecision.REJECT:
                self.sandbox.release(current)
            if input_decision is not PolicyDecision.ALLOW:
                return self._held(pipeline, stage.name, "input", input_decision, trace)

            output = stage.execute(current)
            if not isinstance(output, Datum):
                raise TypeError(f"stage {stage.name} must return Datum")
            output_decision = self.sandbox.evaluate(output)
            if output_decision is PolicyDecision.REJECT:
                self.sandbox.release(output)
            trace.append(
                {
                    "name": stage.name,
                    "revision": stage.revision,
                    "input_state": current.state.value,
                    "output_state": output.state.value,
                    "jona_decision": output_decision.value,
                }
            )
            if output_decision is not PolicyDecision.ALLOW:
                return self._held(pipeline, stage.name, "output", output_decision, trace)
            current = self.sandbox.release(output)

        result = Datum(
            current.value,
            current.state,
            current.source,
            current.method,
            {
                **current.metadata,
                "pipeline": pipeline.name,
                "pipeline_source": pipeline.source,
                "pipeline_revision": pipeline.revision,
                "stages": trace,
            },
        )
        decision = self.sandbox.evaluate(result)
        if decision is PolicyDecision.REJECT:
            self.sandbox.release(result)
        if decision is not PolicyDecision.ALLOW:
            return self._held(pipeline, "release", "output", decision, trace)
        return self.sandbox.release(result)

    def _held(
        self,
        pipeline: PipelineDefinition,
        stage_name: str,
        direction: str,
        decision: PolicyDecision,
        trace: list[dict],
    ) -> Datum:
        held = Datum(
            None,
            EvidenceState.UNAVAILABLE,
            method="pipeline-jona-held",
            metadata={
                "pipeline": pipeline.name,
                "pipeline_source": pipeline.source,
                "pipeline_revision": pipeline.revision,
                "stage": stage_name,
                "direction": direction,
                "jona_decision": decision.value,
                "stages": trace,
            },
        )
        return self.sandbox.release(held)
