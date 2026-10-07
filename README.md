Handling: Unclassified — public

# OpenChokepoint (working name)

An open grammar for mapping supply-chain dependencies: who supplies what, from where, under whose jurisdiction, and on what evidence. It gives analysts, researchers and industry one shared way to record chokepoints so registries can be compared, validated and combined.

> **Status:** private preview. The project name is a placeholder pending a name-availability check.

## What is here

| Path | Content |
|---|---|
| `schema/openchokepoint.yaml` | Object and link types: Entity, Facility, Capability, Programme; located_at, provides_capability, requires_capability, supplies |
| `tools/validate.py` | Validator for instance files |
| `examples/synthetic-example.yaml` | A fully fictional worked example (space turbopump supply chain) |

```bash
pip install pyyaml
python3 tools/validate.py examples/synthetic-example.yaml
```

## Design rules

- **Jurisdiction of control, not residency.** Every entity records where it is incorporated and who controls it.
- **Evidence on every record.** Each object and link carries an evidence grade, sources and an as-of date.
- **Announced is not operational.** Lifecycle keeps the two apart.
- **Synthetic only, for now.** External data contributions open after review; until then the validator rejects any non-synthetic record.

## Contributing

Read [PROGRAM.md](PROGRAM.md) for the programme and first use case, [CONTRIBUTING.md](CONTRIBUTING.md) for how to contribute, and [BOUNTIES.md](BOUNTIES.md) for paid issues. Contributors sign the CLA once, through the CLA bot on their first pull request.

## Licences

Code under Apache-2.0; documentation and data under the Open Government Licence – Canada 2.0. See [LICENSING.md](LICENSING.md).

---
Element Ventures (Canada) Ltd. · © 2026 T. Leroy Smith. Exclusively licensed to Element Ventures (Canada) Ltd.
