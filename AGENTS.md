# NeuCLX repository rules

1. Never invent a measurement, source, capability, benchmark, or runtime state.
2. Every externally visible datum must use one of: `measured`, `computed`, `declared`, `unavailable`, `not_implemented`.
3. JONA is the mandatory sandbox boundary. No code path may bypass its decision.
4. Core code and tests use only the Python standard library. No external LLM, hosted inference API, model weight, or silent fallback.
5. Imported ideas require an entry in `docs/SOURCE_LEDGER.md` with repository, path, revision, and adaptation status.
6. NeuCLX is one continuously growing tree. The only permitted branch is `main`.
7. Commit linearly to `main`; parallel branches, feature branches, release branches, and pull-request refs are forbidden.
8. CI and CD must reject every Git ref except `refs/heads/main`. Never force-push or rewrite `main` history.
9. A future capability is documentation, never a runtime capability, until its test passes.
10. Every `main` commit must build curated Python, npm, and Rust release candidates with tests, benchmark evidence, and current documentation.
11. Do not publish to PyPI, npm, or crates.io while `maturity.json` is `developing` or `public_registry_publish` is false.
