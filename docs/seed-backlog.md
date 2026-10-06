Handling: Unclassified — public

# Seed backlog (to file as issues at launch)

| # | Title | Track | Labels | Acceptance test |
|---|---|---|---|---|
| 1 | Add JSON Schema export for `openchokepoint.yaml` | Tooling | good first issue | `tools/export_jsonschema.py` emits a schema that validates the synthetic example |
| 2 | CSV → YAML converter for objects and links | Tooling | bounty | Round-trips the synthetic example without loss |
| 3 | Validator: report all errors with line numbers | Tooling | good first issue | Errors cite file and line |
| 4 | Unit tests for every validation rule | Tooling | bounty | Each rule has a passing and failing test |
| 5 | Extend the turbopump example: bearings and seals tier | Examples | good first issue | Validates; adds ≥5 synthetic entities |
| 6 | Extend the turbopump example: test and qualification facilities | Examples | — | Validates; uses `provides_capability` maturity |
| 7 | Propose `Component`, `Lot` and `MaterialClass` types | Schema | schema | Proposal issue approved by maintainers |
| 8 | Propose a `supplies` volume/criticality property | Schema | schema | Proposal approved; no monetary values |
| 9 | Document the evidence-grade rules with examples | Examples | good first issue | Doc page merged |
| 10 | Jurisdiction-of-control guide: worked cases | Examples | bounty | Three synthetic cases, reviewed |
| 11 | Graph export (GraphML) | Tooling | bounty | Opens in a standard graph tool |
| 12 | Pre-commit hook running the validator | Tooling | good first issue | Hook documented and tested |
