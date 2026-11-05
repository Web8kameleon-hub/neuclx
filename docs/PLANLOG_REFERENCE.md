# NeuCLX — Planlog Reference

`declared`: Version 1.0, 2026-11-04. This is the development plan, decision log
and reference catalog for the direction approved by the user. Planned behavior
does not establish runtime capability. Repository rules in [AGENTS.md](../AGENTS.md)
remain authoritative.

## Approved direction

`declared`: Develop NeuCLX as an advanced AI available free of charge to users.
Prioritize four approved areas: GRAM/HVWO memory, reasoning and understanding,
mandatory JONA governance, and reproducible evaluation. Top-five AI performance
is a research objective, without an established ranking or promised date.

`declared`: Reuse only material needed for a demonstrated requirement. Do not
assemble every ecosystem service into the core. Free access is a product goal;
it does not establish an open-source license or eliminate operating costs.

`unavailable`: Public service funding/capacity, independent comparative rank,
held-out general reasoning quality, and proof that the ecosystem already contains
everything needed for the objective.

## Architecture decisions

| ID | State | Decision |
|---|---|---|
| D01 | declared | GRAM/HVWO is the primary memory and relationship research direction; graph/directional operators must earn promotion through quality tests. |
| D02 | declared | JONA is mandatory at release and before relevant side effects. No character/personality component replaces the sandbox decision. |
| D03 | declared | Pillar is a blog publishing engine with editorial rules. Its academic explanation/argumentation rules are a separate reuse candidate; publication itself is an optional downstream operation. |
| D04 | declared | The user identifies Pillar's academic reasoning/explanation quality as important. Verify the actual rule enforcement and outputs rather than treating academic vocabulary or a style score as proof. |
| D05 | declared | Identify the exact NIN linked to JONA character. Do not substitute intent NIN or telemetry NIN merely because they share a name. |
| D06 | declared | Keep WWWMMM/XLC symbol profiles distinct from OS-CLX WWWMMM runtime state. Preserve domain fields and provenance. |
| D07 | declared | Longo, RehaConnect and AGIXmed contribute only narrowly selected contracts or mechanisms after verification; application stacks are not default core dependencies. |
| D08 | declared | External models may be studied or called through explicit adapters. Code reuse requires pinned provenance, applicable licensing conditions and duplicate detection. |
| D09 | declared | Core/tests remain Python-standard-library-only. Explicit local/hosted adapters are allowed only with JONA checks before outbound requests and returned results; no implicit weight download or hidden fallback. |
| D10 | declared | One main tree, no alternate branches, no rewritten history. No commit or public registry publication is authorized by this document. |

`computed`: The current experimental signal gateway includes `pillar` among
required control callbacks. That reflects an earlier architectural assumption,
not a verified Pillar integration. Correcting that dependency is planned work;
this document does not modify the gateway.

## Evidence and lifecycle

`declared`: Lifecycle labels complement, rather than replace, the five evidence
states measured/computed/declared/unavailable/not_implemented.

| Label | Required evidence |
|---|---|
| DISCOVERED | Repository, exact path and revision were found. |
| VERIFIED | Implementation, contract and relevant tests were inspected. Explicitly distinguish static review from executed tests and record their actual results. |
| INTEGRATED | Real NeuCLX-to-component communication or execution is demonstrated with pinned versions, traces, negative cases and reproducible evidence. A callback name, import or mocked upstream alone is insufficient. |
| MISSING | The specific object was not found in a documented search scope. Retain queries, revisions, paths and failure reasons; do not generalize to unsearched sources. |

`declared`: Follow Discover → Verify → Reuse → Integrate → Validate. Integration
can be experimental; default promotion requires validation against the existing
baseline. Never convert source declarations, synthetic signals or heuristics into
measured facts.

## Ordered work and exit criteria

| Phase | State | Work | Exit evidence |
|---|---|---|---|
| P0 — baseline | declared | Resolve missing neuclx.data test imports, fabricated agent successes, JONA bypasses and main-only CI contradictions. Review the unnecessary mandatory Pillar slot. | Full applicable tests and rejection paths pass; current release-candidate checks and documentation agree. |
| P1 — source verification | declared | Finish the exact NIN–JONA binding search; inspect Pillar rule enforcement/tests; identify NanogridData precisely. Record algorithms, dependencies, licenses and duplicate copies. | Each chosen component has repository/path/commit/hash, contract, test coverage, execution status, dependencies, verified links and a reuse decision. |
| P2 — quality baseline | declared | Version retrieval, arithmetic, multi-step reasoning, code, Albanian/English, contradiction and abstention tasks. Include academic explanation assessment. | Raw per-task outputs reproduce scores; development and held-out data remain separate; resource conditions and acceptance criteria are declared before the evaluation. |
| P3 — selective reuse | declared | Select the smallest GRAM/HVWO improvement and the applicable Pillar explanation rules. Evaluate Longo/Reha mechanisms only against explicit needs. | Isolated adaptation, provenance, bounded resource use and negative tests; no mandatory remote service or silent fallback introduced. |
| P4 — experimental integration | declared | Connect one verified component at a time through the appropriate contract and JONA boundary. | Real integration trace including unavailable/rejected cases; source claims retain their evidence state; no fabricated controller or upstream success. |
| P5 — validation and promotion | declared | Compare each candidate against the baseline and report regressions, correctness, abstention, latency and memory. | Reproducible results justify the declared acceptance criteria; candidate remains optional if evidence is insufficient. |
| P6 — free public access | declared | Establish deployment capacity, operating budget, privacy, abuse controls and service limits appropriate to measured behavior. | Tested end-to-end user flow, recovery/security checks, documented limits and a sustainable operating plan. No registry publishing while maturity gates prohibit it. |

