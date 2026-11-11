Handling: Unclassified — public

# Public-Evidence Coverage Score and Gap Atlas Methodology

This note defines how OpenChokepoint scores public-evidence coverage across a digital-thread trace (`tools/coverage.py`) and how the repository's cross-trace gap atlas ([`docs/gap-atlas.md`](gap-atlas.md)) is constructed.

In keeping with schema v0.2.1-draft and [`docs/digital-thread.md`](digital-thread.md), the coverage score measures **public visibility of the paper trail** — never part quality, engineering acceptance, or supplier performance. A low score on a public trace indicates where public disclosures stop and private manufacturing records begin.

---

## 1. Required `ProcessStep` Baseline for a Flight-Critical Rotating Part

Schema v0.2.1-draft (`schema/openchokepoint.yaml`) enumerates ten canonical controlled operation kinds (`ProcessStep.step_kind`) that form the complete manufacturing, post-processing, verification, and integration thread of an additively or conventionally manufactured flight-critical rotating turbopump component:

| # | `step_kind` | Role in the Digital Thread | Typical `EvidenceRecord.record_kind` |
|---:|---|---|---|
| 1 | `build` | Primary consolidation / additive build / casting / forging from a `MaterialLot` | `build_record`, `material_certificate` |
| 2 | `stress_relief` | Thermal stress-relief cycle prior to support removal or sectioning | `heat_treatment_record` |
| 3 | `hip` | Hot isostatic pressing to close internal porosity | `heat_treatment_record` |
| 4 | `heat_treatment` | Solution / aging / quench-and-temper thermal cycle | `heat_treatment_record` |
| 5 | `machining` | Datum generation, flow-path milling, interface turning, or grinding | `inspection_report`, `other` |
| 6 | `finishing` | Surface finishing, polishing, coating, or passivation | `inspection_report`, `other` |
| 7 | `cleaning` | Precision propellant-compatibility or oxygen/LOX cleanliness processing | `cleaning_certificate` |
| 8 | `inspection` | Non-destructive evaluation (CT, dye penetrant, ultrasonic) and dimensional inspection | `inspection_report` |
| 9 | `balancing` | High-speed dynamic rotor balancing | `balancing_record` |
| 10 | `assembly` | Sub-assembly or stage-level propulsion integration | `assembly_record`, `other` |

All ten `step_kind` values form the denominator ($N_{\text{req}} = 10$) for the **Required-Step Coverage Score**.

---

## 2. Evidence-Grade Weighting (`confirmed`, `reported`, `missing`)

By rule **DT-002** (`tools/validate.py`), real digital-thread records must be graded `confirmed` or `reported`; gaps are shown rather than inferred. For each `ProcessStep` $s$:

1. **Un-evidenced step (`missing`, weight `0.0`)**: If $s$ has no `evidenced_by` link pointing to a valid `EvidenceRecord` in the trace, the step has weight $w(s) = 0.0$ and is classified as `missing` with `gap_kind = "un_evidenced_step"`.
2. **Evidenced step**: If $s$ is linked via `evidenced_by` to one or more `EvidenceRecord` objects $E(s) = \{e_1, \dots, e_k\}$, let $g(e_i)$ be each record's `evidence_grade`. The effective grade of step $s$ is bounded by both the step's own grade and the strongest backing `EvidenceRecord` grade:
   $$\text{grade}_{\text{eff}}(s) = \min_{\text{rank}}\!\left(\text{grade}(s),\; \max_{\text{rank}}_{e \in E(s)} \text{grade}(e)\right)$$
   where $\text{confirmed} > \text{reported} > \text{missing}$.
3. **Numeric weights**:
   - `confirmed`: **$1.0$** — backed by an authoritative primary filing, statutory disclosure, or verified certificate pointer.
   - `reported`: **$0.5$** — backed by a secondary or company press-release announcement without primary certificate verification.
   - `missing`: **$0.0$** — either no `ProcessStep` of that kind is recorded (`not_recorded`) or the recorded `ProcessStep` carries no `EvidenceRecord` (`un_evidenced_step`).

---

## 3. Scoring Formulas

`tools/coverage.py` computes two complementary metrics for every trace and for every `SerialItem`:

1. **Required-Step Coverage Score ($\text{Score}_{\text{req}} \in [0, 1]$)**:
   Measures how much of the 10-step canonical digital thread is publicly evidenced:
   $$\text{Score}_{\text{req}} = \frac{1}{10} \sum_{k \in \text{REQUIRED\_STEP\_KINDS}} w(k)$$
   where $w(k) \in \{1.0, 0.5, 0.0\}$ is the strongest effective weight among steps of kind $k$.

