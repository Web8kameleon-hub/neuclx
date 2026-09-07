# NeuCLX architecture

NeuCLX starts as a small auditable cognitive kernel, not a disguised wrapper around an external model.

## Runtime path

1. Input is deterministically tokenized.
2. Each token becomes a cognitive cell in a sparse, multi-layer HVWO lattice.
3. H, V, JP, JL, VP, VL and W operators provide directional and wave projections.
4. A result is emitted as a typed datum with an epistemic state and method.
5. JONA evaluates every datum before release.
6. Stigma Film Memory compresses the released datum into an immutable frame.
7. The journey ledger records the frame as a successful stepping stone without changing its epistemic state.

## One-page interface

The standard-library HTTP server exposes a single multifunctional chat surface and two JSON endpoints: `POST /api/respond` and `GET /api/journey`. The browser loads compact journey records and never needs the entire cognitive lattice.

## Capability boundary

The current kernel implements deterministic ingestion, sparse cell construction, HVWO projection/contraction/wave transformation, evidence-bound retrieval, and JONA output policy. It is not yet a general-purpose language model. Claims of superiority over GPT, Gemini, DeepSeek, or Perplexity remain `declared` until a versioned benchmark harness measures them.

## Planned native evolution

- compositional cell algebra and temporal memory;
- CLX.I reasoning stages and GRAM mesh adaptation;
- repository corpus ingestion with immutable source revisions;
- adversarial JONA tests;
- reproducible quality, latency, memory, energy, and provenance benchmarks.
