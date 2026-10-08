Handling: Unclassified — public

# Contributing

1. **Sign once.** On your first pull request the CLA bot asks you to post a one-line signing statement; that covers all your later contributions ([CLA.md](CLA.md)). If you contribute for an organization, it signs [CCLA.md](CCLA.md) first and its contributors are allowlisted.
2. **Pick an issue.** Start with `good first issue`, or a `bounty` issue under [BOUNTIES.md](BOUNTIES.md) (a deferred ledger: see [LEDGER.md](LEDGER.md)). Comment to claim it before you start.
3. **Open a pull request** from a branch. CI runs the validator and the data-handling guard; the CLA bot checks your signature.

## Rules

- Real-world records are accepted only under `data/`, built from public, citable sources with a complete `provenance.yaml` ([DATA-CONTRIBUTIONS.md](DATA-CONTRIBUTIONS.md)). Everywhere else, synthetic data only.
- Every contribution passes the export-control screen in [EXPORT-CONTROL.md](EXPORT-CONTROL.md).
- No personal information, no confidential or export-controlled information, no third-party material you cannot license.
- Every new or changed file carries a `Handling:` marking.
- Schema changes start as a **schema proposal** issue and need maintainer approval before a pull request.
- Supply-chain mapping and schema work only; see [CONTRIBUTION-SCOPE.md](CONTRIBUTION-SCOPE.md).
- AI-assisted work needs a named Responsible Person who reviews it and signs the CLA (CLA.md section 11).
- Ideas and feedback that are not contributions follow [FEEDBACK.md](FEEDBACK.md); governance is in [GOVERNANCE.md](GOVERNANCE.md).

## Pre-publication notice for programme-funded work

Material produced under a government-funded programme engagement (for example SoW 4.21 deliverables) is not contributed to this repository directly. Maintainers publish it only after the funder's pre-publication notice period (15 business days for government-funded work, where the agreement applies it) and the deliverable owner's review. Community contributions are not affected.

## Sign-off

The one-time CLA signature covers every contribution. A per-commit `Signed-off-by` (DCO) trailer is welcome but not required.

Be kind and specific. See [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).
