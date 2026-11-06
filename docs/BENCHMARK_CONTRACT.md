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
- `benchmarks/results/truthfulqa-live-5-e089965.json` (`measured`, development only): five first-in-file-order rows with HTTPS sources, run through NeuCLX Hybrid-Fluid at commit `e0899654dbc920b93333bdb7ad193d62d76a398a`. All five responses abstained; four sources were unavailable (one HTTP 404 and three with no query-matching text), and one source was declared while its response remained unavailable. There were zero request errors and mean latency was 1861.2 ms. This is a single five-row proxy run, not a quality or ranking result.
