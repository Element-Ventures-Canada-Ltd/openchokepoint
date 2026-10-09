Handling: Unclassified — public

# OpenChokepoint Python SDK (preview)

A small, read-only Python client for OpenChokepoint instance files. Use it to load a
registry, walk the graph, and validate files with the same rules CI applies.

## What it does

| Function | Purpose |
|---|---|
| `Registry.load(path)` | Load an instance file (objects and links) |
| `reg.of_type("Entity")`, `reg.get(id)` | Look records up by type or id |
| `reg.links_from(id, type)`, `reg.targets(id, type)` | Walk the graph |
| `reg.steps_for(serial_id)` | Process steps for one physical piece; ordered only when the file gives the order |
| `reg.steps_without_evidence()` | Steps with no evidence record: a gap shown, never filled |
| `validate(path, tier="public")` | Run `tools/validate.py` and get structured issues with rule IDs |

## What it does not do

- It does not write, score, rank or judge any record, organization or part.
- It does not infer an order of steps the file does not state.
- It does not hold a second copy of the rules. Validation always runs the project's own
  `tools/validate.py`, so the SDK and CI cannot disagree.

## Use it

From a checkout of this repository:

```bash
pip install pyyaml
cd sdk/python
python3 -c "
from openchokepoint import Registry, validate
reg = Registry.load('../../examples/synthetic-turbopump-thread.yaml')
print(len(reg), 'records; all synthetic:', reg.is_synthetic)
print(validate('../../examples/synthetic-turbopump-thread.yaml') or 'valid')
"
```

Or install it into your environment with `pip install ./sdk/python`. The SDK finds the
schema and validator by looking above its own folder; outside a checkout, set
`OPENCHOKEPOINT_ROOT` to the repository folder.

For a worked application, see [`apps/chokepoint-explorer`](../../apps/chokepoint-explorer/README.md).

## Status

Preview, version 0.1.0. The interface may change before schema 1.0. Not yet published to a
package index. Further language SDKs follow the JSON Schema export
(`schema/openchokepoint.schema.json`) once contributors ask for them.

Code under Apache-2.0. Documentation under OGL-Canada-2.0 (see LICENSING.md).
