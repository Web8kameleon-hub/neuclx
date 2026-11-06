# Source ledger

## Planlog references and prior read-only audit, 2026-11-04

`measured`: The following source/test paths were inspected during the preceding
read-only audit. No upstream code was copied or executed. This entry records
references for [PLANLOG_REFERENCE.md](PLANLOG_REFERENCE.md), not integration.

| Repository | Path | Revision | Adaptation status |
|---|---|---|---|
| Web8kameleon-hub/clisonix.com | services/content-factory/content_pillar_strategy.py; services/blerina/main.py; services/blog_publisher/main.py | 3a7eb115a71f063dc0bb7b54664583a1c4a2b08c | declared; editorial rules/publication reference; no new adaptation; Pillar is not a mandatory core controller |
| Web8kameleon-hub/Kloud | services/content-factory/content_pillar_strategy.py; services/blerina/main.py; services/blog_publisher/main.py | 9e2d2356d98c427a3f2eb6cf52e1c6618a608577 | declared; source-specific editorial/publication reference; not assumed identical to Clisonix |
| Web8kameleon-hub/LONGO- | java-longo/src/main/java/com/clisonix/longo/LongoStore.java; LongoCollection.java, StorageEngine.java and LongoServer.java in the same package; java-longo/src/test/java/com/clisonix/longo/LongoRuntimeTest.java | 62c87f9c6072a2b36bd90bc2a1edd38873280a61 | declared; storage and failure-test reference; static review only, no integration |
| Web8kameleon-hub/rehaconnect | backend/rehaconnect-api/src/main/java/com/rehaconnect/WorkspaceService.java; ClinicStore.java in the same package; controllers/BillingController.java; backend/rehaconnect-api/src/test/java/com/rehaconnect/WorkspaceServiceTest.java and AssistantBridgeTest.java | a611120308b5e72cf468d90b1cb618193bf36488 | declared; authorization/conflict/bridge reference; static source and test review, not executed here |
| Web8kameleon-hub/ultrawebthinking | apps/web/components/AGIXmed/index.tsx; backend/server.ts; apps/web/app/api/agixmed/consultations/route.ts; apps/web/app/api/agixmed/auth/login/route.ts | e2cc2160080107df13e4779d8280789ee8008c24 | declared; demo/UI contract review; mock/random analysis and demo auth not admitted |
| Web8kameleon-hub/clisonix.com | tests/unit/test_module_lab_integration.py | 3a7eb115a71f063dc0bb7b54664583a1c4a2b08c | declared; limited NIN intent-test reference; does not verify NIN–JONA-character binding |
| karpathy/llm.c | repository README/license display | unavailable; exact commit not pinned | declared; training-code study candidate only; no code import or implementation adaptation |
| Qwen/Qwen3-8B | LICENSE on Hugging Face model repository | unavailable; exact model revision not pinned | declared; Apache-2.0 text reference previously inspected; no weights admitted |
| meta-llama/Llama-3.1-8B | LICENSE on Hugging Face model repository | unavailable; exact model revision not pinned | declared; model-specific license reference previously inspected; no weights admitted |

## NIN and JONA-character clarification, 2026-11-04

`declared`: The intended integration is the user's NIN linked to JONA character,
not an automatic substitution of a telemetry engine. The exact binding remains
unavailable in the reviewed files; variants stay distinct in SIGNAL_ARCHITECTURE.md.

| Repository | Path | Revision | Adaptation status |
|---|---|---|---|
| Web8kameleon-hub/clisonix.com | ocean-core/nin_engine.py | 3a7eb115a71f063dc0bb7b54664583a1c4a2b08c | declared; inspected pattern-based intent/entity engine, not ported; blob febeb7890693e17a1107eeeb224af438ba6ac7e0 |
| Web8kameleon-hub/clisonix.com | apps/api/services/jona_character.py | 3a7eb115a71f063dc0bb7b54664583a1c4a2b08c | declared; character/oversight interfaces reviewed; no explicit NIN reference found; blob cf5c8d4122efe1a2a89614c1584585579f33d1d7 |
| Web8kameleon-hub/Kloud | apps/api/services/jona_character.py | 9e2d2356d98c427a3f2eb6cf52e1c6618a608577 | declared; character/oversight interfaces reviewed; no explicit NIN reference found; blob 519d779b84f2aabe53ded02fecfb8ca3e0a866ca |

