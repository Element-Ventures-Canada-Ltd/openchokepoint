Handling: Unclassified — public

# Sovereign Space Supply Chain: a country-agnostic reference map

A reference map of **role archetypes** for a space supply chain, from upstream materials to downstream services. It is written in the OpenChokepoint grammar so that any registry can reuse the same roles, dependencies and risk placement and compare like with like.

**This is mapping only.** It records which kinds of supplier a space capability depends on, how concentrated each kind is, which export-control regime family applies, and what evidence stands behind each statement. It holds no design, process, test or performance data ([CONTRIBUTION-SCOPE.md](../../../CONTRIBUTION-SCOPE.md)). It names no company, programme or country.

## Files

| File | Content |
|---|---|
| `../../../examples/synthetic-space-supply-chain-archetypes.yaml` | The map as a graph in the repository's own grammar: 117 `Entity` archetypes and 354 `supplies` links. Validated in CI. `synthetic: true` throughout |
| `archetypes.yaml` | The attributes of each archetype (below) |
| `dependency-edges.yaml` | The 354 dependency edges (feeds → consumer) and the 14 edge families |
| `annex-b-risk-categories.yaml` | The 13 risk categories used for placement |
| `generic-chokepoints.yaml` | Ten generic chokepoints with their evidence notes |

## Archetype fields

| Field | Meaning |
|---|---|
| `id`, `group` | Stable id (`U` upstream inputs, `C` components and subsystems, `S` spacecraft integration, `A` assembly, integration and test, `L` launch, `TP` turbopump sub-chain, `O` in-space, `G` ground segment, `D` downstream, `E` horizontal enablers) |
| `tier` | `4` raw and processed inputs, `3` specialist process, `2` component or subsystem, `1` integrator, facility or service, `E` enabler |
| `suppliers_worldwide_band` | Indicative count band of qualified suppliers worldwide (for example `≤3`, `4–10`, `11–30`, `>30`) |
| `export_regime` | The regime family that governs trade in the item, named by category only |
| `exposure` | Indicative concentration and control exposure: Low, Medium, High, Extreme |
| `hs_2022` | Harmonized System 2022 subheadings where the archetype is a traded good; `n/a (service)` for services, facilities and enablers |
| `risk_note` | One-line reason the archetype matters |
| `evidence_grade` | `C` confirmed, `R` reported, `I` inferred, `S` speculative (see below) |
| `annex_b_primary`, `annex_b_secondary` | Placement in the 13 risk categories |

## Evidence grades

Grades follow the repository's four-way grading, shortened to one letter in the attribute files.

| Letter | Repository grade | Reading |
|---|---|---|
| C | `confirmed` | Stated by a primary public source |
| R | `reported` | Reported by a credible public source |
| I | `inferred` | Analyst inference from public structure |
| S | `speculative` | Plausible, no direct evidence |

A mixed grade such as `R/I` keeps both letters in `archetypes.yaml` and `generic-chokepoints.yaml`. In the example graph the `evidence_grade` field takes the **weaker** grade, and every dependency edge is graded `inferred`.

## Caveats

- **Bands are indicative.** Supplier-count bands and exposure ratings are ordinal bands set from public reporting and analyst judgment. They are not measurements, and they change.
- **Archetypes are not organizations.** The example graph uses the `Entity` type with `synthetic: true` for every archetype. Jurisdiction `XX` (the ISO 3166 user-assigned code) means any or unspecified, so jurisdiction of control is deliberately left open: a registry that instantiates an archetype records the real incorporation and controlling jurisdictions.
- **Entity kind is nominal.** `entity_kind` on an archetype that is a regime, authority or market function (for example export controls or launch licensing) is `government`, `academic` or `company` by closest fit.
- **Chokepoint notes cite publications by name.** Figures in `generic-chokepoints.yaml` are as reported in the named public publication. Source URLs are to be added before any chokepoint is promoted to a graded record under `data/`.
- **Regimes are named, not summarised.** Export-control references identify the regime family only. They are not legal advice and do not state what is or is not controlled.

## Risk categories

The 13 categories follow Annex B of the publicly released Defence Supply Chain Control Tower request for information on CanadaBuys. Each archetype has one or two primary placements and up to three secondary placements.

## Validate

```bash
pip install pyyaml
python3 tools/validate.py examples/synthetic-space-supply-chain-archetypes.yaml
python3 -m unittest discover -s tests -p test_reference_map.py
```

---
Element Ventures (Canada) Ltd. · © 2026 T. Leroy Smith. Exclusively licensed to Element Ventures (Canada) Ltd.
Indicative bands only; not legal, procurement or investment advice.
