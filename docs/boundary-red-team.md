# Handling: Unclassified — public

# Boundary Red-Team Catalogue — sample (RT-001), Slice C of issue #18

Sample required by the issue's sample-before-full-work rule: five attack
cases and one new rule (RT-001). The full seven-category catalogue extends
this draft on a maintainer's nod.

Every value shown here and in the corpus is **fictional and invented** for
this catalogue only. No real technical values from any source were used,
per the slice rules. URLs use the reserved `example.org` domain.

## RT-001 — engineering-unit payloads in free-text fields

The validator's pre-existing content guards are a field-name blacklist
(EV-002), a string-length cap, and pointer-only evidence. None of them
looks at *what a short legitimate field says*. An identifier is a natural
place to hide a parameter:

| # | Field | Fictional payload | Expected |
| :-- | :-- | :-- | :-- |
| 1 | `Component.name` | `Inducer forging batch, min 325 MPa yield` | reject RT-001 |
| 2 | `MaterialLot.lot_number` | `LOT-2026-325MPa-HT` | reject RT-001 |
| 3 | `EvidenceRecord.issuer` | `Acme Test Labs, quench 60 °C` | reject RT-001 |
| 4 | `Component.part_number` | `PN-4421-TOL-0.02mm` | reject RT-001 |
| 5 | `SerialItem.serial` | `SN-001-range-(-54C-to-177C)` | reject RT-001 |

Negative controls (must stay accepted): plain identifiers
(`PN-2026-0007`, `LOT-88-0001`), alphanumeric material names without units
(`Inconel lot 718 supplier`), URLs whose query carries an id
(`https://example.org/report?id=889`), and section pointers
(`Section 7.3`). The unit regex requires a digit glued to a real unit
token, and the bare-letter temperature form (`54C`) is only flagged when
followed by punctuation, so phrases like `3 Company` never match.

False-positive rate measured on: existing `examples/` (2/2 accepted), the
full main test suite (51/51), and the negative fixtures (3/3): **0**.

Residual risks (open by design, listed per the issue's acceptance test):

1. **Prose descriptions without digits** — "typical yield strength for the
   17-4 PH condition" carries engineering meaning to a human and no unit
   token to a regex. No rule can catch this without reading; human review
   stays necessary.
2. **`sequence` ordinals** — an integer step order is syntactically
   indistinguishable from a smuggled parameter.
3. **Content hashes** — EV-001..004 correctly treat `content_hash` as a
   pointer; the validator cannot verify what the hash points to.
4. **Legitimate non-Latin names** — future look-alike rules (full slice)
   will surface Cyrillic supplier names in identifier fields for human
   review; a documented exemption path is intentional.
5. **Unlisted encodings** — this catalogue is a growing pattern library,
   not a completeness proof.

Maintenance: new evasion shape → new fixture in `tests/red-team/cases/`
with `expected: reject` and the rule id that must catch it; one negative
control per legitimate shape the rule could over-reach. AI-assistance
disclosure is recorded in the pull request description, per
CONTRIBUTING.md.
