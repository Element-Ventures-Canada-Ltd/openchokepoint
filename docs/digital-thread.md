Handling: Unclassified — public

# The digital thread, in plain language

A rocket turbopump is only as trustworthy as the paper trail behind each part. A good design is not enough. Someone has to show that this particular part was made from this particular material, treated, cleaned and inspected the way it must be. That trail is the **digital thread**. This page explains how OpenChokepoint (schema v0.2.0-draft) describes it, for readers who are not engineers.

The schema records **that** evidence exists and **where it sits**. It never holds the technical content: no drawings, geometry, process settings, test numbers or acceptance limits.

## The chain

Follow one part from raw material to assembly:

1. A **material lot** (`MaterialLot`: a batch of powder, wire, bar or billet) is the starting point.
2. The physical part (`SerialItem`) goes through ordered **process steps** (`ProcessStep`): build, stress relief, HIP, heat treatment, machining, finishing, cleaning, inspection, balancing, assembly.
3. Each step can point to an **evidence record** (`EvidenceRecord`): a material certificate, a build record, a cleaning certificate, an inspection report.
4. Some things are flagged as **critical items** (`CriticalItem`), because losing them would delay a programme.

| Link | Reads as |
|---|---|
| `instance_of` | this serial item is made to that design |
| `made_from` | this serial item came from that material lot |
| `produced_by` | that lot was produced by that organization |
| `underwent` (with `sequence`) | this serial item went through that step, in this order |
| `evidenced_by` | that step is backed by that evidence record |
| `performed_at` | that step happened at that site |
| `flags` | this critical item concerns that design, lot, capability or step |
| `alternate_for` | this organization or site is a qualified alternate for that critical item |

Three distinctions matter most. Each one stops a common misreading.

## 1. A design is not a part

A **component** is a design: a part number and a revision. Think of it as the recipe. A **serial item** is one physical piece made to that recipe, with its own serial number. Two serial items of the same component can have different histories: different material lots, different sites, different records.

Why it matters: a design can be perfectly sound while one physical piece has a gap in its record. The thread follows the piece, not the recipe.

## 2. A pointer is not proof of acceptance

An **evidence record** is a pointer. It says a record of a certain kind exists, who issued it, when, and where it can be found: a content fingerprint (`content_hash`, written `sha256:` followed by 64 hex characters) or a public citation (`citation`, an https link, plus `citation_section`). It does not contain the record, and it does not say the part passed.

Why it matters: "a cleaning certificate exists" and "the part was accepted" are different statements. The schema only makes the first. Whether the certificate shows the part met its limits is a question for the people holding the certificate.

## 3. A missing record is not an inferred fact

If a record cannot be found, the thread shows a step with **no evidence record**. It does not fill the gap with a guess, even a reasonable one. Real (non-fictional) thread records must be graded `confirmed` or `reported`; `inferred` is not accepted for them.

Why it matters: a gap is information. It tells a reader where to ask a question. A guess that looks like a fact hides the question.

## Critical items

A **critical item** flags something whose loss would delay a programme by more than 30 days. It carries simple markers: how big the delay would be (`delay_band`), whether there is only one source (`single_source`), whether a qualified alternate exists (`qualified_alternate`), and whether the flag is about a missing record (`missing_evidence`).

Critical-item judgments appear **only in fictional examples**. They are never recorded against a real organization or part, because a judgment about a real supplier is an assessment, not a public fact. The validator enforces this, including when a fictional flag is attached to something that is itself linked to a real organization.

## Three fictional examples

All three are in `examples/synthetic-turbopump-thread.yaml`. They use invented names and describe no real organization or part.

**Example A: single source.** The fictional *Rotor R-100, revision B* is made from powder lot *NF-0042*, produced by one fictional foundry, *Northfield Test Foundry*. No other source is listed. The critical item is marked single-source with no alternate. A reader learns: if this foundry stops, the programme stops.

**Example B: qualified alternate.** The fictional *Seal housing S-20* is finished at *Harbour Finishing Works*. *Lakeside Surface Co* is linked as a qualified alternate. A reader learns: there is a second route, and where it is.

**Example C: missing evidence.** Fictional serial item *R-100-0008* has a cleaning step with no evidence record. The thread shows the gap and stops there. A reader learns: ask for the cleaning certificate. The thread does not claim the cleaning was done or not done.

The same file traces fictional serial *R-100-0007* end to end: material lot, build, stress relief, HIP, heat treatment, machining, cleaning, inspection and assembly, with an evidence record for every step.

## How to read a thread

Ask five questions, in order:

1. Which physical piece is this, and which design is it made to?
2. Which material lot did it come from?
3. Which steps did it go through, and in what order?
4. For each step, does an evidence record exist, and where is it?
5. Where is the thread thin: a single source, no alternate, or a missing record?

The answers to questions 4 and 5 tell you where to ask for more. They do not tell you whether the part is good. That judgment belongs to the people who hold the underlying records.

## Validator rules

Each error starts with a rule ID you can cite in a review.

| ID | Rule |
|---|---|
| EV-001 | An evidence record carries a content hash or a public citation |
| EV-002 | No inline content; the hash is `sha256:` plus 64 hex; text fields stay short |
| EV-003 | A citation is a public https link |
| EV-004 | A real evidence record cites a publicly released report |
| CI-001 | A critical item is fictional (`synthetic: true`) |
| CI-002 | A critical item never flags, or takes an alternate from, a real record |
| CI-003 | A critical item never reaches a real record through what it flags |
| CI-004 | Critical-item markers match the graph (alternate linked; missing evidence really missing) |
| DT-001 | Step order is unique for each serial item |
| DT-002 | Real thread records are graded confirmed or reported |

## What this is not

- Not a design repository. It holds no geometry and no drawings.
- Not a quality verdict. A pointer to an inspection report is not a pass.
- Not a ranking of suppliers. Judgments are shown only on fictional examples.

## Where to look

- Schema: `schema/openchokepoint.yaml`
- Fictional examples: `examples/`
- Validator and its tests: `tools/validate.py`, `tests/`
- Real public-report traces, when contributed: `data/digital-thread/`, each with a `provenance.yaml` (see `DATA-CONTRIBUTIONS.md` and issue [#3](https://github.com/Element-Ventures-Canada-Ltd/openchokepoint/issues/3))
