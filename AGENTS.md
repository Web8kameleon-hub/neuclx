# NeuCLX repository rules

1. Never invent a measurement, source, capability, benchmark, or runtime state.
2. Every externally visible datum must use one of: `measured`, `computed`, `declared`, `unavailable`, `not_implemented`.
3. JONA is the mandatory sandbox boundary. No code path may bypass its decision.
4. Core code and tests use only the Python standard library. No external LLM, hosted inference API, model weight, or silent fallback.
5. Imported ideas require an entry in `docs/SOURCE_LEDGER.md` with repository, path, revision, and adaptation status.
6. Work on a branch; require tests before merging; do not force-push protected history.
7. A future capability is documentation, never a runtime capability, until its test passes.

