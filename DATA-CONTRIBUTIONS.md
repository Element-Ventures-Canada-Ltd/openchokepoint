Handling: Unclassified — public

# Data and Model Contributions

Requirements for any contribution of data, datasets, model weights, fine-tunes,
or evaluation sets to the open tier. These sit alongside CLA.md and HANDLING.md.

## Rules

1. **Synthetic or public only.** Data must be synthetic, or public and licensed
   for redistribution and model training. No real entity-level data from
   non-public sources.
2. **No personal information** unless fully de-identified and permitted by the
   source licence.
3. **No export-controlled technical data**, and nothing marked above
   "Unclassified — public".
4. **Right to train.** You must have the right to let EV use the data to train,
   evaluate, and distribute models, including commercially.
5. **Provenance manifest required.** Every data or model contribution includes
   a `provenance.yaml` in the same folder, completed as below.

## provenance.yaml template

```yaml
handling: "Unclassified — public"
contribution: ""          # short name
type: ""                  # dataset | weights | fine-tune | eval-set
sources:
  - description: ""
    url: ""
    licence: ""           # SPDX id or licence name
    retrieved: ""         # YYYY-MM-DD
synthetic: false          # true if generated
personal_information: none   # none | de-identified (explain in notes)
export_controlled: false
training_rights_confirmed: false
base_model: ""            # for weights / fine-tunes
notes: ""
```

Contributions without a complete manifest will not be merged.