`declared`: A newly trained or adapted neural-model track requires a separate
architecture decision: model origin, allowed dependencies, hardware, data rights,
training/evaluation separation and changes to the current no-weights rule. Do not
hide that decision inside a memory-graph or external-reference task.

## Pillar academic explanation track

`measured`: Source review found section-based article generation and editorial
checks for word count, code/metric patterns, placeholders and academic markers.
The content-factory strategy also gathers code snippets and requests metrics.
These are observations of the reviewed code, not a measured academic-quality score.

`computed`: The reviewed publisher and generator are distinct paths. The strategy
file's require_expert_review field does not itself establish a human approval
workflow. Clisonix Blerina includes fallback prose; its provenance must remain
explicit in any selected adaptation.

`declared`: Extract reusable explanation rules as explicit requirements. Proposed
evaluation checks: supported claims and citations, correct intermediate steps,
clear premises and conclusions, explicit assumptions, counterevidence, limitations,
and separation of observation from hypothesis. These proposed checks are not
assertions that every one is currently implemented in Pillar.

`declared`: Compare explanations for the same tasks with and without the selected
rules. Use answer correctness plus a declared explanation rubric and independent
review where needed. More words, academic phrasing, code fences or numeric-looking
metrics do not independently establish better reasoning.

`unavailable`: A held-out evaluation of Pillar's academic explanation quality and
proof that its rules improve NeuCLX reasoning.

## Pinned ecosystem references

`measured`: These entries summarize prior read-only source inspection. VERIFIED
below means static code/test review only; tests were not executed in that audit.
No component in this catalog has demonstrated INTEGRATED status with NeuCLX.
Repository prefix: https://github.com/Web8kameleon-hub/.

| Reference | Repository, path | Commit SHA | Evidence / decision |
|---|---|---|---|
| R01 GRAM | clisonix-evolution; packages/gram/core.py | f120457ab2c38c5bac9d23b62fca5d4ea6f17a0e | declared; DISCOVERED directional graph and heuristic connection logic; memory candidate |
| R02 Pillar Clisonix | clisonix.com; services/content-factory/content_pillar_strategy.py; services/blerina/main.py; services/blog_publisher/main.py | 3a7eb115a71f063dc0bb7b54664583a1c4a2b08c | declared; DISCOVERED editorial/generation/publication code; specific publication tests not found in audited paths |
| R03 Pillar Kloud | Kloud; same three paths as R02 | 9e2d2356d98c427a3f2eb6cf52e1c6618a608577 | declared; DISCOVERED; do not assume feature parity with Clisonix |
| R04 Longo | LONGO-; java-longo/src/main/java/com/clisonix/longo/{LongoStore,LongoCollection,StorageEngine,LongoServer}.java; java-longo/src/test/java/com/clisonix/longo/LongoRuntimeTest.java | 62c87f9c6072a2b36bd90bc2a1edd38873280a61 | computed; VERIFIED statically for storage and test coverage; Java service adoption deferred |
| R05 RehaConnect | rehaconnect; backend/rehaconnect-api/src/main/java/com/rehaconnect/{WorkspaceService,ClinicStore}.java; controllers/BillingController.java under that package | a611120308b5e72cf468d90b1cb618193bf36488 | computed; VERIFIED statically with WorkspaceServiceTest.java and AssistantBridgeTest.java under src/test/java/com/rehaconnect; authorization/contract reference |
| R06 AGIXmed | ultrawebthinking; apps/web/components/AGIXmed/index.tsx; backend/server.ts; apps/web/app/api/agixmed/{consultations,auth/login}/route.ts | e2cc2160080107df13e4779d8280789ee8008c24 | computed; DISCOVERED UI, mock/random analysis and demo persistence/auth; not an admitted diagnostic engine |
| R07 NIN intent | clisonix.com; ocean-core/nin_engine.py; tests/unit/test_module_lab_integration.py | 3a7eb115a71f063dc0bb7b54664583a1c4a2b08c | computed; VERIFIED statically for limited intent tests, not the requested NIN–JONA binding |
| R08 Cwy NIN bridge | Cwy; engines/signals/clisonix-bridge.ts; ecosystem.config.js | 0f6d038564512353a98be554170890ef99099d7b | declared; DISCOVERED HTTP client and process reference; exact character binding MISSING in audited scope |
| R09 JONA character | clisonix.com; apps/api/services/jona_character.py | 3a7eb115a71f063dc0bb7b54664583a1c4a2b08c | declared; DISCOVERED personality/oversight/EEG interfaces; mock/simulated defaults must not become measured evidence |
| R10 WWWMMM / Fluid / Nanogrid | OS-CLX; runtime/pkg/contracts/contracts.go; docs/runtime/nodedb-fluid-cycle-engine.md | c54e104f94adb972b0c69e2a6ac750242c0c1048 | declared; typed state and ModuleHint references; runtime parity not verified |
| R11 LAGTER | clisonix-evolution; docs/LAGTER_PROTOCOLS.md | f120457ab2c38c5bac9d23b62fca5d4ea6f17a0e | declared; paired-signal/audit specification, not runtime integration |
| R12 Neurosonic rules | www.neuroconic.eu; docs/Constitution.md; docs/guides/hvo-memory.md | 23f5da06bf0b6b6325129e7cf6f18f180552d1ec | declared; constitutional and memory-rule references pending native tests |

