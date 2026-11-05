# Benchmark contract

NeuCLX may claim superiority over another system only when a checked-in report contains:

- exact NeuCLX commit and competitor version;
- public or committed dataset with license/provenance;
- task definition and scoring code;
- hardware, operating system, runtime and resource limits;
- raw outputs and failure counts;
- quality, latency, memory, energy (when measurable), and provenance coverage;
- at least three runs where nondeterminism exists.

Until then, “more advanced than GPT, Gemini, DeepSeek, or Perplexity” has state `declared`, not `measured`.


## Recorded runs

- `benchmarks/results/truthfulqa-proxy-25.json` (`measured`, development only): 25 TruthfulQA rows with their own source URL, proxy scoring, one run, no competitor baseline. It cannot support any ranking claim under this contract.
