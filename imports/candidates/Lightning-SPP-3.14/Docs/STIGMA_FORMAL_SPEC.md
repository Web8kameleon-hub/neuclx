# Stigma Formal Specification (v1.0)

## 1. Scope

This document defines the formal behavior of the Stigma pipeline in Lightning SPP.

Pipeline phases:
1. scan
2. resonance
3. imprint
4. enhancement
5. stabilization
6. print

## 2. Data Model
### 2.1 Input Signal
- Type: byte sequence `B = {b0, b1, ..., bn-1}`
- Domain: `bi in [0, 255]`

### 2.2 Resonance Signal
A normalized scalar in `[0, 1]` representing field coherence:

`R = coherence(B)`

Implementation note: in current runtime, coherence is approximated through image-domain transformations (grayscale/contrast/edge enhancement), then evaluated indirectly through processing behavior.

### 2.3 NanoDecibel Signature
NanoDecibel is defined as:

`NdB = 20 * log10(max(R, epsilon)) * 10^9`

where `epsilon = 1e-12` avoids `log10(0)`.

### 2.4 Imprint Field
Imprint is the stabilized representation of transformed signal after resonance-aware enhancement.

`I = stabilize(enhance(resonance(scan(B))))`

## 3. Functional Requirements
### FR-1 Scan
- The system shall accept binary or decodable image input.
- If decoding fails, the system shall build a deterministic grayscale raster from binary payload.

### FR-2 Resonance
- The system shall apply mode-specific transforms.
- Modes and intent:
  - Lightning: low-latency contrast/grayscale
  - TideWave: coherence amplification
  - Resonance: edge/tension extraction
  - NanoDecibel: high-fidelity edge + amplitude emphasis

### FR-3 Imprint/Enhancement
- Stigma print path shall apply resonance smoothing before final compression.

### FR-4 Stabilization
- Output shall be deterministic for deterministic input and same configuration.

### FR-5 Print
- Stigma output shall be persisted as compressed artifact.

## 4. Non-Functional Requirements
### NFR-1 Determinism
For fixed input and fixed mode, the output hash should remain stable across runs in the same version.

### NFR-2 Performance Targets
- Instant: target < 1 ms for small payloads
- UltraFast: target < 5 ms
- Lightning: target < 10 ms

### NFR-3 Security
- License issuance endpoint requires bearer auth.
- API requests are rate limited.
- License at-rest storage is encrypted.

## 5. Acceptance Criteria
1. Golden test vectors pass for scan/process/print paths.
2. Runtime metrics endpoint exposes pipeline success/failure and phase latency averages.
3. Dashboard renders license status and metrics snapshot.

## 6. Versioning
- Spec version: 1.0
- Backward compatibility: changes to formulas or thresholds require spec version bump.

