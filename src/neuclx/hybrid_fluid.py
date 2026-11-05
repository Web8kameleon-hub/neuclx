"""JONA-gated adapters and the explicit eleven-stage hybrid-fluid pipeline."""

from __future__ import annotations

import ipaddress
import json
import math
import os
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlparse
from urllib.request import HTTPRedirectHandler, ProxyHandler, Request, build_opener

from .evidence import Datum, EvidenceState
from .jona import JonaSandbox
from .megalayer import MegaLayerAdapter, UPSTREAM_REVISION as MEGALAYER_REVISION
from .pipeline import PipelineDefinition, PipelineRunner, PipelineStage


ALPHABET_CONTRACT_REVISION = "3a7eb115a71f063dc0bb7b54664583a1c4a2b08c"
FLUID_CONTRACT_REVISION = "c673de4c8e51321520250c9539ef4535a196d919"
_MAX_RESPONSE_BYTES = 1_000_000
_MAX_QUERY_LENGTH = 500
_WAVE_FIELDS = (
    "consciousness_level",
    "peak_consciousness",
    "variance",
    "harmony",
    "dominant_frequency",
    "phi_alignment",
)


class HybridFluidError(RuntimeError):
    """A configured hybrid-fluid service failed or violated its API contract."""

    status_code = 502
    error_code = "hybrid_fluid_unavailable"


class HybridFluidNotConfigured(HybridFluidError):
    status_code = 503
    error_code = "hybrid_fluid_not_configured"


class AlphabetContractError(HybridFluidError):
    error_code = "alphabet_contract_mismatch"


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def _validate_service_url(url: str | None, service: str, *, base_url: bool) -> str | None:
    value = url.strip() if url else None
    if not value:
        return None
    parsed = urlparse(value)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError(f"{service} URL must be an absolute HTTP(S) URL")
    if parsed.username or parsed.password or parsed.query or parsed.fragment:
        raise ValueError(f"{service} URL must not contain credentials, query, or fragment")
    if base_url and parsed.path not in {"", "/"}:
        raise ValueError(f"{service} URL must be an origin without a path")
    host = parsed.hostname or ""
    try:
        loopback = ipaddress.ip_address(host).is_loopback
    except ValueError:
        loopback = host.casefold() == "localhost"
    if parsed.scheme == "http" and not loopback:
        raise ValueError(f"non-loopback {service} URLs must use HTTPS")
    return value.rstrip("/")


def _authorize_request(jona: JonaSandbox, query: str, method: str, source: str) -> None:
    datum = Datum(
        query,
        EvidenceState.MEASURED,
        source=source,
        method=method,
    )
    decision = jona.evaluate(datum)
    if decision.value != "allow":
        jona.release(datum)
        raise PermissionError(f"JONA did not allow outbound request: {decision.value}")
    jona.release(datum)


def _request_json(
    url: str,
    *,
    method: str,
    timeout: float,
    body: dict | None = None,
) -> object:
    encoded_body = None
    headers = {"Accept": "application/json"}
    if body is not None:
        encoded_body = json.dumps(body, ensure_ascii=False).encode("utf-8")
        headers["Content-Type"] = "application/json"
    request = Request(url, data=encoded_body, headers=headers, method=method)
    try:
        opener = build_opener(ProxyHandler({}), _NoRedirect())
        with opener.open(request, timeout=timeout) as response:
            raw = response.read(_MAX_RESPONSE_BYTES + 1)
    except HTTPError as exc:
        raise HybridFluidError(f"service returned HTTP {exc.code}: {url}") from exc
    except (URLError, TimeoutError, OSError) as exc:
        raise HybridFluidError(f"service request failed: {url}: {exc}") from exc
    if len(raw) > _MAX_RESPONSE_BYTES:
        raise HybridFluidError("service response exceeded 1 MB")
    try:
        return json.loads(raw)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise HybridFluidError(f"service returned invalid JSON: {url}") from exc


