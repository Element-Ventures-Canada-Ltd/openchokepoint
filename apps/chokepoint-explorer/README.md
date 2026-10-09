Handling: Unclassified — public

# Chokepoint explorer (sample application)

A worked example of building on the [OpenChokepoint Python SDK](../../sdk/python/README.md).
It reads one instance file and writes a plain-language Markdown report.

## Run it

```bash
pip install pyyaml
python3 apps/chokepoint-explorer/explore.py examples/synthetic-turbopump-thread.yaml
python3 apps/chokepoint-explorer/explore.py data/registry/launch-chain.yaml --out report.md
```

## What the report shows

| Section | Question it answers |
|---|---|
| Jurisdiction of control | Where is each organization controlled from, and which are incorporated in one place but controlled from another? |
| Capabilities | Who does the file list against each capability, and which programmes require it? |
| Digital threads | For each physical piece: which design, which material lot, which steps, and is there an evidence record for each? |
| Evidence gaps | Which steps have no evidence record? |
| Declared critical items | Which judgments does the file declare? Synthetic records only. |

## Guardrails

- **Fails closed.** A file that does not pass `tools/validate.py` produces no report.
- **Facts, not assessments.** The explorer counts and lists what the file states. It never
  scores, ranks or labels a real organization or part. Critical-item judgments appear only
  as declared, and the validator allows them on fictional records only.
- **No inferred order.** Steps are numbered only when the file gives their order. Otherwise
  the report says the order is not published.
- **A pointer is not a pass.** An evidence record shows that a record exists and where it
  sits, not that a part was accepted.

## Build your own

Copy `explore.py` as a starting point. Load a file with `Registry.load`, check it with
`validate`, and keep the same guardrails.

## Good first contributions

Extend the synthetic turbopump example (the first use case in [PROGRAM.md](../../PROGRAM.md))
and show what this explorer reveals about it, or add a report section. Synthetic data and
supply-chain mapping only; see [CONTRIBUTION-SCOPE.md](../../CONTRIBUTION-SCOPE.md).