## Signal ecosystem review, 2026-11-04

`measured`: Files below were read at pinned revisions; some reads were bounded
to introductory sections. No source code was copied or executed. Source-specific
limitations and the native callback contract are documented in SIGNAL_ARCHITECTURE.md.
Private source contents remain outside candidate snapshots.

| Repository | Path | Revision | Adaptation status |
|---|---|---|---|
| Web8kameleon-hub/clisonix-evolution | packages/gram/server.py; gram-fabric/install-adapter.sh | f120457ab2c38c5bac9d23b62fca5d4ea6f17a0e | declared; reviewed API/fabric seams; native signal_gateway.py is a new contract, not a server port |
| Web8kameleon-hub/clisonix-evolution | docs/LAGTER_PROTOCOLS.md | f120457ab2c38c5bac9d23b62fca5d4ea6f17a0e | declared; paired-signal and audit reference, not implemented |
| Web8kameleon-hub/clisonix-evolution | services/content-factory/content_pillar_strategy.py | f120457ab2c38c5bac9d23b62fca5d4ea6f17a0e | declared; content-pillar reference; not identified as the user's complete Pillar system |
| Web8kameleon-hub/OS-CLX | docs/clx_wwwmmm_ndb_flow.md; runtime/pkg/contracts/contracts.go | c54e104f94adb972b0c69e2a6ac750242c0c1048 | declared; typed domain and ModuleHint references; no runtime integration |
| Web8kameleon-hub/OS-CLX | kernel/src/brigades.rs | c54e104f94adb972b0c69e2a6ac750242c0c1048 | declared; four governance pillars reviewed, not ported |
| Web8kameleon-hub/OS-CLX | docs/STIGMA_MEMORY_CHIP_SPEC.md | c54e104f94adb972b0c69e2a6ac750242c0c1048 | declared; hardware proposal only |
| Web8kameleon-hub/Kloud | ocean-core/xlc/xlc_alphabet.py | 9e2d2356d98c427a3f2eb6cf52e1c6618a608577 | declared; deterministic WWWMMM symbol-profile reference, not ported |
| Web8kameleon-hub/www.neuroconic.eu | docs/Constitution.md; docs/guides/zero-fake.md | 23f5da06bf0b6b6325129e7cf6f18f180552d1ec | declared; five-pillar and truth-law reference pending native mapping |
| Web8kameleon-hub/Cwy | engines/signals/clisonix-bridge.ts | 0f6d038564512353a98be554170890ef99099d7b | declared; NIN telemetry contract reviewed; not connected |
| Web8kameleon-hub/Cwy | nin_core.py | 0f6d038564512353a98be554170890ef99099d7b | unavailable; exact root path returned 404, not a repository-wide absence claim |
| Web8kameleon-hub/OS-CLX | nin-engine/nin_core.py | c54e104f94adb972b0c69e2a6ac750242c0c1048 | declared; telemetry/anomaly/state-label implementation reviewed; dependencies/default health prevent direct core adoption |
| Web8kameleon-hub/OS-CLX | docs/runtime/nodedb-fluid-cycle-engine.md | c54e104f94adb972b0c69e2a6ac750242c0c1048 | declared; cycle-state and scheduling reference, not algorithm parity evidence |
| Web8kameleon-hub/clisonix-evolution | services/nanogrid_zeiss/main.py | f120457ab2c38c5bac9d23b62fca5d4ea6f17a0e | declared; inspected upstream vision proxy, not native vision integration |
| Web8kameleon-hub/Lightning-SPP-3.14 | AUDIT.md | c673de4c8e51321520250c9539ef4535a196d919 | declared; source audit's scoped XCL/CLX/CLX.i classification, not independently executed here |

## Native retrieval experiment, 2026-11-04

`measured`: rank_bm25 master resolved to the commit below; source and license
were reread at that commit and matched the previously observed blob identifiers.

