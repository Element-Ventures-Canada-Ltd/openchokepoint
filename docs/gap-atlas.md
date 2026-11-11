Handling: Unclassified — public

# Public-Evidence Gap Atlas

This gap atlas is generated offline by `python3 tools/coverage.py --write-atlas` across all
digital-thread traces in `data/digital-thread/` and the reference synthetic thread in
`examples/synthetic-turbopump-thread.yaml`. See [`docs/coverage-score.md`](coverage-score.md)
for the scoring methodology, step-kind baseline, and evidence-grade weights.

## Trace Summary

| Trace | Tier / Kind | Serial Items | Confirmed Step Kinds | Reported Step Kinds | Missing Step Kinds | Required-Step Score | Recorded-Step Coverage |
|---|---|---:|---:|---:|---:|---:|---:|
| `data/digital-thread/relativity-terran-r/relativity-terran-r.yaml` | public real trace | 1 | 0/10 | 1/10 | 9/10 | **5.0%** (0.05) | 33.3% (0.33) |
| `data/digital-thread/rocket-lab-archimedes/rocket-lab-archimedes.yaml` | public real trace | 1 | 1/10 | 1/10 | 8/10 | **15.0%** (0.15) | 50.0% (0.50) |
| `examples/synthetic-turbopump-thread.yaml` | synthetic example | 2 | 8/10 | 0/10 | 2/10 | **80.0%** (0.80) | 88.9% (0.89) |

## Step-Kind Coverage Matrix (All Traces)

Each cell reports the strongest public evidence grade backing that `ProcessStep.step_kind`
(`confirmed` = 1.0, `reported` = 0.5, `missing` = 0.0). When a `ProcessStep` is recorded
in the trace without an `evidenced_by` link to an `EvidenceRecord`, the cell highlights
`missing (un-evidenced step)` to distinguish an explicit visibility gap from an unrecorded operation.

| Step Kind | `relativity-terran-r` | `rocket-lab-archimedes` | `synthetic-turbopump-thread` |
|---|---|---|---|
| `build` | missing | confirmed | confirmed |
| `stress_relief` | missing | missing | confirmed |
| `hip` | missing | missing | confirmed |
| `heat_treatment` | missing | missing | confirmed |
| `machining` | missing | reported | confirmed |
| `finishing` | missing | missing | missing |
| `cleaning` | missing | missing | confirmed |
| `inspection` | missing (un-evidenced step) | missing (un-evidenced step) | confirmed |
| `balancing` | missing | missing | missing |
| `assembly` | reported | missing | confirmed |
| **Required-Step Score** | **5.0%** (0.05) | **15.0%** (0.15) | **80.0%** (0.80) |

## Per-Serial Breakdown

| Trace | Serial ID | Serial | Component | Recorded Steps | Evidenced Steps | Confirmed | Reported | Missing | Required-Step Score | Recorded-Step Coverage |
|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|
| `relativity-terran-r` | `ser-terran-r-stage1-dev01` | `TR-S1-DEV01` | `cmp-terran-r-first-stage` | 3 | 2 | 0 | 1 | 9 | **5.0%** (0.05) | 33.3% (0.33) |
| `rocket-lab-archimedes` | `ser-archimedes-tp-dev01` | `ARCH-TP-DEV-01` | `cmp-archimedes-turbopump-housing` | 3 | 2 | 1 | 1 | 8 | **15.0%** (0.15) | 50.0% (0.50) |
| `synthetic-turbopump-thread` | `ser-1007` | `R-100-0007` | `cmp-1001` | 8 | 8 | 8 | 0 | 2 | **80.0%** (0.80) | 100.0% (1.00) |
| `synthetic-turbopump-thread` | `ser-1008` | `R-100-0008` | `cmp-1001` | 1 | 0 | 0 | 0 | 10 | **0.0%** (0.00) | 0.0% (0.00) |

## Explicit Visibility Gaps (`un_evidenced_step`)

Steps that are recorded on a `SerialItem` in the trace but have no `evidenced_by` link:

- **`data/digital-thread/relativity-terran-r/relativity-terran-r.yaml`** — `inspection` (`stp-rel-003`): step recorded without an `EvidenceRecord` (`missing`).
- **`data/digital-thread/rocket-lab-archimedes/rocket-lab-archimedes.yaml`** — `inspection` (`stp-arch-003`): step recorded without an `EvidenceRecord` (`missing`).
- **`examples/synthetic-turbopump-thread.yaml`** — no un-evidenced recorded step kinds at the trace level.
