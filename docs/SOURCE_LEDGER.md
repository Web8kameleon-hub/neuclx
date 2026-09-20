# Source ledger

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