| Repository | Path | Revision (commit) | Adaptation status |
|---|---|---|---|
| dorianbrown/rank_bm25 | rank_bm25.py; LICENSE | 47aa3ddf8dc1ebeb7ef4e65f2b4536af44594099 | computed; algorithm-inspired native stdlib implementation in src/neuclx/retrieval.py, no upstream code copied or dependency installed; opt-in only |

`declared`: The native ranker uses positive `log1p` IDF, unique query terms,
fixed k1=1.5 and b=0.75, and retains the existing coverage gate. It is not an exact
port of upstream Okapi's epsilon floor. Source code blob:
`d20a28e82d82520ff23a9f4684a26b01f5e8d7d7`; license blob:
`261eeb9e9f8b2b4b0d119366dda99c6fd7d35c64` (Apache-2.0 text).
Validation and evaluation limits are recorded in LEARNING.md.

## External open-source discovery, 2026-11-04

`measured`: Files below were read through the GitHub connector. Revision is the
returned Git blob SHA, not a verified repository commit. Default branches can
move; pin a repository commit and recheck file hashes before adaptation.
All entries remain references: no source code copied, installed or executed.
Selection and admission conditions: [OPEN_SOURCE_STRATEGY.md](OPEN_SOURCE_STRATEGY.md).

| Repository | Path | Revision (Git blob SHA) | Adaptation status |
|---|---|---|---|
| dorianbrown/rank_bm25 | rank_bm25.py | d20a28e82d82520ff23a9f4684a26b01f5e8d7d7 | declared; retrieval reference, NumPy import incompatible with direct core use |
| dorianbrown/rank_bm25 | LICENSE | 261eeb9e9f8b2b4b0d119366dda99c6fd7d35c64 | measured; Apache-2.0 text inspected, no code admission |
| sympy/sympy | LICENSE | 68911b22b5d974019fd781220a87a9e2e13c210f | measured; BSD three-clause text inspected; algorithm adaptation not implemented |
| EleutherAI/lm-evaluation-harness | LICENSE.md | 12e6063183935e876e232db276568baf4954b492 | measured; MIT text inspected, no code admission |
| EleutherAI/lm-evaluation-harness | pyproject.toml | 0c24d4fcb7349fa4cf431d9a4533e98bf7ba88ed | declared; external evaluation reference, dependencies excluded from core/tests |

## Connected GitHub review, 2026-11-04

`measured`: The following files were fetched at explicit commits through the
connected GitHub tool. Revision means the requested commit; blob SHA identifies
the returned file. Review findings and development gates: [WEB8_RESEARCH.md](WEB8_RESEARCH.md).

| Repository | Path | Revision | Blob SHA | Adaptation status |
|---|---|---|---|---|
| Web8kameleon-hub/clisonix-evolution | packages/gram/core.py | f120457ab2c38c5bac9d23b62fca5d4ea6f17a0e | 71b7f59a54c3fece8fb88a910bb970bc8912eac8 | declared; reviewed graph-memory candidate, no code imported |
| Web8kameleon-hub/Kloud | protocol/src/governance_contracts.rs | 9e2d2356d98c427a3f2eb6cf52e1c6618a608577 | 862e44689f89c3170030bd3b3411a078b9a21a60 | declared; reviewed only, sandbox bypass incompatible with NeuCLX |
| Web8kameleon-hub/Lightning-SPP-3.14 | Docs/STIGMA_FORMAL_SPEC.md | c673de4c8e51321520250c9539ef4535a196d919 | a1897457905467ee7c591034b9df8accdf11ca40 | declared; specification reference, targets not runtime measurements |
| Web8kameleon-hub/Kloud | ocean_training.py | 9e2d2356d98c427a3f2eb6cf52e1c6618a608577 | 90c10318da80a37a6557e6fadafc217abe26f76f | declared; reviewed query-driver script, not imported or executed |

## Local PC documentation import

`measured`: Local documentation was read from the following roots. Exact file paths, content revisions, and adaptation status are recorded in the local `data/local-source-ledger.json`; import results are in `data/local-learning-report.json`. Working-tree content is identified by SHA-256, not asserted to match a remote Git revision.

