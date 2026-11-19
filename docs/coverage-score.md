# Public-Evidence Coverage Score (`docs/coverage-score.md`)

Handling: Unclassified — public

## Purpose and Scope Boundary

The **public-evidence coverage score** measures how much of a flight-critical rotating part's manufacturing and inspection thread is backed by verifiable public citations or content-hashed evidence pointers.

- **What it measures:** The completeness of the **public record** in a digital-thread YAML trace.
- **What it does NOT measure:** It never scores a real organization's engineering capability, manufacturing quality, or internal compliance. Missing public evidence means the record must be requested under a private data-sharing agreement—not that a step failed to occur.

---

## Required `ProcessStep` Kinds

Per `schema/openchokepoint.yaml`, a complete rotating-part digital thread spans all **10** `ProcessStep.step_kind` enum values:

1. `build`
2. `stress_relief`
3. `hip` (Hot Isostatic Pressing)
4. `heat_treatment`
5. `machining`
6. `finishing`
7. `cleaning`
8. `inspection`
9. `balancing`
10. `assembly`

---

## Grade Weighting & Scoring Formula

Each of the 10 `step_kind` slots receives a score based on the highest `evidence_grade` among `EvidenceRecord` objects linked to a `ProcessStep` of that kind via an `evidenced_by` link:

| Evidence Status | Weight | Meaning |
| :--- | :---: | :--- |
| `confirmed` | **1.00** | Linked `EvidenceRecord` carries `evidence_grade: confirmed` (primary public document or content hash). |
| `reported` | **0.50** | Linked `EvidenceRecord` carries `evidence_grade: reported` (secondary/press reporting only). |
| `inferred` | **0.25** | Linked `EvidenceRecord` carries `evidence_grade: inferred`. |
| `unverified` | **0.00** | `ProcessStep` exists in the trace, but has no `evidenced_by` link to an `EvidenceRecord`. |
| `missing` | **0.00** | No `ProcessStep` of this `step_kind` is present in the trace. |

$$\text{Coverage (\%)} = \frac{\sum_{k=1}^{10} \text{weight}(k)}{10} \times 100$$

---

## Worked Example: `examples/synthetic-turbopump-thread.yaml`

Running `python tools/coverage.py examples/synthetic-turbopump-thread.yaml` produces **80.0% (8.0 / 10.0)**:

- **Covered (`confirmed`, 1.0 each — 8 steps):** `build`, `stress_relief`, `hip`, `heat_treatment`, `machining`, `cleaning` (via `stp-1706` -> `evd-1706`), `inspection`, `assembly`.
- **Missing (`0.0` each — 2 steps):** `finishing` and `balancing` have no `ProcessStep` entries in the synthetic file.
- *(Note: Serial `R-100-0008` in the same trace also demonstrates an unverified `cleaning` step `stp-1806` with no `evidenced_by` link, while `R-100-0007` supplies `confirmed` cleaning evidence `evd-1706`, so the trace-level `cleaning` slot scores `1.00`.)*

---

## Regenerating the Gap Atlas

Run a single command from the repository root (zero network access):

```bash
python tools/coverage.py --atlas --write docs/gap-atlas.md
```
