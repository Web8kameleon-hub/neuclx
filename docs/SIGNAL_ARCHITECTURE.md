# GRAM/HVWO signal admission and ecosystem integration

`declared`: Architecture clarification, 2026-11-04: the user identifies Pillar as
the blog publication engine and emphasizes its academic argumentation/explanation
rules. Study those rules for reasoning reuse; publication is optional downstream
behavior. The current gateway's mandatory pillar callback is an earlier assumption,
not a verified requirement or integration. It has not been changed by this
documentation update. Development decisions and gates: [PLANLOG_REFERENCE.md](PLANLOG_REFERENCE.md).

`declared`: User-requested direction: admit different signal families to GRAM,
preserve HVWO relationships, and place processing under JONA plus ALDA, MALI,
KLAJDI, LIAM, ALBA, ALBI, BLERINA, Pillar, ALBANA and LAGTER controls. Include NIN,
WWWMMM, NodeDB Fluid, NanogridData, ZEISS and XCL/CLX/CLX.I in source review.
This document distinguishes the local contract from proposed engine integration.

## Implemented local admission contract

`computed`: `src/neuclx/signal_gateway.py` provides an explicit, standard-library
admission seam. An immutable SignalEnvelope carries kind, bounded bytes, source
and revision. Byte length and SHA-256 are measured locally; kind, source identity
and source revision remain declarations, not authenticated evidence.

`computed`: JONA evaluates admission before any registered controller or adapter.
Every named control must have an explicit local callback and revision. Missing
bindings or an unknown signal kind yield `not_implemented`. Every callback must
return a PolicyDecision. Rejection raises PermissionError; sandbox-only review
holds processing and yields `unavailable`. All approvals are required for adapter
execution. JONA also gates the final adapter result.

`declared`: These are local callback contracts, not process isolation or proof of
controller correctness. Callbacks must be trusted, reviewed, side-effect-free
local implementations. Signals cannot register or replace callbacks. No remote
source, endpoint or module name is executed automatically. Controller failures
propagate; there is no success fallback. This seam is not connected to the web UI.

`computed`: Included feature helpers cover strict UTF-8 structure, finite numeric
JSON sequences, and opaque binary byte count/hash. They do not decode EEG, audio,
video or image semantics. A helper is an intermediate computation; submit is the
governed release entry point. No controllers or adapters are registered by default.

`not_implemented`: Real named controller bindings, GRAM graph mutation, HVWO
projection of signal features, persistent signal storage and live service calls.
The tests use explicitly synthetic control callbacks, not stand-ins advertised as
working engines. Unknown modalities must not silently become semantic features.

## Source distinctions that integration must preserve

| Component | Evidence read | Status in NeuCLX |
|---|---|---|
| GRAM | clisonix-evolution packages/gram/core.py and server.py | declared: graph and API reference; not integrated as a multisignal engine |
| WWWMMM/XLC | Kloud ocean-core/xlc/xlc_alphabet.py | computed: inspected deterministic symbol-profile construction; not measured physical signals |
| WWWMMM runtime | OS-CLX contracts.go and clx_wwwmmm_ndb_flow.md | declared: distinct wave/weight/momentum/memory/mode/meta-model state contract; do not conflate with XLC's W1/W2/W3/M1/M2/M3 |
| NodeDB Fluid | OS-CLX cycle-engine document and ModuleHint contract | declared: telemetry/cycle/scheduling reference; actual runtime algorithm parity is not verified here |
| NanogridData | search found a frontend variable named nanogridData | unavailable: independent engine identity not established; do not equate it automatically with NanogridContext |
| ZEISS | clisonix-evolution services/nanogrid_zeiss/main.py | computed: inspected HTTP proxy to upstream vision; upstream model and accuracy are unverified |
| NIN / Esthisis | Cwy bridge and OS-CLX nin-engine/nin_core.py | computed: telemetry interpretation, code heuristics, anomaly detection and state labels; no comparative understanding result established |
| LAGTER | clisonix-evolution docs/LAGTER_PROTOCOLS.md | declared: paired metrics, biological/behavioral/environmental context and audit requirements; not a deployed validation engine |
| Pillar | Clisonix/Kloud services/content-factory/content_pillar_strategy.py, services/blerina/main.py and services/blog_publisher/main.py | computed: DISCOVERED editorial generation/publication pipeline; academic-rule effectiveness and integration with NeuCLX remain unverified; distinct from OS-CLX brigades and constitutional pillars |
| Chips | OS-CLX docs/STIGMA_MEMORY_CHIP_SPEC.md | declared: hardware proposal; no measured silicon performance established by this review |
| XCL/CLX/CLX.i | Lightning AUDIT.md | declared: audit maps these specific image-processing entry points to Brotli levels; do not transfer that classification to every similarly named module |

