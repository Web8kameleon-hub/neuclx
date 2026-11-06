# Release provenance policy

Every NeuCLX candidate is built from a direct commit to `main`. Tags and other refs are rejected by CI/CD.

The main-commit workflow produces a wheel, source archive, SHA-256 checksums, SPDX 2.3 SBOM, and NeuCLX truth manifest. GitHub Actions creates build provenance and SBOM attestations with Sigstore/OIDC through `actions/attest@v4`. These are candidate artifacts, not public releases.

NeuCLX remains `developing` and `public_registry_publish` is false, so candidates are never published to PyPI, npm, or crates.io. The manifest complements—but never replaces—the platform-generated attestation. Comparative benchmarks, certifications, and audits remain explicitly `not_measured`, `not_claimed`, or `not_available` until corresponding evidence exists.

Verify a downloaded artifact with:

```bash
gh attestation verify neuclx-0.1.0-py3-none-any.whl --repo Web8kameleon-hub/neuclx
sha256sum --check SHA256SUMS
```