class AlphabetLayerAdapter:
    def __init__(self, endpoint: str | None = None, *, timeout: float = 5.0):
        self.endpoint = _validate_service_url(endpoint, "Alphabet", base_url=True)
        if timeout <= 0:
            raise ValueError("timeout must be positive")
        self.timeout = timeout

    @classmethod
    def from_environment(cls):
        return cls(os.environ.get("NEUCLX_ALPHABET_URL"))

    def _url(self, path: str) -> str:
        if not self.endpoint:
            raise HybridFluidNotConfigured("Alphabet service URL is not configured")
        return f"{self.endpoint}{path}"

    def _get(self, path: str, query: str, jona: JonaSandbox) -> object:
        url = self._url(path)
        _authorize_request(jona, query, f"http:GET:{path}", "neuclx:hybrid-fluid-request")
        return _request_json(url, method="GET", timeout=self.timeout)

    def inspect(self, query: str, jona: JonaSandbox) -> Datum:
        health = self._get("/health", query, jona)
        stats = self._get("/api/v1/alphabet/stats", query, jona)
        if not isinstance(health, dict) or not isinstance(stats, dict):
            raise AlphabetContractError("Alphabet health and stats responses must be JSON objects")

        mismatches = []
        expected_health = {
            "status": "healthy",
            "service": "alphabet-layers",
            "letters": 61,
            "layers": 61,
        }
        expected_stats = {
            "base_layers": 61,
            "greek_letters": 25,
            "albanian_letters": 36,
            "meta_layer": True,
        }
        for field, expected in expected_health.items():
            if health.get(field) != expected:
                mismatches.append(f"health.{field}={health.get(field)!r} (expected {expected!r})")
        for field, expected in expected_stats.items():
            if stats.get(field) != expected:
                mismatches.append(f"stats.{field}={stats.get(field)!r} (expected {expected!r})")
        total_layers = stats.get("total_layers")
        if type(total_layers) is not int or total_layers < 61:
            mismatches.append(f"stats.total_layers={total_layers!r} (expected integer >= 61)")
        if mismatches:
            raise AlphabetContractError("Alphabet 61-layer contract mismatch: " + "; ".join(mismatches))

        return Datum(
            {"health": health, "stats": stats},
            EvidenceState.COMPUTED,
            source="Web8kameleon-hub/clisonix.com/alphabet-layers",
            method="GET /health and GET /api/v1/alphabet/stats",
            metadata={"contract_reference_revision": ALPHABET_CONTRACT_REVISION},
        )

    def process(self, query: str, jona: JonaSandbox) -> Datum:
        path = "/api/v1/alphabet/process"
        url = self._url(path)
        _authorize_request(jona, query, "http:POST:" + path, "neuclx:hybrid-fluid-request")
        result = _request_json(
            url,
            method="POST",
            timeout=self.timeout,
            body={"query": query},
        )
        if not isinstance(result, dict):
            raise AlphabetContractError("Alphabet process response must be a JSON object")
        if result.get("alphabet_size") != 61:
            raise AlphabetContractError(
                f"Alphabet process reported alphabet_size={result.get('alphabet_size')!r}; expected 61"
            )
        active_layers = result.get("active_layers")
        if type(active_layers) is not int or active_layers < 61:
            raise AlphabetContractError(
                f"Alphabet process reported active_layers={active_layers!r}; expected integer >= 61"
            )
        return Datum(
            result,
            EvidenceState.COMPUTED,
            source="Web8kameleon-hub/clisonix.com/alphabet-layers",
            method="POST /api/v1/alphabet/process",
            metadata={"contract_reference_revision": ALPHABET_CONTRACT_REVISION},
        )

    def wave_indices(self, query: str, jona: JonaSandbox) -> Datum:
        path = "/api/v1/alphabet/consciousness"
        url = self._url(path) + "?" + urlencode({"text": query})
        _authorize_request(jona, query, "http:GET:" + path, "neuclx:hybrid-fluid-request")
        result = _request_json(url, method="GET", timeout=self.timeout)
        if not isinstance(result, dict):
            raise AlphabetContractError("Alphabet wave response must be a JSON object")
        if type(result.get("text_length")) is not int or result["text_length"] != len(query):
            raise AlphabetContractError("Alphabet wave response text_length does not match the submitted query")
        for field in _WAVE_FIELDS:
            if not self._finite_number(result.get(field)):
                raise AlphabetContractError(f"Alphabet wave field {field!r} must be a finite number")
        return Datum(
            result,
            EvidenceState.COMPUTED,
            source="Web8kameleon-hub/clisonix.com/alphabet-layers",
            method="GET /api/v1/alphabet/consciousness",
            metadata={
                "contract_reference_revision": ALPHABET_CONTRACT_REVISION,
                "interpretation": "computed indices; not sensor measurements or physical frequencies",
            },
        )

    @staticmethod
    def _finite_number(value) -> bool:
        return (
            not isinstance(value, bool)
            and isinstance(value, (int, float))
            and math.isfinite(value)
        )


