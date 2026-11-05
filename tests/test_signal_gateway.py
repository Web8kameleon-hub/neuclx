import unittest

from neuclx.evidence import Datum, EvidenceState
from neuclx.jona import JonaSandbox, PolicyDecision
from neuclx.signal_gateway import (MAX_PAYLOAD_BYTES, REQUIRED_CONTROLS,
    SignalEnvelope, SignalGateway, binary_features, numeric_features, text_features)


class SignalGatewayTests(unittest.TestCase):
    def envelope(self, payload=b'JONA sandbox', kind='text'):
        return SignalEnvelope(kind, payload, 'fixture:local', 'test-v1')

    def bound_gateway(self, adapter=text_features, kind='text', sandbox=None):
        gateway = SignalGateway(sandbox)
        # Synthetic controls test the contract, not the real named engines.
        for name in REQUIRED_CONTROLS:
            gateway.register_control(name, lambda signal: PolicyDecision.ALLOW,
                                     revision='synthetic-test-v1')
        gateway.register_adapter(kind, adapter, revision='test-adapter-v1')
        return gateway

    def test_missing_bindings_never_report_success(self):
        result = SignalGateway().submit(self.envelope())
        self.assertEqual(result.state, EvidenceState.NOT_IMPLEMENTED)
        self.assertIsNone(result.value)
        self.assertEqual(result.metadata['missing_controls'], list(REQUIRED_CONTROLS))

    def test_every_required_controller_can_veto_before_adapter(self):
        for rejecting in REQUIRED_CONTROLS:
            with self.subTest(control=rejecting):
                called = []
                gateway = SignalGateway()
                for name in REQUIRED_CONTROLS:
                    decision = PolicyDecision.REJECT if name == rejecting else PolicyDecision.ALLOW
                    gateway.register_control(name, lambda signal, d=decision: d, revision='test-v1')
                gateway.register_adapter('text', lambda signal: called.append(signal), revision='test-v1')
                with self.assertRaises(PermissionError):
                    gateway.submit(self.envelope())
                self.assertEqual(called, [])

    def test_jona_rejection_prevents_controls_and_adapter(self):
        class Deny(JonaSandbox):
            def evaluate(self, datum):
                return PolicyDecision.REJECT
        called = []
        gateway = SignalGateway(Deny())
        gateway.register_control('alda', lambda signal: called.append(signal), revision='test-v1')
        with self.assertRaises(PermissionError):
            gateway.submit(self.envelope())
        self.assertEqual(called, [])

    def test_jona_can_reject_final_output(self):
        class RejectOutput(JonaSandbox):
            def evaluate(self, datum):
                return PolicyDecision.REJECT if datum.state is EvidenceState.COMPUTED else super().evaluate(datum)
        gateway = self.bound_gateway(sandbox=RejectOutput())
        with self.assertRaises(PermissionError):
            gateway.submit(self.envelope())

    def test_text_numeric_binary_features_keep_provenance(self):
        for kind, payload, adapter in [('text', 'kujtesë'.encode(), text_features),
                                       ('numeric', b'[1, -2, 3.5]', numeric_features),
                                       ('binary', b'\x00\xff', binary_features)]:
            with self.subTest(kind=kind):
                result = self.bound_gateway(adapter, kind).submit(self.envelope(payload, kind))
                self.assertEqual(result.state, EvidenceState.COMPUTED)
                self.assertEqual(len(result.metadata['controls']), len(REQUIRED_CONTROLS))
                observation = result.metadata['input_observation']
                self.assertEqual(observation['state'], 'measured')
                self.assertEqual(observation['metadata']['source_claim']['state'], 'declared')

    def test_invalid_data_and_unknown_modality_do_not_fallback(self):
        gateway = self.bound_gateway(numeric_features, 'numeric')
        for payload in [b'[NaN]', b'[true]', b'[]', b'{"sample": 1}']:
            with self.subTest(payload=payload), self.assertRaises(ValueError):
                gateway.submit(self.envelope(payload, 'numeric'))
        self.assertEqual(gateway.submit(self.envelope(b'raw', 'eeg')).state, EvidenceState.NOT_IMPLEMENTED)
        with self.assertRaises(UnicodeDecodeError):
            self.bound_gateway().submit(self.envelope(b'\xff'))

    def test_envelope_limits_and_bindings(self):
        for payload in [b'', b'x' * (MAX_PAYLOAD_BYTES + 1)]:
            with self.assertRaises(ValueError):
                self.envelope(payload)
        with self.assertRaises(TypeError):
            self.envelope(bytearray(b'content'))
        gateway = self.bound_gateway()
        with self.assertRaises(ValueError):
            gateway.register_control('alda', lambda signal: PolicyDecision.ALLOW, revision='v2')

    def test_sandbox_only_holds_processing(self):
        gateway = SignalGateway()
        for name in REQUIRED_CONTROLS:
            gateway.register_control(name, lambda signal: PolicyDecision.SANDBOX_ONLY, revision='test-v1')
        gateway.register_adapter('text', lambda signal: self.fail('must not process'), revision='test-v1')
        self.assertEqual(gateway.submit(self.envelope()).state, EvidenceState.UNAVAILABLE)

    def test_invalid_control_result_does_not_authorize_adapter(self):
        gateway = SignalGateway()
        for name in REQUIRED_CONTROLS:
            gateway.register_control(name, lambda signal: True, revision='test-v1')
        gateway.register_adapter('text', lambda signal: self.fail('must not process'), revision='test-v1')
        with self.assertRaises(TypeError):
            gateway.submit(self.envelope())

    def test_adapter_failure_propagates_without_substitute(self):
        def broken(signal):
            raise RuntimeError('adapter failed')
        with self.assertRaisesRegex(RuntimeError, 'adapter failed'):
            self.bound_gateway(broken).submit(self.envelope())
        with self.assertRaises(TypeError):
            self.bound_gateway(lambda signal: {'success': True}).submit(self.envelope())
