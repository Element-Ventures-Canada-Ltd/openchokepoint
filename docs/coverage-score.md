# Public-Evidence Coverage Score

Handling: Unclassified — public

## Overview

The **Public-Evidence Coverage Score** measures the completeness of the public record for a specific digital thread. It does not measure the quality of a supplier or the safety of a part; it measures how much of the "story" of a part is backed by verifiable public evidence.

## Scoring Methodology

For a **flight-critical rotating part** (e.g., a turbopump rotor), we define four mandatory process steps that must be evidenced to achieve a full score.

### 1. Required Step Kinds
| Step Kind | Description |
|-----------|-------------|
| `material_lot` | Evidence of raw material origin and batch properties. |
| `build` | Evidence of the primary forming process (e.g., Additive Manufacturing, Forging). |
| `inspection` | Evidence of non-destructive testing (NDT) or dimensional verification. |
| `assembly` | Evidence of integration into a higher-level component. |

### 2. Evidence Weights
The score for each required step is determined by the `evidence_grade` of the associated `EvidenceRecord`:

- **Confirmed (1.0):** Evidence is verified by a third party or cryptographic proof.
- **Reported (0.5):** Evidence is self-reported by the manufacturer without independent verification.
- **Missing (0.0):** No public evidence record exists for this step.

### 3. Calculation
The total score is the average of the best evidence found for each of the four required categories:

$$Score = \frac{\sum \max(Weight_{kind})}{4}$$

## Worked Example: Synthetic Turbopump Rotor
File: `examples/synthetic-turbopump-thread.yaml`
Trace: `R-100-0007`

1. **Material Lot:** `ev-101` (confirmed) -> **1.0**
2. **Build:** `ev-102` (confirmed) -> **1.0**
3. **Inspection:** `ev-108` (confirmed) -> **1.0**
4. **Assembly:** `ev-109` (confirmed) -> **1.0**

**Total Score: 1.0 (100%)**

*Note: While the trace contains other steps (Post-processing, Cleaning), the coverage score focuses on the critical path defined for rotating parts.*
