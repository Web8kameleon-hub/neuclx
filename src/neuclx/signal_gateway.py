"""Explicit signal admission seam for a future GRAM/HVWO pipeline.

Registered callbacks are trusted local code, never loaded from signal contents.
This gateway does not implement the named remote engines or a GRAM graph.
"""

from dataclasses import dataclass
from hashlib import sha256
import json
import math
from typing import Callable

from .evidence import Datum, EvidenceState
from .jona import JonaSandbox, PolicyDecision


REQUIRED_CONTROLS = ('alda', 'mali', 'klajdi', 'liam', 'alba', 'albi',
                     'blerina', 'pillar', 'albana', 'lagter')
MAX_PAYLOAD_BYTES = 1_048_576


@dataclass(frozen=True, slots=True)
class SignalEnvelope:
    kind: str
    payload: bytes
    source: str
    revision: str

    def __post_init__(self):
        if not all(isinstance(value, str) and value.strip()
                   for value in (self.kind, self.source, self.revision)):
            raise ValueError('kind, source and revision are required strings')
        if not isinstance(self.payload, bytes):
            raise TypeError('payload must be immutable bytes')
        if not self.payload or len(self.payload) > MAX_PAYLOAD_BYTES:
            raise ValueError('payload must contain 1 to 1048576 bytes')


class SignalGateway:
    """JONA plus all required controllers must approve before adapter execution.

    No controllers are supplied by default. Registering a callback describes an
    explicit local binding, not proof of a live service or controller quality.
    There is no network access, automatic discovery, fallback, or persistent write.
    """

    def __init__(self, sandbox=None):
        self.sandbox = sandbox if sandbox is not None else JonaSandbox()
        self._controls = {}
        self._adapters = {}

    def register_control(self, name: str, callback: Callable, *, revision: str):
        if name not in REQUIRED_CONTROLS:
            raise ValueError('unknown control')
        self._register(self._controls, name, callback, revision)

    def register_adapter(self, kind: str, callback: Callable, *, revision: str):
        if not isinstance(kind, str) or not kind.strip():
            raise ValueError('adapter kind is required')
        self._register(self._adapters, kind, callback, revision)

    @staticmethod
    def _register(registry, name, callback, revision):
        if not callable(callback) or not isinstance(revision, str) or not revision.strip():
            raise ValueError('callable and explicit revision are required')
        if name in registry:
            raise ValueError('binding already exists')
        registry[name] = (callback, revision)

    def submit(self, signal: SignalEnvelope) -> Datum:
        if not isinstance(signal, SignalEnvelope):
            raise TypeError('SignalEnvelope is required')
        # Only byte count and digest are measured; source assertions stay declared.
        observation = Datum({'sha256': sha256(signal.payload).hexdigest(),
                             'byte_count': len(signal.payload)},
                            EvidenceState.MEASURED, 'signal-gateway:local-bytes',
                            'sha256+byte-count', metadata={
                                'source_claim': {'state': 'declared', 'value': signal.source},
                                'revision_claim': {'state': 'declared', 'value': signal.revision},
                                'kind_claim': {'state': 'declared', 'value': signal.kind}})
        decision = self.sandbox.evaluate(observation)
        self.sandbox.release(observation)
        if decision is not PolicyDecision.ALLOW:
            return self.sandbox.release(Datum(None, EvidenceState.UNAVAILABLE,
                method='signal-input-not-authorized', metadata={'jona_decision': str(decision)}))
        missing = [name for name in REQUIRED_CONTROLS if name not in self._controls]
        if missing or signal.kind not in self._adapters:
            return self.sandbox.release(Datum(None, EvidenceState.NOT_IMPLEMENTED,
                method='signal-bindings-missing', metadata={
                    'missing_controls': missing, 'missing_adapter': signal.kind not in self._adapters}))
        # Snapshot bindings: registration changes cannot change this admission pass.
        controls = [(name, *self._controls[name]) for name in REQUIRED_CONTROLS]
        adapter, adapter_revision = self._adapters[signal.kind]
        approvals = []
        for name, control, revision in controls:
            control_decision = control(signal)
            if not isinstance(control_decision, PolicyDecision):
                raise TypeError(f'{name} must return PolicyDecision')
            approvals.append({'control': name, 'revision': revision,
                              'decision': control_decision.value, 'state': 'computed'})
            if control_decision is PolicyDecision.REJECT:
                raise PermissionError(f'{name} rejected signal')
            if control_decision is PolicyDecision.SANDBOX_ONLY:
                return self.sandbox.release(Datum(None, EvidenceState.UNAVAILABLE,
                    method='signal-review-required', metadata={'controls': approvals}))
        output = adapter(signal)
        if not isinstance(output, Datum):
            raise TypeError('adapter must return Datum')
        # Serialize the output through JONA; never substitute controller success.
        return self.sandbox.release(Datum(output.value, output.state, output.source,
            output.method, {**output.metadata, 'input_observation': observation.as_dict(),
                            'controls': approvals, 'adapter_revision': adapter_revision}))


def text_features(signal: SignalEnvelope) -> Datum:
    """UTF-8 structure only; no semantic understanding or truth verification."""
    text = signal.payload.decode('utf-8', errors='strict')
    return Datum({'characters': len(text), 'words': len(text.split()),
                  'lines': len(text.splitlines())}, EvidenceState.COMPUTED,
                 method='signal:utf8-structure-v1')


def numeric_features(signal: SignalEnvelope) -> Datum:
    """Finite JSON numeric sequences; units and physical meaning are unverified."""
    values = json.loads(signal.payload.decode('utf-8'))
    if not isinstance(values, list) or not values:
        raise ValueError('nonempty JSON numeric array required')
    if any(type(value) not in (int, float) or not math.isfinite(value) for value in values):
        raise ValueError('only finite numbers are accepted')
    return Datum({'samples': len(values), 'minimum': min(values), 'maximum': max(values)},
                 EvidenceState.COMPUTED, method='signal:numeric-range-v1')


def binary_features(signal: SignalEnvelope) -> Datum:
    """Opaque bytes only; not an audio/image/video/EEG decoder."""
    return Datum({'bytes': len(signal.payload), 'sha256': sha256(signal.payload).hexdigest()},
                 EvidenceState.COMPUTED, method='signal:opaque-bytes-v1')