class FluidEngineAdapter:
    def __init__(
        self,
        endpoint: str | None = None,
        pipeline_name: str | None = None,
        *,
        timeout: float = 5.0,
    ):
        self.endpoint = _validate_service_url(endpoint, "FluidEngine", base_url=True)
        self.pipeline_name = pipeline_name.strip() if pipeline_name else None
        if timeout <= 0:
            raise ValueError("timeout must be positive")
        self.timeout = timeout

    @classmethod
    def from_environment(cls):
        return cls(
            os.environ.get("NEUCLX_FLUID_URL"),
            os.environ.get("NEUCLX_FLUID_PIPELINE_NAME"),
        )

    def execute(self, input_data: str, jona: JonaSandbox) -> Datum:
        if not self.endpoint or not self.pipeline_name:
            raise HybridFluidNotConfigured(
                "FluidEngine URL and NEUCLX_FLUID_PIPELINE_NAME must be configured"
            )
        path = "/api/fluid/execute"
        _authorize_request(
            jona,
            input_data,
            "http:POST:" + path,
            "neuclx:hybrid-fluid-request",
        )
        result = _request_json(
            self.endpoint + path,
            method="POST",
            timeout=self.timeout,
            body={"pipelineName": self.pipeline_name, "inputData": input_data},
        )
        if result is None:
            raise HybridFluidError("FluidEngine returned a null JSON response")
        return Datum(
            result,
            EvidenceState.COMPUTED,
            source="Web8kameleon-hub/Lightning-SPP-3.14/FluidEngine",
            method="POST /api/fluid/execute",
            metadata={
                "contract_reference_revision": FLUID_CONTRACT_REVISION,
                "pipeline_name": self.pipeline_name,
            },
        )