`computed`: NIN's inspected source returns default health 0.5 on failed fabric
probes. A native adaptation must instead preserve an explicit unavailable state.
Its emotional labels are computed operational summaries, not measured feelings.
The Cwy bridge was read successfully; Cwy root nin_core.py returned 404 at the
pinned revision, and the actual inspected implementation was located in OS-CLX.

`declared`: The user clarified that the intended NIN is linked to the JONA
character. Preserve that intended linkage as a separate integration requirement;
do not equate it automatically with OS-CLX telemetry NIN.

`measured`: Additional reads found `NINEngine` in clisonix.com
`ocean-core/nin_engine.py`, and `JONA_Character` in Kloud and clisonix.com
`apps/api/services/jona_character.py`. The inspected intent engine uses patterns,
entity extraction and a cache. The inspected character files define personality,
oversight, EEG and audio-related interfaces, including mock/simulated providers.
Neither read character file contained an explicit NIN/Cwy/Esthisis reference.

`unavailable`: The exact executable NIN-to-JONA-character binding at these
revisions. Absence of that reference in two files does not establish that the
binding is absent elsewhere. Character, intent and telemetry outputs must retain
distinct provenance, and simulated EEG must never be presented as measured data.
JONA's character/personality role does not replace NeuCLX's mandatory sandbox.

`declared`: OS-CLX's ModuleHint contract permits external modules to provide
read-only telemetry; FluidCycleEngine retains state-decision ownership. Future
integration must not grant controllers direct writes to CLXEnvelope, WWWMMM,
Resonance, NDB or Nanogrid. JONA remains mandatory in NeuCLX even when a source
system has a different governance boundary.

`declared`: Preserve typed domain fields, units, timestamps, topology, provenance
and missingness in dedicated adapters. Byte transport and hashes do not replace
WWWMMM/NDB/Nanogrid semantics or authenticate the physical meaning of a signal.
No synthetic zero may substitute for an absent measurement.

`declared`: Neurosonic's five constitutional pillars and MR001-MR006 memory rules
are reference requirements pending native policy mapping and tests. They are not
silently installed as runtime capabilities. Applicable NeuCLX repository rules
remain authoritative.

## Verification

```powershell
$env:PYTHONPATH = 'src'
python -m unittest discover -s tests -p test_signal_gateway.py -v
```

`measured`: Initial eight contract tests passed, including each required control's
veto, JONA rejection at input/output, missing bindings, strict decoding and finite
numbers, payload bounds, and sandbox-only processing holds. They validate this
local contract, not any remote engine's health or multimodal quality.

`declared`: Additional regression cases cover invalid control decisions and
adapter failures. Current execution evidence is saved in
`evidence/signal-contract.json`; it records source hashes rather than claiming
the working tree matches a published commit.

`unavailable`: End-to-end multisignal reasoning quality, live ecosystem state,
hardware performance and superiority over other systems.

## Hybrid-Fluid reasoning integration

`computed`: The reasoning UI offers an explicit Hybrid-Fluid mode implemented
as eleven registered NeuCLX stages: receive, validate, JONA input approval,
Unicode normalization, Alphabet health/statistics, Alphabet query processing,
computed wave indices, MegaLayer, FluidEngine, result assembly, and JONA-gated
ledger recording. Each outbound HTTP request is independently authorized by
JONA. The service clients use Python's standard library, reject redirects, cap
responses, and preserve the returned service data and provenance.

