# NeuCLX

NeuCLX is the clean, sovereign AI synthesis repository for the Web8kameleon-hub profile.

## Non-negotiable truth contract

NeuCLX never fills an evidence gap with an artificial result. Every value carries one explicit epistemic state: `measured`, `computed`, `declared`, `unavailable`, or `not_implemented`.

The only mandatory policy boundary is the JONA sandbox.

## Dependency policy

The core runtime and tests use the Python standard library only. Local or hosted inference is opt-in through the OpenAI-compatible `ModelAdapter`; JONA checks requests and returned results. No model runtime or weights are installed or downloaded by NeuCLX, and there is no fallback when an endpoint is unavailable.

## Source data contracts

`neuclx.data` provides standard-library record normalization and evidence-contract
validation. Normalized records preserve source metadata; validation requires the
repository's evidence fields and passes the content through JONA. Longo source
lineage and license boundaries are recorded once in [SOURCE_LEDGER.md](docs/SOURCE_LEDGER.md).
NeuCLX does not vendor the Java Longo implementation or require Azure.

## JONA-gated pipeline stages

`neuclx.pipeline` provides a standard-library runner for explicitly registered
Python stage callbacks. JONA must allow each stage input and output; held or
rejected data stops the pipeline, and stage exceptions are surfaced. Pipeline
definitions are pinned to source/revision metadata. NeuCLX does not dynamically
load YAML pipelines or execute source-provided `CODE`/`TOOL` steps.

## Run the single-page interface

```bash
PYTHONPATH=src python -m neuclx.web
```

Open `http://127.0.0.1:8787`. Every completed response becomes a success stepping stone while retaining its honest epistemic state. Stigma Film Memory stores immutable compressed frames so the journey remains lightweight.

## Optional Clisonix MegaLayer analysis

NeuCLX can request analysis metadata from the Clisonix MegaLayer `POST /process`
endpoint running on loopback. Set `NEUCLX_MEGALAYER_URL` to the complete local
endpoint URL before starting the server. Remote/hosted endpoints are rejected.
When the variable is unset, the reasoning response reports MegaLayer as
`not_implemented`. When configured, JONA evaluates the query and returned data;
the validated layer metrics are labeled `computed` and shown as analysis metadata,
not as evidence or a generated answer. Upstream errors are returned explicitly.

The MegaLayer API inspected for this adapter exposes `/process`. The Clisonix
launcher and backend proxy also reference a different `/api/v1/megalayer` path;
verify which endpoint your running deployment serves before configuring it.

## Optional model endpoint

`ModelAdapter` can call an explicitly configured OpenAI-compatible chat-completions
endpoint. It is disabled by default, accepts loopback HTTP(S) for `local` and HTTPS
for `hosted`, does not follow redirects, and requires callers to supply the endpoint
and model name. An API key can be read from a named environment variable; neither
the key nor the endpoint URL is added to result metadata. JONA checks the outbound
request and the returned result. HTTP errors, invalid responses, and missing
credentials are surfaced; there is no retry or fallback. This adapter does not
download weights or itself install/run a local inference runtime.

To opt in for a local OpenAI-compatible runtime, set these PowerShell variables
before starting NeuCLX:

```powershell
$env:NEUCLX_MODEL_ENABLED = 'true'
$env:NEUCLX_MODEL_PROVIDER = 'local'
$env:NEUCLX_MODEL_NAME = 'your-local-model'
$env:NEUCLX_MODEL_ENDPOINT = 'http://127.0.0.1:8000/v1/chat/completions'
```

For hosted inference, use `NEUCLX_MODEL_PROVIDER='hosted'`, an HTTPS endpoint,
and optionally `NEUCLX_MODEL_API_KEY_ENV` naming an environment variable that
holds the key. The endpoint must implement the OpenAI chat-completions request
and response shape. `/api/respond` and `/api/reason` use this adapter only when
enabled; generated answers remain `computed` and are not independently verified.

## Public web evidence

The chat and reasoning APIs accept an optional `source_urls` array (up to 10
URLs per request). The UI exposes the same input as one public HTTPS URL per
line. NeuCLX fetches pages directly without a proxy or redirect, rejects
non-public DNS addresses and credential-bearing URLs, and extracts at most one
600-character matching excerpt per page. Only the excerpt, source URL, content
digest, retrieval time, and retrieval state are retained in the response ledger;
the full page is not persisted. Source text remains `declared` and JONA is
evaluated before retrieval and before release.

This is direct-URL reading, not web-wide URL discovery or a crawler. The
Clisonix Web Reader and Developer Center are listed as possible sources, but
their pages did not expose a concrete public reader API contract during
inspection. Ocean AI hosted inference is not called.