`declared`: Brace groups in this catalog abbreviate multiple paths; they are not
literal filenames. Keep algorithm novelty, code authorship, copied implementations
and standard techniques distinct. Full provenance belongs in [SOURCE_LEDGER.md](SOURCE_LEDGER.md).

## External reference candidates

`measured`: Earlier reference checks identified the following source surfaces.
Their presence here authorizes no installation, code copy or weight download.

| Candidate | Source surface | Revision / admission |
|---|---|---|
| rank_bm25 | rank_bm25.py; LICENSE | measured: commit 47aa3ddf8dc1ebeb7ef4e65f2b4536af44594099 pinned in the source ledger; native experimental BM25 remains optional |
| llm.c | https://github.com/karpathy/llm.c | declared: C/CUDA training-code study candidate; repository license display reviewed as MIT; exact source/commit not selected |
| Qwen3-8B | https://huggingface.co/Qwen/Qwen3-8B/blob/main/LICENSE | declared: license reference reviewed as Apache-2.0; immutable model revision unavailable here; weights not admitted |
| Llama 3.1 | https://huggingface.co/meta-llama/Llama-3.1-8B/blob/main/LICENSE | declared: model-specific license reference; immutable model revision unavailable here; weights not admitted |
| SymPy / lm-evaluation-harness | Existing entries in SOURCE_LEDGER.md | declared: mathematics/evaluation references; not core or core-test dependencies |

`declared`: Code, weights, datasets and model-generated training data require
separate provenance/rights checks. A permissive code license does not establish
permission for every weight or dataset. Reference discovery does not prove a
model is an appropriate base for NeuCLX.

## Planlog

| Date | State | Recorded event | Consequence |
|---|---|---|---|
| 2026-11-04 | declared | User approved GRAM/HVWO, reasoning, JONA and evaluation priorities. | Use P0–P6 gates; no claim of completed advanced-model capability. |
| 2026-11-04 | declared | User requested selective reuse without unnecessary complexity. | Require an explicit need and baseline comparison for each dependency. |
| 2026-11-04 | declared | User clarified Pillar as blog engine and emphasized its academic explanation rules. | Separate optional publishing from explanation-rule reuse; verify quality through P2/P3. |
| 2026-11-04 | declared | User identified NIN linked to JONA character. | Keep exact binding search open; do not substitute other NIN variants. |
| 2026-11-04 | declared | User approved the development route and requested Planlog Reference. | Create this planning artifact; current core constraints remain unchanged. |

`declared`: Update the log when evidence changes a decision. Each future entry
must include the decision, source revision or measured artifact, affected phase,
acceptance result and remaining unknowns. Never mark a phase complete merely
because a document, callback, scaffold or endpoint exists.

## Current evidence and next work

`measured`: Earlier local checks recorded 12 focused retrieval/learning tests and
10 signal-contract tests passing. Retrieval's six authored development fixtures
produced baseline 4/6 and experimental BM25 6/6. These are historical local checks,
not new test runs or held-out quality evidence for this planning document.

`measured`: The previously run complete Python suite encountered the missing
neuclx.data import. [LEARNING.md](LEARNING.md) documents retrieval limits;
[SIGNAL_ARCHITECTURE.md](SIGNAL_ARCHITECTURE.md) distinguishes the experimental
callback contract from actual ecosystem integration.

`declared`: Next implementation work starts with P0. It must preserve source
provenance and remove unsupported runtime success claims before expanding model
capability. This document itself changes no runtime code and makes no commit.