`declared`: Configure the service origins and the actual installed FluidEngine
pipeline before selecting Hybrid-Fluid:

```powershell
$env:NEUCLX_ALPHABET_URL = 'https://<alphabet-service-origin>'
$env:NEUCLX_MEGALAYER_URL = 'https://<megalayer-service-origin>/process'
$env:NEUCLX_FLUID_URL = 'https://<fluidengine-service-origin>'
$env:NEUCLX_FLUID_PIPELINE_NAME = '<installed-pipeline-name>'
```

Non-loopback HTTP endpoints are rejected. The FluidEngine API documents the
request fields `pipelineName` and `inputData`, but does not define a response
schema; NeuCLX preserves its JSON response instead of claiming a normalized
success result. The Hybrid-Fluid path reads supplied `source_urls` through the
JONA-gated public web reader. Cited excerpts are learned into the retrieval
corpus (`self_learning.py`); model output is never ingested as a fact, only
remembered as a Stigma Film frame via the journey ledger together with a
computed grounding index (term overlap and literal source mentions, not a
truth score). Documents are classified `bigdata` (>= 256 KiB), `seltendata`
(<= 1 retrieval) or `standarddata` by a computed rule over stored size and
retrieval hits; these tiers are NeuCLX definitions, not FluidEngine pipeline
behavior. `newdata` is a quarantined fourth class: the first occurrence of a
normalized-answer signature or of a facet combination (mode, model, source
hosts) is counted as computed novelty. It is not validity or creativity, and it
never enters the retrieval corpus. The pre-existing API path remains selectable as
`native`; API callers that omit `mode` retain that behavior.

`measured`: The inspected Clisonix alphabet service source at
`Web8kameleon-hub/clisonix.com` revision
`3a7eb115a71f063dc0bb7b54664583a1c4a2b08c` declares 25 Greek letters (alpha to
omega inclusive, so final sigma is a distinct letter, as the project owner
confirmed) and 36 Albanian letters: 61 base layers. Its health endpoint reports
`letters=61`, and a live probe returned `alphabet_size=61` from the process
route. NeuCLX checks the live health, statistics and process responses against
this 25 + 36 = 61 contract and stops on any deviation.

`computed`: Alphabet wave fields are preserved as values calculated by the
remote service and explicitly labeled computed indices, not sensor readings,
physical frequencies, or evidence of consciousness. MegaLayer output and the
FluidEngine response are likewise exposed as service results, not independently
verified truths.

`measured`: On 2026-11-05 one live run on a single Windows host started the
three modules from their source repositories as loopback processes and
`/api/v1/reason` with `mode=hybrid-fluid` completed all stages. Alphabet
(`clisonix.com` `3a7eb115`, `alphabet_layers_api:app`) and MegaLayer
(`clisonix-evolution` `ocean_core/api_mega_layer.py`) ran unmodified. The
FluidEngine repository (`Lightning-SPP-3.14`) contains only the .NET library
and an OpenAPI description, so a minimal local host exposing
`POST /api/fluid/execute` for the library's `JsonDataStep` was used; that host
is not part of the repository and `NEUCLX_FLUID_PIPELINE_NAME=JsonDataStep`.
This one run verifies neither deployment health nor sustained quality.

`measured`: A second live run with `NEUCLX_MODEL_ENABLED=true`, the explicitly
configured local Ollama model `llama3.1:8b` (OpenAI-compatible
`/v1/chat/completions`, no download) and all three modules returned a model
answer alongside the 11 JONA-allowed stages. The answer is labeled
`Model-generated response; not independently verified.` and is not
retrieval-grounded; the factual claims in it were not checked against a source.
Hybrid-Fluid passes only the question, declared facts and two computed service
signals to the model.

`unavailable`: Beyond that run, deployment health and runtime quality of the
services are not verified, and the other FluidEngine pipelines are not hosted
or tested. Local fixture tests verify HTTP request shapes, JONA vetoes, stage
ordering, and rejection of contract mismatches. Missing endpoint configuration returns
HTTP 503; service failures or contract mismatches return explicit HTTP 502
errors. No fallback is attempted.