| Local project | Path | Revision | Adaptation status |
|---|---|---|---|
| Server Kameleon | C:/Users/Admin/Server Kameleon/docs | per-file SHA-256 in local ledger | declared; cited document retrieval only |
| www.neuroconic.eu | C:/Users/Admin/www.neuroconic.eu/docs | per-file SHA-256 in local ledger | declared; cited document retrieval only |
| ultrawebthinking | C:/Users/Admin/ultrawebthinking/docs | per-file SHA-256 in local ledger | declared; cited document retrieval only |

Source document claims remain `declared`. Local source contents are stored only in the ignored local database; no source code or model is executed by ingestion.

## Document retrieval import, 2026-09-20

`declared`: The following sources are ingested as cited document text only, not executable capabilities. The local importer uses document content hashes for working-tree revisions. Existing quarantined candidates retain their manifest revisions and are checked against their SHA-256 before ingestion.

| Repository | Path | Revision | Adaptation status |
|---|---|---|---|
| Web8kameleon-hub/Kloud | README.md | 6b59e8c03837dbea1366cab2909a3981d51a8588 | declared; retrieved text only |
| Web8kameleon-hub/Lightning-SPP-3.14 | README.md | ec9e8d6312bfd7cdd2442352bf53d201c2e79105 | declared; retrieved text only |
| Web8kameleon-hub/www.neuroconic.eu | README.md | 23f5da06bf0b6b6325129e7cf6f18f180552d1ec | declared; retrieved text only |
| Web8kameleon-hub/neuclx | README.md, AGENTS.md, docs/*.md | per-file SHA-256 stored locally | declared; local document retrieval |

`measured`: A README.md lookup at main was attempted for all 17 repositories supplied by the user. Results and unavailable reasons are recorded locally in data/repository-discovery.json. A failed path/ref lookup does not establish that the repository itself is inaccessible. Unpinned discovery does not become a runtime source.

Research date: 2026-09-07. A listing here records influence/provenance, not automatic code import.

| Source repository | Verified path | Revision observed | Verified concept | NeuCLX status |
|---|---|---|---|---|
| Web8kameleon-hub/clisonix.com | `packages/gram/core.py`, `packages/gram/node.py` | `1c6be3a0bd74f015384de9416ea94e2bd453a870` | HVOW directional links, wave and memory links | adapted; no source copy |
| Web8kameleon-hub/clisonix.com | `clx_local_domain_wrapper.py` | same | HVO horizontal/vertical/orbital domain vocabulary | adapted; no source copy |
| Web8kameleon-hub/clisonix.com | `jona_server.py` | same | JONA sandbox and synthesis boundary | adapted as mandatory local policy |
| Web8kameleon-hub/Kloud | `protocol/src/governance_contracts.rs` | `6b59e8c03837dbea1366cab2909a3981d51a8588` | governance decisions and sandbox-only gating | adapted; no source copy |
| Web8kameleon-hub/Lightning-SPP-3.14 | `Docs/FUNCTIONS_REFERENCE.md` | `ec9e8d6312bfd7cdd2442352bf53d201c2e79105` | TideWave, resonance, CLX processing vocabulary | declared for later integration |
| Web8kameleon-hub/Lightning-SPP-3.14 | `README.md`, `Docs/STIGMA_GLOSSARY.md` | `ec9e8d6312bfd7cdd2442352bf53d201c2e79105` | Stigma Memory and stabilized film/imprint vocabulary | adapted as compact immutable response frames |
| Web8kameleon-hub/Cwy | `README.md`, `engines/system/osclx.ts` | `0f6d038564512353a98be554170890ef99099d7b` | linewave and OS-CLX memory/momentum vocabulary | declared for later integration |
| Web8kameleon-hub/OS-CLX | repository indexed | revision not captured in this bootstrap | sovereign OS-CLX integration target | unavailable pending file-level audit |
| Web8kameleon-hub/www.neuroconic.eu | repository indexed | revision not captured in this bootstrap | Neuroconic integration target | unavailable pending file-level audit |

## New declarations

`HVWO`, `JP`, `JL`, `VP`, and `VL` were requested as new NeuCLX concepts. GitHub code search did not verify them as existing implementations in the listed sources. They are therefore declared NeuCLX extensions and are implemented here with explicit tests; no historical-source claim is made.

## Optional MegaLayer metadata adapter

`measured`: The files below were inspected at the current `main` commit. The
NeuCLX adapter is a new standard-library, loopback-only HTTP client; no Clisonix
source code was copied. It accepts validated processing metrics as computed
analysis metadata only, not as semantic answers or supporting evidence. JONA
evaluates both the outbound query and returned datum.

| Repository | Path | Revision | Adaptation status |
|---|---|---|---|
| Web8kameleon-hub/clisonix-evolution | ocean_core/mega_layer_engine.py; ocean_core/api_mega_layer.py | f120457ab2c38c5bac9d23b62fca5d4ea6f17a0e | adapted; new loopback-only stdlib client targets the declared POST /process contract; no source code copied |
| Web8kameleon-hub/clisonix-evolution | ocean_core/ocean_core_temp/runtime/mega_layer_adapter.py; apps/api/main.py; launch-megalayer.ps1 | f120457ab2c38c5bac9d23b62fca5d4ea6f17a0e | declared; inspected placeholder and route mismatch; not used as answer engine |

## Clisonix public web-reader discovery

`measured`: Official pages at `www.clisonix.com` were read on 2026-11-05.
The Developer Center describes a Web Reader and API catalog, but the inspected
page output did not expose a concrete Web Reader endpoint contract. No Clisonix
hosted inference endpoint is used. NeuCLX's direct-URL excerpt reader is a new
standard-library implementation; it does not copy Clisonix code.

| Repository | Path | Revision | Adaptation status |
|---|---|---|---|
| Web8kameleon-hub/clisonix.com | https://www.clisonix.com/ | unavailable; page has no published source revision | declared; official product-page reference only |
| Web8kameleon-hub/clisonix.com | https://www.clisonix.com/developers | unavailable; page has no published source revision | declared; API catalog claims observed, no endpoint contract adapted |
| Web8kameleon-hub/clisonix.com | https://www.clisonix.com/modules/web-reader | unavailable; page has no published source revision | declared; Web Reader product surface observed, no API contract adapted |

## NeuCLX data layer and Longo source lineage

`measured`: `neuclx.data` was added as a native Python standard-library package.
It normalizes records and validates them through the existing evidence contract
and JONA sandbox. No Java Longo source was copied into NeuCLX. The references
below are the durable lineage record; the Lightning repository's root MIT
license does not cover its `Persistence/Longo` directory.

| Repository | Path | Revision | Adaptation status |
|---|---|---|---|
| Web8kameleon-hub/LONGO- | java-longo/LICENSE; java-longo/README.md; java-longo/pom.xml; java-longo/src/main/java/com/clisonix/longo/{Document,Filters,LongoCollection,LongoDatabase,LongoServer,LongoStore,StorageEngine}.java; java-longo/src/test/java/com/clisonix/longo/LongoRuntimeTest.java | 62c87f9c6072a2b36bd90bc2a1edd38873280a61 | declared; AGPL-3.0 source reviewed as the canonical Longo implementation; not copied or run |
| Web8kameleon-hub/rehaconnect | LICENSE; backend/rehaconnect-api/src/main/java/com/clisonix/longo/{Document,Filters,LongoCluster,LongoCollection,LongoDatabase,LongoStore,StorageEngine}.java; backend/rehaconnect-api/src/main/java/com/rehaconnect/clients/LongoClient.java | a611120308b5e72cf468d90b1cb618193bf36488 | declared; Longo source files match the canonical repository blobs; repository license is proprietary; reference only, no code copied |
| Web8kameleon-hub/Lightning-SPP-3.14 | LICENSE; LICENSE-COMMERCIAL.txt; Persistence/Longo/PROVENANCE.md; Persistence/Longo/src/main/java/com/clisonix/longo/{JsonCodec,LongoCollection,LongoServer,LongoStore,StorageEngine}.java; Persistence/Longo/src/test/java/com/clisonix/longo/LongoRuntimeTest.java | c673de4c8e51321520250c9539ef4535a196d919 | declared; provenance identifies a Longo-derived component with writer-lock and compare-and-swap changes; this directory is commercial, not covered by the repository MIT grant; reference only |
| Web8kameleon-hub/clisonix.com | java-longo/; java-longo/LICENSE-COMMERCIAL.md | 6a3724508d4f7592c033ec8814d007fb3e1008fc | declared; Lightning's PROVENANCE.md names this as the upstream Longo snapshot; no code copied |
| Web8kameleon-hub/OS-CLX | kernel/src/stigma_memory.rs | c54e104f94adb972b0c69e2a6ac750242c0c1048 | declared; user identifies OS-CLX with aiagi.io; no Longo-named path was found in the inspected tree; unrelated existing reference only |
| Web8kameleon-hub/www.neurosonic.eu | repository identity and matching website | unavailable; exact repository identifier was not returned by the connected GitHub listing | declared; user says the repository and website share this name; identity is retained as a user-declared reference, not independently verified |

The current connected GitHub listing returned `Web8kameleon-hub/www.neuroconic.eu`
at `4cd55c289fbc7e90e9aa28fec5413d312e0ba589`; its spelling differs from the
user-declared `www.neurosonic.eu`, so these names are not silently treated as
the same repository. The import manifest remains the 16-repository candidate
inventory; the table above records additional lineage references without
promoting private or commercially licensed code into that inventory.

## Pipeline source discovery, 2026-11-05

`measured`: The repositories and paths below were identified by pinned GitHub
tree listings. This is path discovery, not full source review or evidence that
the pipeline runs. No pipeline source code was copied or executed. Repository
license metadata is recorded as `NOASSERTION` where GitHub did not report a
license; that value is not a license grant.

| Repository | Path | Revision | Adaptation status |
|---|---|---|---|
| Web8kameleon-hub/Kloud | ai_agi_pipeline.py; core/pipelines/pipeline_framework.py; hybrid_protocol_pipeline.py; airflow/dags/{clinicaltrials,crossref,openalex,openfda,pubmed,semantic_scholar}_ingest.py; app/modules/auto_adapt_trainer.ts | 9e2d2356d98c427a3f2eb6cf52e1c6618a608577 | measured; discovered only; repository license metadata NOASSERTION; static source/license/dependency review and blob comparison pending |
| Web8kameleon-hub/clisonix.com | ai_agi_pipeline.py; .github/workflows/{ingestion,ocean-model-stack,ocean-runtime-deploy,ocean-runtime-diagnostics}.yml | 3a7eb115a71f063dc0bb7b54664583a1c4a2b08c | measured; discovered only; repository license metadata NOASSERTION; no adaptation |
| Web8kameleon-hub/clisonix-evolution | ai_agi_pipeline.py; airflow/dags/; ocean_core/pipelines/; ocean_core/reasoning_engine.py; hybrid_saas_platform/run_pipeline.py | f120457ab2c38c5bac9d23b62fca5d4ea6f17a0e | measured; discovered only; repository license metadata NOASSERTION; potential overlap with Kloud requires blob-level comparison |
| Web8kameleon-hub/OS-CLX | imports/kloud/ocean-core/pipelines/{reasoning,safety,context_manager}.py; runtime/internal/api/control_plane_pipeline.go; nin-engine/nin_core.py | c54e104f94adb972b0c69e2a6ac750242c0c1048 | measured; discovered only; repository license metadata NOASSERTION; reasoning and control-plane paths need separate review |
| Web8kameleon-hub/Ultrawebthinkig-v2 | core/engines/{agi-engine,chat-engine,reasoning-engine}.ts | 8c7263eee2dc25cdb7aa09c6c8b779929ae3cbf3 | measured; discovered only; repository license metadata NOASSERTION; no adaptation |
| Web8kameleon-hub/Lightning-SPP-3.14 | .github/workflows/{ci-cd,continuous-release-evidence,hosting-readiness,release-readiness,runtime-packages}.yml; Scripts/package-release.py; Scripts/validate-release-companions.py | c673de4c8e51321520250c9539ef4535a196d919 | measured; discovered only; repository license metadata NOASSERTION; CI/release candidates, not an AI runtime; Persistence/Longo has a separately recorded commercial boundary |

`declared`: The user authorized adapting selected AI, data, reasoning, signal,
CI/release/deploy and business-workflow pipeline sources from the identified
Web8kameleon-hub repositories, including private repositories. Authorization
does not replace path-level source review, applicable license notices,
dependency review, secret scanning, duplicate detection, JONA admission, or
tests. The OpenAI-compatible ModelAdapter is new NeuCLX code and does not copy
these pipeline implementations.

## Hybrid-Fluid service contracts

`computed`: NeuCLX now has new standard-library HTTP adapters and an explicit
11-stage pipeline. The adapters use the referenced JSON/API contracts; no
upstream implementation code is copied. Environment configuration is required,
JONA authorizes each outbound request, redirects are rejected, and there is no
local or hosted-model fallback.

| Repository | Path | Revision | Adaptation status |
|---|---|---|---|
| Web8kameleon-hub/clisonix.com | alphabet_layers_api.py; ocean-core/alphabet_layers.py | 3a7eb115a71f063dc0bb7b54664583a1c4a2b08c | computed; new stdlib client for health, stats, process and computed wave-index routes; upstream 25 Greek + 36 Albanian = 61 contract is enforced |
| Web8kameleon-hub/clisonix-evolution | ocean_core/api_mega_layer.py; ocean_core/mega_layer_engine.py | f120457ab2c38c5bac9d23b62fca5d4ea6f17a0e | computed; existing stdlib client is JONA-gated and permits configured HTTPS endpoints; response revision is identified as a contract reference, not a verified deployed revision |
| Web8kameleon-hub/Lightning-SPP-3.14 | wwwmmm.FluidEngine/openapi.fluid.json | c673de4c8e51321520250c9539ef4535a196d919 | computed; new stdlib client sends the selected configured pipeline name and actual upstream results; response shape is preserved without an invented success schema |

`unavailable`: Live service health and execution. No service endpoints were
configured in the inspected environment, and local HTTP fixture tests do not
establish that a remote deployment is running these exact source revisions.

`computed`: `src/neuclx/pipeline.py` implements a native, JONA-gated explicit
stage runner inspired by the sequence-of-stages concept in the Kloud framework.
It does not copy source code. The upstream file imports PyYAML and defines
`CODE` and `TOOL` step types; those dynamic execution/configuration surfaces
were not carried into NeuCLX. `tests/test_pipeline.py` covers allow, hold,
reject, invalid output and exception behavior.

## TruthfulQA benchmark dataset, 2026-11-05

| Repository | Path | Revision | Adaptation status |
| --- | --- | --- | --- |
| sylinrl/TruthfulQA | TruthfulQA.csv | d71c110897f5d31c5d7f309e7bc316c152f6f031 | declared; Apache-2.0 (commercial use permitted, attribution required, not MIT); downloaded explicitly by the operator, not vendored; `benchmarks/truthfulqa_benchmark.py` reads a local copy; `benchmarks/results/truthfulqa-proxy-25.json` contains the 25 question rows and outputs used in the run |

`measured`: `benchmarks/results/truthfulqa-proxy-25.json` is one run (temperature
0) of the first 25 rows with an https `Source`, through `/api/v1/reason` in
hybrid-fluid mode with `llama3.1:8b` via Ollama. Scoring is a term-overlap proxy
against the dataset's reference answers, not the official TruthfulQA metric.
The result is development evidence and does not establish AI rank.
| Web8kameleon-hub/OS-CLX | docs/hardware/stigma_center_core.v | c54e104f94adb972b0c69e2a6ac750242c0c1048 | declared; owner-authored, private repo; RTL not copied. src/neuclx/stigma_chip.py is a bit-exact uint64 software model (computed). Icarus Verilog 11.0 with -g2012: tests/test_stigma_rtl_differential.py checks the three datapath submodules across reset and 3 seeds x 400 cycles, and the top module across reset and 500 cycles including mapper, SNZG, NDB, memory, momentum, V_dpa, resonance, load band, and every NDB output. RTL is read from NEUCLX_STIGMA_RTL, never vendored; tests skip when unavailable. These are functional simulation results only; synthesis, speed, power, area and silicon remain not_implemented. |
