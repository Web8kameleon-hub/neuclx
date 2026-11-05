# Web8kameleon-hub research and NeuCLX development target

`measured`: On 2026-11-04, the connected GitHub repository search for
`user:Web8kameleon-hub` returned 21 repositories, including private repositories.
Selected file reads succeeded. This is a discovery snapshot, not an exhaustive
code audit, a persistent runtime connection, or verification of every repository.

## Source findings

`measured`: The following files were read at explicit commits. Blob identifiers
and adaptation status are recorded in SOURCE_LEDGER.md. No source code was
imported or executed during this review.

| Repository and path | Finding | Adaptation decision |
|---|---|---|
| clisonix-evolution / packages/gram/core.py | Node graph, directional links, similarity scoring and automatic connection code | declared: candidate for a native, evidence-preserving memory graph; not a demonstrated language model |
| Kloud / protocol/src/governance_contracts.rs | Three governance outcomes and risk-dependent rules | declared: study only; replace string quality ordering and prohibit its approved-path sandbox bypass |
| Lightning-SPP-3.14 / Docs/STIGMA_FORMAL_SPEC.md | Pipeline specification, deterministic artifact requirements and latency targets | declared: design reference; targets are not measured NeuCLX performance |
| Kloud / ocean_training.py | Sends HTTP queries and counts responses and timings | computed: this script does not itself implement parameter training or validate answer correctness; do not treat HTTP success as learning |

`computed`: The inspected GRAM code uses text similarity and heuristic graph
connections. Direction names and resonance scores alone do not establish semantic
understanding, calibrated confidence, or general reasoning quality.

`declared`: The clisonix-evolution and LONGO- README files mention Ollama, vLLM,
PyTorch and Transformers. These statements are not runtime verification. Such
dependencies are not core dependencies; any local runtime must be explicitly
configured through an adapter, and model weights are not downloaded implicitly.

## Top-five objective

`declared`: The user's objective is for NeuCLX to reach the top five AI models.
This is a research objective, without a promised rank or completion date.

`unavailable`: Current comparative rank, a selected independent leaderboard,
competitor version set, training-compute budget, and evidence that all required
materials already exist in these repositories.

`declared`: A ranking claim requires a named evaluation and dated model versions,
published scoring rules, an unseen evaluation split, equal tool and resource
conditions, raw outputs, failure accounting, and uncertainty reporting. A top-five
result on a narrow task must retain that scope rather than imply overall rank.

## Ordered development gates

1. `declared`: Restore the complete Python test suite, remove fabricated agent
   successes, enforce JONA on every output and relevant side effect, and align
   CI/CD with the main-only policy. Acceptance: regression and rejection tests
   pass, including callers using public APIs directly.
2. `declared`: Complete the source inventory with pinned commits, content hashes,
   license review, dependency inspection and duplicate detection. The user
   authorized pipeline-source reuse from the identified Web8kameleon-hub
   repositories; each copied/adapted file still requires path-level provenance,
   applicable notices, dependency review and secret scanning. Acceptance: each
   adaptation has a reproducible source-ledger entry and explicit decision.
3. `declared`: Establish quality evaluation for retrieval, multi-step reasoning,
   arithmetic, code tasks, Albanian/English, contradictory evidence and abstention.
   Measure correctness separately from availability, latency and citation presence.
   Acceptance: versioned task definitions and raw per-task results can reproduce
   the aggregate scores; development examples are excluded from the held-out set.
4. `declared`: Adapt one GRAM-inspired memory improvement using the standard
   library, bounded growth, explicit provenance and JONA authorization. Acceptance:
   compare against existing retrieval on the held-out tasks and report regressions,
   memory usage and latency alongside gains. Do not promote on unit tests alone.
5. `declared`: Select an independent comparison track, pin comparison systems and
   publish reproducible evidence before any rank claim. External comparison
   tooling must not become a hidden model fallback in the NeuCLX runtime.

## Pipeline source discovery, 2026-11-05

`measured`: GitHub tree listings at the pinned revisions below exposed candidate
AI, data-ingestion, reasoning, signal and CI/release paths. This was path
discovery only; implementations, licenses, dependencies and duplicate content
have not yet been reviewed as a complete set. No source pipeline has been copied
or executed as part of this discovery.

| Repository | Revision | Candidate paths | License metadata | Status |
|---|---|---|---|---|
| Web8kameleon-hub/Kloud | 9e2d2356d98c427a3f2eb6cf52e1c6618a608577 | `ai_agi_pipeline.py`; `core/pipelines/pipeline_framework.py`; `hybrid_protocol_pipeline.py`; `airflow/dags/{clinicaltrials,crossref,openalex,openfda,pubmed,semantic_scholar}_ingest.py`; `app/modules/auto_adapt_trainer.ts` | NOASSERTION | measured: discovered; no adaptation |
| Web8kameleon-hub/clisonix.com | 3a7eb115a71f063dc0bb7b54664583a1c4a2b08c | `ai_agi_pipeline.py`; `.github/workflows/{ingestion,ocean-model-stack,ocean-runtime-deploy,ocean-runtime-diagnostics}.yml` | NOASSERTION | measured: discovered; no adaptation |
| Web8kameleon-hub/clisonix-evolution | f120457ab2c38c5bac9d23b62fca5d4ea6f17a0e | `ai_agi_pipeline.py`; `airflow/dags/`; `ocean_core/pipelines/`; `ocean_core/reasoning_engine.py`; `hybrid_saas_platform/run_pipeline.py` | NOASSERTION | measured: discovered; overlaps candidates in Kloud; blob deduplication pending |
| Web8kameleon-hub/OS-CLX | c54e104f94adb972b0c69e2a6ac750242c0c1048 | `imports/kloud/ocean-core/pipelines/{reasoning,safety,context_manager}.py`; `runtime/internal/api/control_plane_pipeline.go`; `nin-engine/nin_core.py` | NOASSERTION | measured: discovered; reasoning and control-plane paths are distinct |
| Web8kameleon-hub/Ultrawebthinkig-v2 | 8c7263eee2dc25cdb7aa09c6c8b779929ae3cbf3 | `core/engines/{agi-engine,chat-engine,reasoning-engine}.ts` | NOASSERTION | measured: discovered; no adaptation |
| Web8kameleon-hub/Lightning-SPP-3.14 | c673de4c8e51321520250c9539ef4535a196d919 | `.github/workflows/{ci-cd,continuous-release-evidence,hosting-readiness,release-readiness,runtime-packages}.yml`; `Scripts/package-release.py`; `Scripts/validate-release-companions.py` | NOASSERTION at repository level; `Persistence/Longo` has a separately documented commercial boundary | measured: discovered; workflow code is CI/release, not an AI runtime |

`unavailable`: Path-level license rights, dependency inventories, secret scans,
blob-level duplication across these repositories, and a complete inventory of
all business workflows. `NOASSERTION` is GitHub repository metadata, not a
license grant. The existing Longo-specific license findings remain in
SOURCE_LEDGER.md and apply independently.

`declared`: The user's approval permits adapting selected pipeline code into
NeuCLX, including identified private repositories. It does not override source
licenses, third-party notices, secret removal, or the requirement that every
runtime path pass through JONA. Candidate discovery is not integration.

`not_implemented`: The original 2026-11-04 research review added no training
algorithm, model weights, external-inference integration, or new runtime
capability. A separately implemented OpenAI-compatible endpoint adapter is now
documented in README.md; no live provider was called during its tests.
