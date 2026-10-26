# Boundary red-team: technical data past the validator

Handling: Unclassified — public

This document records the adversarial cases used to test the promise that the public repository never carries technical data. Every value below is invented.

## Attack catalogue

| Category | Example | Rule |
| --- | --- | --- |
| Number with an engineering unit | `Example pump 25 mm` | RT-001 |
| Tolerance | `Example pump ±0.5` | RT-002 |
| Numeric range | `Example pump 10–20 bar` | RT-002 |
| Split value | `Example pump 1 234` | RT-003 |
| Encoded value | `Example pump 0x1F` | RT-003 |
| Look-alike character | `Example pump 25 µm` | RT-001 / RT-004 |
| Value hidden in an identifier | `part_number: X-1-25mm` | RT-005 |

## Test corpus

`tests/red-team/cases.yaml` holds fictional records with an expected result. `tests/test_red_team.py` runs them in CI. A case is either rejected by a named rule or listed under residual risk.

## False positives

The rules are deliberately narrow. They scan free text and identifiers only, not URLs, hashes, dates or enum fields. The existing synthetic examples and traces contain no unit-bearing free text, so the measured false-positive rate on them is zero. A name such as `Example pump two stage` and an identifier such as `X-1` are accepted.

## Residual risk

These rules cannot catch everything, and human review stays necessary:

- A bare number with no unit (`Example pump 3`) is accepted.
- A unit outside the list (`Example pump 3 furlongs`) is accepted.
- A value split across two fields (`name: Example pump`, `item: 25`) is accepted.
- A value hidden in a URL path or query string is accepted.
- A value hidden in a citation section that looks like a label (`Section 3`) is accepted.
- A value encoded as words (`twenty-five`) is accepted.
- A look-alike character that is not in the list is accepted.
- A real technical value that happens to look like an identifier (`X-1`) is accepted.

Because the validator is a tripwire, not a parser, a reviewer must still read the free text and identifiers of any record that claims to be parameter-free.
