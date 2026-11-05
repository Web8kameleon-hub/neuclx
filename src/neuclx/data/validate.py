"""Validate normalized data records against the evidence contract."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from neuclx.evidence import Datum, EvidenceState as RuntimeEvidenceState
from neuclx.bridge.evidence_contract import ContractViolation, EvidenceContract
from neuclx.bridge.source_manifest import EvidenceState, SourceManifest
from neuclx.jona import JonaSandbox


class DataValidator:
    def __init__(self, contract: EvidenceContract | None = None, sandbox: JonaSandbox | None = None):
        self.contract = contract or EvidenceContract.default()
        self.sandbox = sandbox or JonaSandbox()

    def validate_record(self, record: dict[str, Any]) -> bool:
        if not isinstance(record, dict):
            return False
        content = record.get("content")
        if not isinstance(content, str) or not content.strip():
            return False
        metadata = record.get("metadata", {})
        if not isinstance(metadata, dict):
            return False
        try:
            timestamp_value = record["timestamp"]
            timestamp = (
                timestamp_value
                if isinstance(timestamp_value, datetime)
                else datetime.fromisoformat(timestamp_value)
            )
            manifest = SourceManifest(
                id=record["id"],
                name=record["name"],
                source_type=record["source_type"],
                location=record["location"],
                metadata=metadata,
                hash=record["hash"],
                evidence_state=EvidenceState(record["evidence_state"]),
                timestamp=timestamp,
                license=record["license"],
                version=record.get("version"),
            )
            valid = self.contract.validate(manifest)
            self.sandbox.release(Datum(
                content,
                RuntimeEvidenceState(manifest.evidence_state.value),
                source=manifest.location,
                method="data:evidence-contract-validation",
            ))
            return valid
        except (ContractViolation, KeyError, PermissionError, TypeError, ValueError):
            return False