2. **Recorded-Step Coverage ($\text{Score}_{\text{rec}} \in [0, 1]$)**:
   Measures what fraction of the steps actually recorded in the trace are backed by an `EvidenceRecord`:
   $$\text{Score}_{\text{rec}} = \begin{cases} \dfrac{1}{|S|} \sum_{s \in S} w(s) & \text{if } |S| > 0 \\ 0.0 & \text{if } |S| = 0 \end{cases}$$

---

## 4. Worked Example: `examples/synthetic-turbopump-thread.yaml`

`examples/synthetic-turbopump-thread.yaml` traces two fictional rotor serial items (`R-100-0007` and `R-100-0008`):

### Serial `ser-1007` (`R-100-0007`)
- **Recorded steps (`8`)**: `stp-1701` (`build`), `stp-1702` (`stress_relief`), `stp-1703` (`hip`), `stp-1704` (`heat_treatment`), `stp-1705` (`machining`), `stp-1706` (`cleaning`), `stp-1707` (`inspection`), `stp-1708` (`assembly`).
- **Evidence links**: Every step `stp-1701..1708` has a `confirmed` `evidenced_by` link to `evd-1700..1708` (all graded `confirmed`).
- **Missing required step kinds (`2`)**: `finishing` (`not_recorded`, `0.0`) and `balancing` (`not_recorded`, `0.0`).
- **Scores for `ser-1007`**:
  - $\text{Score}_{\text{req}}(\text{ser-1007}) = \frac{8 \times 1.0 + 2 \times 0.0}{10} = \mathbf{0.80}$ (**80.0%**)
  - $\text{Score}_{\text{rec}}(\text{ser-1007}) = \frac{8 \times 1.0}{8} = \mathbf{1.00}$ (**100.0%**)

### Serial `ser-1008` (`R-100-0008`)
- **Recorded steps (`1`)**: `stp-1806` (`cleaning`, graded `reported`), which deliberately has **no** `evidenced_by` link (flagged by synthetic `CriticalItem` `cri-1003` with `missing_evidence: true`).
- **Effective status of `cleaning` on `ser-1008`**: `missing` (`gap_kind = "un_evidenced_step"`, weight `0.0`).
- **Scores for `ser-1008`**:
  - $\text{Score}_{\text{req}}(\text{ser-1008}) = \frac{0.0}{10} = \mathbf{0.00}$ (**0.0%**)
  - $\text{Score}_{\text{rec}}(\text{ser-1008}) = \frac{0.0}{1} = \mathbf{0.00}$ (**0.0%**)

### Real Public Traces Comparison
- **`rocket-lab-archimedes.yaml`**:
  - `build` (`stp-arch-001` -> `evd-arch-001` SEC Form 10-K) is `confirmed` ($1.0$).
  - `machining` (`stp-arch-002` -> `evd-arch-001`) is `reported` ($0.5$).
  - `inspection` (`stp-arch-003`) is recorded without an `EvidenceRecord` (`missing (un-evidenced step)`, $0.0$).
  - $\text{Score}_{\text{req}} = \frac{1.0 + 0.5}{10} = \mathbf{0.15}$ (**15.0%**); $\text{Score}_{\text{rec}} = \frac{1.5}{3} = \mathbf{0.50}$ (**50.0%**).
- **`relativity-terran-r.yaml`**:
  - `assembly` (`stp-rel-001`, `stp-rel-002` -> `evd-rel-001`, `evd-rel-002`) is `reported` ($0.5$).
  - `inspection` (`stp-rel-003`) is recorded without an `EvidenceRecord` (`missing (un-evidenced step)`, $0.0$).
  - $\text{Score}_{\text{req}} = \frac{0.5}{10} = \mathbf{0.05}$ (**5.0%**); $\text{Score}_{\text{rec}} = \frac{2 \times 0.5}{3} = \mathbf{0.3333}$ (**33.3%**).

---

## 5. Regenerating the Gap Atlas

Run `tools/coverage.py` from the repository root:

```bash
# Human-readable coverage summary for all traces
python3 tools/coverage.py

# Machine-readable JSON output
python3 tools/coverage.py --json

# Regenerate docs/gap-atlas.md in one command
python3 tools/coverage.py --write-atlas
```
