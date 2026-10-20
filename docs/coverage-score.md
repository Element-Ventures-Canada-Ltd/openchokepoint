Handling: Unclassified — public

# The coverage score, in plain language

A digital thread is only as useful as the part of it the public can read. This note
defines the number `tools/coverage.py` reports, so that two traces can be compared
and a gap can be cited instead of argued about.

The score measures **the public record**, never a supplier, a programme, or a part's
quality. A trace that scores low may point at a perfectly good part whose paperwork
is held under agreement. That is the finding, not a defect in the part.

## 1. What counts as required

A **flight-critical rotating part** has to show six things before its public record
can be called complete. Each maps onto a `ProcessStep.step_kind` that the schema
already defines, so nothing new is invented here:

| Required `step_kind` | Why the public record needs it |
| :-- | :-- |
| `build` | The part exists; there is a build record behind the serial. |
| `heat_treatment` | Properties were set by a controlled thermal process, not assumed. |
| `machining` | Final geometry came from a controlled operation. |
| `cleaning` | Cleanliness was controlled, which is what a downstream certificate attests. |
| `inspection` | A dimensional or non-destructive check was recorded. |
| `balancing` | The part rotates: imbalance is its own failure mode, so it gets its own step. |

The other four kinds in the schema — `stress_relief`, `hip`, `finishing`, `assembly` —
are **optional**. Many parts have them, many do not: whether a part is HIP'd is a
design choice, and assembly belongs to the parent item. A trace is not penalised for
omitting them, and a trace does not earn extra credit for including them. This keeps
the denominator constant, which is the whole point of a comparable number.

The set is a constant in `tools/coverage.py` (`REQUIRED_STEP_KINDS`) so a reader can
diff the policy against this table. Changing it changes every score; treat it as a
policy change, not a bug fix.

## 2. How each step is graded

For one required kind, the tool looks at the steps of that kind that the serial item
`underwent`, and at the `EvidenceRecord`s each step `evidenced_by`. The best of them
decides the grade:

| Grade | Condition | Weight |
| :-- | :-- | --: |
| `confirmed` | A step of this kind has at least one record graded `confirmed`. | 1.0 |
| `reported` | Records exist, but the strongest is graded `reported` (or weaker). | 0.5 |
| `missing` | No record is attached, **or** no step of this kind appears at all. | 0.0 |

`reported` is worth half because the record is named but nobody has checked it. The
distinction the schema already makes — a pointer is not proof of acceptance — is the
reason the weights are not equal.

Two consequences are deliberate:

- A step that happened but carries no record is `missing`, and the report says the
  step was **present, unevidenced**. That is a different failure from a step that
  never appears, and the JSON keeps them apart (`strength` vs `present`).
- Absent and unevidenced both score zero. Neither can be recovered by inference: the
  schema's public tier forbids inferring real records (rule DT-002), and so does this
  score.

## 3. The score

```
coverage = (sum of the six weights) / 6
```

Always out of six, so `coverage` is comparable across traces. A second number is
reported alongside it and is **not** comparable across traces:

```
recorded_coverage = (sum of the weights of the kinds present) / (kinds present)
```

`recorded_coverage` answers a narrower question — "of the steps this trace shows, how
many are backed by evidence?" — and it is reported because a short trace should not be
confused with a sloppy one. A trace with one confirmed step scores `1.0` here and
`1/6` on the comparable number. Both are true; they answer different questions.

## 4. Worked example: `examples/synthetic-turbopump-thread.yaml`

The example holds two serial items, and they fail differently — which is the reason
the tool reports per serial rather than per file.

**`R-100-0007` — coverage 83.3%, recorded coverage 100%.**
It records eight steps (`build`, `stress_relief`, `hip`, `heat_treatment`, `machining`,
`cleaning`, `inspection`, `assembly`), and every one of them hangs an evidence record
off an `evidenced_by` link. Five of the six required kinds are `confirmed`. The sixth,
`balancing`, does not appear at all — the example calls itself end to end, and by this
policy it is not: a rotor with no balancing step has a hole in its public record. The
score is `5/6 = 83.3%`, and the gap atlas names `balancing` as the gap.

This is the tool doing its job on the repository's own example. If balancing is not
meant to be required for this part, that is an argument to change the policy constant,
not to soften the arithmetic.

**`R-100-0008` — coverage 0%, recorded coverage 0%.**
It shows exactly one step, `cleaning`, deliberately without an evidence record. So the
kind is present and unevidenced: `missing`, not absent. The other five kinds never
appear. `0/6 = 0%`. The example's comment says the gap "is shown, not filled", and this
is that gap as a number.

## 5. What the score does not claim

- It does not rank suppliers, programmes, or jurisdictions, and it never attaches to a
  real organisation. Every record it reads is synthetic in the public tier.
- It does not check that a record is genuine. It records that a pointer exists, at the
  grade the trace declares; establishing that a certificate is real is a separate act.
- It does not weight by criticality beyond the six-step policy. A `CriticalItem` flag
  can say which step a programme cares about; the score stays deliberately naive so
  that two traces remain comparable.

## 6. Reproducing it

```bash
python3 tools/coverage.py                              # score every trace, plain text
python3 tools/coverage.py --json                        # same, machine-readable
python3 tools/coverage.py --write-gap-atlas             # regenerate docs/gap-atlas.md
python3 tools/coverage.py --check-gap-atlas             # non-zero if the atlas is stale
python3 -m unittest tests.test_coverage -v              # the tests behind these numbers
```

The tool reads YAML only, writes nothing but the atlas, and calls no network. Same
file in, same numbers out: the gap atlas is checked in and `--check-gap-atlas` fails
the build if it drifts from the traces.