class HybridFluidPipeline:
    """Run Alphabet, MegaLayer, and FluidEngine without synthetic fallbacks."""

    def __init__(
        self,
        jona: JonaSandbox,
        ledger,
        *,
        alphabet: AlphabetLayerAdapter,
        megalayer: MegaLayerAdapter,
        fluid: FluidEngineAdapter,
    ):
        self.jona = jona
        self.ledger = ledger
        self.alphabet = alphabet
        self.megalayer = megalayer
        self.fluid = fluid
        self.runner = PipelineRunner(jona)
        self.definition = PipelineDefinition(
            name="neuclx-hybrid-fluid-11",
            source="NeuCLX explicit stdlib service adapters",
            revision="neuclx-hybrid-fluid-v1",
            stages=(
                PipelineStage("01-receive", "neuclx-v1", self._receive),
                PipelineStage("02-validate", "neuclx-v1", self._validate),
                PipelineStage("03-jona-input", "jona-policy-v1", self._jona_input),
                PipelineStage("04-normalize", "unicode-nfkc-v1", self._normalize),
                PipelineStage("05-alphabet-profile", ALPHABET_CONTRACT_REVISION, self._alphabet_profile),
                PipelineStage("06-alphabet-process", ALPHABET_CONTRACT_REVISION, self._alphabet_process),
                PipelineStage("07-wave-indices", ALPHABET_CONTRACT_REVISION, self._wave_indices),
                PipelineStage("08-megalayer", MEGALAYER_REVISION, self._megalayer),
                PipelineStage("09-fluid-engine", FLUID_CONTRACT_REVISION, self._fluid),
                PipelineStage("10-assemble", "neuclx-v1", self._assemble),
                PipelineStage("11-jona-record", "jona-ledger-v1", self._record),
            ),
        )

    @classmethod
    def from_environment(cls, jona: JonaSandbox, ledger):
        return cls(
            jona,
            ledger,
            alphabet=AlphabetLayerAdapter.from_environment(),
            megalayer=MegaLayerAdapter.from_environment(),
            fluid=FluidEngineAdapter.from_environment(),
        )

    def run(self, task: str, facts=()) -> Datum:
        missing = []
        if not self.alphabet.endpoint:
            missing.append("NEUCLX_ALPHABET_URL")
        if not self.megalayer.endpoint:
            missing.append("NEUCLX_MEGALAYER_URL")
        if not self.fluid.endpoint:
            missing.append("NEUCLX_FLUID_URL")
        if not self.fluid.pipeline_name:
            missing.append("NEUCLX_FLUID_PIPELINE_NAME")
        if missing:
            raise HybridFluidNotConfigured(
                "Hybrid-Fluid requires all upstream services; missing: " + ", ".join(missing)
            )
        if not isinstance(task, str) or not task.strip():
            raise ValueError("task is required")
        if not isinstance(facts, (list, tuple)) or any(not isinstance(fact, str) for fact in facts):
            raise TypeError("facts must be a list of strings")

        query = task.strip()
        context = [fact.strip() for fact in facts if fact.strip()]
        if context:
            query += "\n\nContext:\n" + "\n".join(context)
        request = Datum(
            {"query": query},
            EvidenceState.MEASURED,
            source="neuclx:reason-api-request",
            method="http:received-request-body",
        )
        return self.runner.run(self.definition, request)

    @staticmethod
    def _computed(value, method: str, source: str = "neuclx:hybrid-fluid") -> Datum:
        return Datum(value, EvidenceState.COMPUTED, source=source, method=method)

    def _receive(self, item: Datum) -> Datum:
        return self._computed(dict(item.value), "pipeline:receive")

    def _validate(self, item: Datum) -> Datum:
        query = item.value.get("query")
        if not isinstance(query, str) or not query.strip():
            raise ValueError("hybrid-fluid query is required")
        if len(query) > _MAX_QUERY_LENGTH:
            raise ValueError(
                f"hybrid-fluid query exceeds {_MAX_QUERY_LENGTH} characters; Alphabet truncates longer inputs"
            )
        return self._computed(
            {**item.value, "query_length": len(query)},
            "validation:query-and-service-limit",
        )

    def _jona_input(self, item: Datum) -> Datum:
        decision = self.jona.evaluate(item)
        if decision.value != "allow":
            self.jona.release(item)
            raise PermissionError(f"JONA did not allow hybrid-fluid input: {decision.value}")
        return self._computed(
            {**item.value, "jona_input_decision": decision.value},
            "jona:input-allow",
        )

    def _normalize(self, item: Datum) -> Datum:
        import unicodedata

        query = unicodedata.normalize("NFKC", item.value["query"]).strip()
        if not query:
            raise ValueError("normalized hybrid-fluid query is empty")
        return self._computed({**item.value, "query": query, "normalized": True}, "unicode:NFKC")

    def _alphabet_profile(self, item: Datum) -> Datum:
        profile = self.alphabet.inspect(item.value["query"], self.jona)
        return self._computed(
            {**item.value, "alphabet_profile": profile.as_dict()},
            "alphabet:health-and-stats",
        )

    def _alphabet_process(self, item: Datum) -> Datum:
        result = self.alphabet.process(item.value["query"], self.jona)
        return self._computed(
            {**item.value, "alphabet_result": result.as_dict()},
            "alphabet:process-query",
        )

    def _wave_indices(self, item: Datum) -> Datum:
        result = self.alphabet.wave_indices(item.value["query"], self.jona)
        return self._computed(
            {**item.value, "wave_indices": result.as_dict()},
            "alphabet:computed-wave-indices",
        )

    def _megalayer(self, item: Datum) -> Datum:
        result = self.megalayer.analyze(item.value["query"], self.jona)
        return self._computed(
            {**item.value, "megalayer": result.as_dict()},
            "megalayer:process-query",
        )

    def _fluid(self, item: Datum) -> Datum:
        fluid_input = {
            "query": item.value["query"],
            "alphabet_profile": item.value["alphabet_profile"],
            "alphabet_result": item.value["alphabet_result"],
            "wave_indices": item.value["wave_indices"],
            "megalayer": item.value["megalayer"],
        }
        input_data = json.dumps(fluid_input, ensure_ascii=False, separators=(",", ":"))
        if len(input_data.encode("utf-8")) > _MAX_RESPONSE_BYTES:
            raise HybridFluidError("FluidEngine input exceeded 1 MB")
        result = self.fluid.execute(input_data, self.jona)
        return self._computed({**item.value, "fluid_engine": result.as_dict()}, "fluid:execute")

    def _assemble(self, item: Datum) -> Datum:
        assembled = {
            "query": item.value["query"],
            "alphabet_profile": item.value["alphabet_profile"],
            "alphabet_result": item.value["alphabet_result"],
            "wave_indices": item.value["wave_indices"],
            "megalayer": item.value["megalayer"],
            "fluid_engine": item.value["fluid_engine"],
        }
        return self._computed(assembled, "pipeline:assemble-real-service-results")

    def _record(self, item: Datum) -> Datum:
        output = Datum(
            item.value,
            EvidenceState.COMPUTED,
            source="neuclx:hybrid-fluid",
            method="pipeline:11-stage-real-service-execution",
            metadata={
                "wave_interpretation": "computed indices; not sensor measurements or physical frequencies",
                "pipeline": self.definition.name,
            },
        )
        self.jona.release(output)
        recorded = self.ledger.record(item.value["query"], output)
        return self._computed({**item.value, "ledger": recorded}, "jona:release-and-ledger-record")
