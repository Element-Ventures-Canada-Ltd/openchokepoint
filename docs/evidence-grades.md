Handling: Unclassified — public

# Evidence Grades

Every object and link in an OpenChokepoint instance file carries an `evidence_grade` property (`schema/openchokepoint.yaml`). The grade records the strength of the public, verifiable source material supporting the claim—never technical performance or engineering acceptance.

All worked examples below are strictly synthetic (`synthetic: true`), use fictional entities on the reserved `example.org` domain, and pass `python3 tools/validate.py` when saved as standalone YAML files.

---

## 1. `confirmed`

Use `confirmed` when a primary, authoritative public record directly states the fact—such as an official corporate registry filing, a published government contract award, or a formal disclosure by the organization itself.

```yaml
# Handling: Unclassified — public
objects:
  - type: Entity
    id: ent-grade-confirmed
    name: "Example Orbital Forge Ltd."
    entity_kind: company
    incorporation_jurisdiction: CA
    controlling_jurisdiction: CA
    evidence_grade: confirmed
    sources:
      - "https://example.org/synthetic/corporate-registry/ent-grade-confirmed"
    as_of: 2026-10-01
    lifecycle: active
    synthetic: true
links: []
```

---

## 2. `reported`

Use `reported` when the claim is documented by credible secondary reporting—such as an independent trade publication, an industry journalism piece, or a third-party conference presentation—where primary registry or contract documents are not yet published.

```yaml
# Handling: Unclassified — public
objects:
  - type: Entity
    id: ent-grade-reported
    name: "Example Cryogenic Valves GmbH"
    entity_kind: company
    incorporation_jurisdiction: DE
    controlling_jurisdiction: DE
    evidence_grade: reported
    sources:
      - "https://example.org/synthetic/trade-press/ent-grade-reported"
    as_of: 2026-10-01
    lifecycle: active
    synthetic: true
links: []
```

---

## 3. `inferred`

Use `inferred` when the record is deduced from indirect public indicators—such as regional job postings, environmental permit applications, or shipping manifest metadata—that strongly point to the relationship or site activity without naming it explicitly in a primary announcement.

```yaml
# Handling: Unclassified — public
objects:
  - type: Facility
    id: fac-grade-inferred
    name: "Example Northern Acceptance Stand"
    facility_kind: test
    host_jurisdiction: SE
    evidence_grade: inferred
    sources:
      - "https://example.org/synthetic/municipal-permit/fac-grade-inferred"
    as_of: 2026-10-01
    lifecycle: active
    synthetic: true
links: []
```

---

## 4. `speculative`

Use `speculative` when early or uncorroborated public signals suggest a potential capability, programme, or supplier link—such as preliminary exploratory memoranda or unverified analyst commentary—that warrants tracking before firmer evidence is available.

```yaml
# Handling: Unclassified — public
objects:
  - type: Capability
    id: cap-grade-speculative
    name: "Example turbopump assembly qualification"
    evidence_grade: speculative
    sources:
      - "https://example.org/synthetic/analyst-note/cap-grade-speculative"
    as_of: 2026-10-01
    lifecycle: announced
    synthetic: true
links: []
```

---

## 5. `no_evidence`

Use `no_evidence` to explicitly record an unsubstantiated placeholder or a known evidentiary gap in a synthetic model where a claim has been surfaced for review but no supporting evidence confirms it yet.

```yaml
# Handling: Unclassified — public
objects:
  - type: Programme
    id: prg-grade-no-evidence
    name: "Example Unverified Upper-Stage Programme"
    evidence_grade: no_evidence
    sources:
      - "https://example.org/synthetic/placeholder/prg-grade-no-evidence"
    as_of: 2026-10-01
    lifecycle: announced
    synthetic: true
links: []
```
