"""Optional stdlib client for Clisonix MegaLayer analysis metadata."""

from __future__ import annotations

import ipaddress
import json
import math
import os
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import HTTPRedirectHandler, ProxyHandler, Request, build_opener

from .evidence import Datum, EvidenceState
from .jona import JonaSandbox


UPSTREAM_REVISION = "f120457ab2c38c5bac9d23b62fca5d4ea6f17a0e"
_MAX_RESPONSE_BYTES = 1_000_000


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


class MegaLayerError(RuntimeError):
    """MegaLayer failed or returned data outside its declared contract."""


class MegaLayerAdapter:
    def __init__(self, endpoint: str | None = None, *, timeout: float = 5.0):
        endpoint = endpoint.strip() if endpoint else None
        if endpoint:
            parsed = urlparse(endpoint)
            if parsed.scheme not in {"http", "https"} or not parsed.netloc:
                raise ValueError("MegaLayer endpoint must be an absolute HTTP(S) URL")
            if parsed.username or parsed.password:
                raise ValueError("MegaLayer endpoint must not contain credentials")
            host = parsed.hostname or ""
            try:
                loopback = ipaddress.ip_address(host).is_loopback
            except ValueError:
                loopback = host.casefold() == "localhost"
            if not loopback:
                raise ValueError("MegaLayer endpoint must use loopback; hosted inference is not permitted")
        if timeout <= 0:
            raise ValueError("timeout must be positive")
        self.endpoint = endpoint
        self.timeout = timeout

    @classmethod
    def from_environment(cls):
        return cls(os.environ.get("NEUCLX_MEGALAYER_URL"))

    def analyze(self, query: str, jona: JonaSandbox) -> Datum:
        if not query.strip():
            raise ValueError("query is required")
        if not self.endpoint:
            return Datum(
                None,
                EvidenceState.NOT_IMPLEMENTED,
                source="clisonix-evolution/mega-layer",
                method="optional-integration:not-configured",
            )

        input_datum = Datum(
            query,
            EvidenceState.DECLARED,
            source="neuclx:user-query",
            method="reasoning:query",
        )
        jona.release(input_datum)

        request = Request(
            self.endpoint,
            data=json.dumps({"query": query}, ensure_ascii=False).encode("utf-8"),
            headers={"Accept": "application/json", "Content-Type": "application/json"},
            method="POST",
        )
        try:
            opener = build_opener(ProxyHandler({}), _NoRedirect())
            with opener.open(request, timeout=self.timeout) as response:
                raw = response.read(_MAX_RESPONSE_BYTES + 1)
        except HTTPError as exc:
            raise MegaLayerError(f"MegaLayer returned HTTP {exc.code}") from exc
        except (URLError, TimeoutError, OSError) as exc:
            raise MegaLayerError(f"MegaLayer request failed: {exc}") from exc

        if len(raw) > _MAX_RESPONSE_BYTES:
            raise MegaLayerError("MegaLayer response exceeded 1 MB")
        try:
            payload = json.loads(raw)
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise MegaLayerError("MegaLayer returned invalid JSON") from exc
        metrics = self._validate_payload(payload)

        result = Datum(
            metrics,
            EvidenceState.COMPUTED,
            source="Web8kameleon-hub/clisonix-evolution",
            method="MegaLayerEngine.process_query via POST /process",
            metadata={
                "upstream_revision": UPSTREAM_REVISION,
                "role": "analysis-metadata-only",
            },
        )
        return jona.release(result)

    @staticmethod
    def _validate_payload(payload):
        if not isinstance(payload, dict):
            raise MegaLayerError("MegaLayer response must be a JSON object")
        required = {
            "unique_signature",
            "combinations_used",
            "theoretical_max",
            "processing_ms",
            "complexity_score",
            "total_layers_engaged",
        }
        missing = required - payload.keys()
        if missing:
            raise MegaLayerError(
                "MegaLayer response is missing fields: " + ", ".join(sorted(missing))
            )

        signature = payload["unique_signature"]
        counts = (
            payload["combinations_used"],
            payload["theoretical_max"],
            payload["total_layers_engaged"],
        )
        processing_ms = payload["processing_ms"]
        complexity = payload["complexity_score"]
        if not isinstance(signature, str) or not signature:
            raise MegaLayerError("MegaLayer unique_signature must be a non-empty string")
        if any(type(value) is not int or value < 0 for value in counts):
            raise MegaLayerError("MegaLayer counts must be non-negative integers")
        if counts[1] == 0:
            raise MegaLayerError("MegaLayer theoretical_max must be positive")
        if not MegaLayerAdapter._finite_number(processing_ms) or processing_ms < 0:
            raise MegaLayerError("MegaLayer processing_ms must be a finite non-negative number")
        if not MegaLayerAdapter._finite_number(complexity):
            raise MegaLayerError("MegaLayer complexity_score must be a finite number")

        return {key: payload[key] for key in sorted(required)}

    @staticmethod
    def _finite_number(value):
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            return False
        try:
            return math.isfinite(value)
        except OverflowError:
            return False
