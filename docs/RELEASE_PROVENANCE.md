# Release provenance policy

Every NeuCLX release is built from an immutable `vMAJOR.MINOR.PATCH` tag whose commit is already in `main`.

The release workflow produces a wheel, reproducible source archive, SHA-256 checksums, SPDX 2.3 SBOM, and NeuCLX truth manifest. GitHub Actions then creates SLSA build provenance and SBOM attestations with Sigstore/OIDC through `actions/attest@v4`.

The NeuCLX manifest complements—but never replaces—the platform-generated in-toto/SLSA attestation. Comparative benchmarks, certifications, and audits remain explicitly `not_measured`, `not_claimed`, or `not_available` until corresponding evidence exists.

Verify a downloaded artifact with:

```bash
gh attestation verify neuclx-0.1.0-py3-none-any.whl --repo Web8kameleon-hub/neuclx
sha256sum --check SHA256SUMS
```
