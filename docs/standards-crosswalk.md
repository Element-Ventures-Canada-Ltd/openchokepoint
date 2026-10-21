Handling: Unclassified — public

# Standards crosswalk: OpenChokepoint v0.2.1 ↔ PROV-O, QIF, STEP AP242

This page maps every OpenChokepoint v0.2.1 object type and link type onto the
closest concept in three established standards:

| Standard | Reference | What it covers here |
|---|---|---|
| W3C PROV-O | W3C PROV-O (https://www.w3.org/TR/prov-o/), § 1–6 | provenance, activities, derivation |
| QIF | ISO 23952:2020, Quality Information Framework, § 4–10 | inspection and quality evidence |
| STEP AP242 | ISO 10303-242:2020, Managed model-based 3D engineering, § 4–12 | part identity and revision |

The OpenChokepoint schema is a grammar for supply-chain dependency registries:
it records **that** evidence exists and **where** it sits, never the technical
content. The crosswalk keeps that posture: we map the *kinds* of records, not
any measured values. Where a standard expresses something the schema cannot
(or the reverse), the mapping is marked `partial` or `none` and the reason is
given. Section 6 collects those gaps and proposes changes **for discussion**;
no schema change is made in this slice.

Conventions:

- **exact** — the OpenChokepoint concept coincides with the standard concept in
  meaning and in the facts it can carry.
- **partial** — the closest concept exists but carries extra or different
  meaning; the mapping loses or adds something.
- **none** — the standard has no counterpart; the concept is out of scope for
  that standard.

## 1. The schema in one view

OpenChokepoint v0.2.1 has ten object types (four from v0.1, six from v0.2) and
ten link types (four from v0.1, six from v0.2). The digital-thread types
(`Component`, `SerialItem`, `MaterialLot`, `ProcessStep`, `EvidenceRecord`,
`CriticalItem`) and their links are the focus of this crosswalk; the v0.1
supply-chain types are included for completeness because the thread hangs off
them (`performed_at` points to `Facility`, `produced_by` to `Entity`).

| Object type | Kind of fact |
|---|---|
| `Entity` | an organization holding a capability |
| `Facility` | a physical site where work is performed |
| `Capability` | something an entity or facility can do or supply |
| `Programme` | a demand-side programme that requires capabilities |
| `Component` | a part design: part number + revision |
| `SerialItem` | one physical instance of a Component |
| `MaterialLot` | a batch of feedstock |
| `ProcessStep` | one controlled operation on a SerialItem (kind only) |
| `EvidenceRecord` | a pointer to proof a step happened |
| `CriticalItem` | a judgment flag (synthetic only) |

| Link type | Reads as |
|---|---|
| `located_at` | Entity located at Facility |
| `provides_capability` | Entity/Facility provides Capability |
| `requires_capability` | Programme requires Capability |
| `supplies` | Entity supplies Entity |
| `instance_of` | SerialItem made to Component design |
| `made_from` | SerialItem came from MaterialLot |
| `produced_by` | MaterialLot produced by Entity |
| `underwent` | SerialItem went through ProcessStep (ordered by `sequence`) |
| `evidenced_by` | ProcessStep backed by EvidenceRecord |
| `performed_at` | ProcessStep happened at Facility |
| `flags` | CriticalItem concerns a design, lot, capability or step |
| `alternate_for` | Entity/Facility is a qualified alternate for a CriticalItem |

## 2. Object types

### 2.1 `Component` — part design, identified by part number and revision

| Standard | Mapping | Rating | Reason |
|---|---|---|---|
| PROV-O | `prov:Entity` | partial | A design is an entity, but PROV-O has no notion of a *kind* with an identifier scheme such as part number + revision; a design is one entity, its physical instances are specializations (§ 5.2.4, `prov:specializationOf`). |
| QIF (ISO 23952) | Part / PartDefinition | partial | QIF models parts as a `Part` with a part definition that carries identifier and versioning (§ 6: Part Model). Revision handling exists but is a version attribute, not a distinct concept with rules; OpenChokepoint treats revision as part of the identity. |
| STEP AP242 (ISO 10303-242) | `product` + `product_definition_formation` | exact | AP242 identifies a product design by part number (`product`) and tracks revision through `product_definition_formation` (§ 7.2, § 9). This is the closest match in the set: part identity and revision are first-class. |

### 2.2 `SerialItem` — one physical instance of a Component

| Standard | Mapping | Rating | Reason |
|---|---|---|---|
| PROV-O | `prov:Entity`, linked to the Component entity with `prov:specializationOf` | exact | PROV-O's specialization is precisely "an entity that is a more specific version/instance of another" (§ 5.2.4). |
| QIF (ISO 23952) | `Part` with serial/instance identity | partial | QIF tracks parts; individual item identity by serial is used in results but the framework's core identity model is the part design, not the serialized unit. |
| STEP AP242 (ISO 10303-242) | `product` with a serialized occurrence / `ProductOccurrence` | partial | AP242 models occurrences in assemblies; a standalone serialized item is expressible but not a dedicated concept the way `SerialItem` is. |

### 2.3 `MaterialLot` — a batch of feedstock

| Standard | Mapping | Rating | Reason |
|---|---|---|---|
| PROV-O | `prov:Entity` | exact | A lot is a well-defined entity with its own identifier. |
| QIF (ISO 23952) | Material/resource context in the plan/results model | partial | QIF records what material was used in an operation (§ 9 results) but has no first-class "lot" identity; it is contextual. |
| STEP AP242 (ISO 10303-242) | Product as material / `product` referencing a material definition | partial | Material is a product type in AP242; a *batch* with a lot number is not a distinct concept (version formation applies to designs, not batches). |

### 2.4 `ProcessStep` — one controlled operation, kind only

| Standard | Mapping | Rating | Reason |
|---|---|---|---|
| PROV-O | `prov:Activity` | exact | An operation is an activity: something that happens over time (§ 2.2, § 5.2.2). OpenChokepoint's "kind only, never parameters" is exactly PROV's abstention from the activity's detail. |
| QIF (ISO 23952) | `Plan` / operation within a plan | partial | QIF plans operations in detail (sequence, parameters, characteristics) (§ 7: Plan Model). The schema's kind-only posture maps to a plan step but QIF expects far more. |
| STEP AP242 (ISO 10303-242) | `process_property_association` / `action` | partial | AP242 models actions on products (manufacturing operations) (§ 11) but with far more structure than the schema needs. |

### 2.5 `EvidenceRecord` — a pointer to proof (hash or citation)

| Standard | Mapping | Rating | Reason |
|---|---|---|---|
| PROV-O | `prov:Entity` + `prov:wasGeneratedBy` the step | exact | PROV-O models the record as an entity generated by an activity, and provenance itself is the standard's subject (§ 4.2, § 5.2.4). The pointer-only posture matches PROV: the entity is the record's existence, not its content. |
| QIF (ISO 23952) | `Results` model entries (inspection result, certificate linkage) | partial | QIF results are *themselves* the quality evidence (§ 10: Results Model) rather than pointers to evidence held elsewhere. |
| STEP AP242 (ISO 10303-242) | `requirement`/`certification` associations | none | AP242 carries certification and requirements on products but has no general "evidence record" pointer concept; it is design-centric. |

### 2.6 `CriticalItem` — a judgment flag, synthetic only

| Standard | Mapping | Rating | Reason |
|---|---|---|---|
| PROV-O | `prov:Entity` (a statement-bearing entity) | partial | PROV-O can carry any entity; a flag is an entity. But PROV-O has no notion of judgment/risk and is deliberately neutral about assessments. |
| QIF (ISO 23952) | `Characteristic` with status/limit evaluation | none | QIF evaluates characteristics against limits; a *programme-level risk flag* (single source, delay band) is outside its scope. |
| STEP AP242 (ISO 10303-242) | `requirement_fulfillment` / part criticality attributes | none | AP242 identifies critical characteristics of a design in some profiles but not a supply-chain risk judgment. |

### 2.7 v0.1 types (for completeness)

| Type | PROV-O | QIF | STEP AP242 |
|---|---|---|---|
| `Entity` (organization) | `prov:Agent` — exact | n/a (organizations as parties) — partial | n/a (supplier data outside core scope) — none |
| `Facility` | `prov:Location` — exact | resource in plans — partial | n/a — none |
| `Capability` | `prov:Entity` (attributed to the provider) — partial | n/a — none | n/a — none |
| `Programme` | `prov:Agent` (demand owner) — partial | n/a — none | n/a — none |

## 3. Link types

### 3.1 `instance_of` — SerialItem → Component

| Standard | Mapping | Rating | Reason |
|---|---|---|---|
| PROV-O | `prov:specializationOf` | exact | A serial item is the canonical example of a specialization of its design entity (§ 5.2.4). |
| QIF (ISO 23952) | Part definition ↔ part instance relationship in plans/results | partial | QIF relates part definitions to actual parts but the relation is implicit in how plans bind to parts. |
| STEP AP242 (ISO 10303-242) | `product_definition_formation` ↔ occurrence / `product_definition` usage | partial | AP242 relates design formation to occurrences; the relation exists but is assembly-oriented. |

### 3.2 `made_from` — SerialItem → MaterialLot

| Standard | Mapping | Rating | Reason |
|---|---|---|---|
| PROV-O | `prov:wasDerivedFrom` | partial | The item is derived from the lot (transformation), which is what `wasDerivedFrom` expresses (§ 5.2.5). It is not exact because PROV's derivation is not restricted to material origin. |
| QIF (ISO 23952) | result → material resource usage | partial | QIF records which material resource was consumed but as an attribute of the operation result, not a lot-level relationship. |
| STEP AP242 (ISO 10303-242) | material association on product / process | partial | AP242 binds material to a product or process step; batch-level traceability is partial. |

### 3.3 `underwent` — SerialItem → ProcessStep (ordered by `sequence`)

| Standard | Mapping | Rating | Reason |
|---|---|---|---|
| PROV-O | `prov:used` (the step activity uses the item entity) | partial | The direction and activity semantics are right (activity uses entity, § 5.2.3). The *order* (`sequence`) is not expressible with the plain predicate; PROV-O's `prov:qualifiedUsage`/`prov:qualifiedAssociation` (§ 5.3) can carry ordering as a qualified annotation, but the plain export (see `tools/export_prov.py`) omits it to avoid inventing order. |
| QIF (ISO 23952) | Plan operation sequence | partial | QIF plans an explicit operation sequence (§ 7), which is *more* than the schema records in the public tier (order may be omitted for real records). |
| STEP AP242 (ISO 10303-242) | process action sequence | partial | AP242 can express process order but the schema's tiered rule (public: no order; private: ordered) has no direct counterpart. |

### 3.4 `evidenced_by` — ProcessStep → EvidenceRecord

| Standard | Mapping | Rating | Reason |
|---|---|---|---|
| PROV-O | `prov:wasGeneratedBy` (record entity generated by the step activity) | exact | This is the native PROV relation for "this entity is the outcome of that activity" (§ 4.2, § 5.2.4). |
| QIF (ISO 23952) | result ↔ characteristic/plan linkage | partial | QIF ties results to the plan and characteristics, not to a separate pointer record. |
| STEP AP242 (ISO 10303-242) | certification/validation association | none | AP242 links certificates to products, not operations to evidence pointers. |

### 3.5 `performed_at` — ProcessStep → Facility

| Standard | Mapping | Rating | Reason |
|---|---|---|---|
| PROV-O | `prov:atLocation` | exact | PROV-O's `atLocation` applies to activities and entities (§ 5.2.6, § 6.3). |
| QIF (ISO 23952) | resource/location in the plan | partial | QIF records the resource performing the operation; location is an attribute, not a typed link. |
| STEP AP242 (ISO 10303-242) | n/a | none | AP242 does not model execution locations. |

### 3.6 `flags` — CriticalItem → (Component, MaterialLot, Capability, ProcessStep)

| Standard | Mapping | Rating | Reason |
|---|---|---|---|
| PROV-O | none (export keeps the edge as `ocp:flags`) | none | PROV-O has no "concerns/flag" relation and is deliberately value-neutral; flagging is a judgment. |
| QIF (ISO 23952) | characteristic criticality / status | none | QIF evaluates measured characteristics, not supply-chain risk flags. |
| STEP AP242 (ISO 10303-242) | critical characteristic designation | none | AP242 can designate criticality of design characteristics; a programme delay-risk flag is outside its scope. |

### 3.7 `alternate_for` — Entity/Facility → CriticalItem

| Standard | Mapping | Rating | Reason |
|---|---|---|---|
| PROV-O | none (export keeps the edge as `ocp:alternateFor`) | none | No counterpart; the concept is a supply-chain resilience statement. |
| QIF (ISO 23952) | alternate resource in plans | partial | QIF plans can name alternate resources for an operation; the schema's alternate is for a *risk item*, not an operation. |
| STEP AP242 (ISO 10303-242) | n/a | none | Out of scope. |

### 3.8 v0.1 links (for completeness)

| Link | PROV-O | Rating | Note |
|---|---|---|---|
| `located_at` | `prov:atLocation` | exact | Entity at location. |
| `provides_capability` | capability `prov:wasAttributedTo` provider | partial | Attribution is the closest PROV relation; capability is not a standard PROV concept. |
| `requires_capability` | none (`ocp:requiresCapability` in export) | none | No PROV counterpart for demand. |
| `supplies` | none (`ocp:supplies` in export) | none | Supplier relations are out of PROV's scope. |
| `produced_by` | `prov:wasAttributedTo` | exact | The lot is attributed to the organization that produced it. |

## 4. Coverage check (acceptance)

Every v0.2.1 type and link appears above:

- **Types (6):** Component 2.1, SerialItem 2.2, MaterialLot 2.3, ProcessStep 2.4, EvidenceRecord 2.5, CriticalItem 2.6.
- **Links (6):** instance_of 3.1, made_from 3.2, underwent 3.3, evidenced_by 3.4, performed_at 3.5, flags 3.6, alternate_for 3.7 — plus v0.1 links in 3.8.

The PROV-O column drives `tools/export_prov.py`; QIF and STEP columns are
documentation-only and are not exported.

## 5. Why PROV-O is the export target

Of the three standards, only PROV-O is an RDF/OWL ontology that can be
serialized and parsed by a standard RDF parser, which is the acceptance test
for this slice. QIF and STEP AP242 are information models with their own
exchange formats (XML-based), not RDF vocabularies; mapping to them is
documented here for adoption and re-keying, and PROV-O is the machine-readable
bridge. `tools/export_prov.py` emits Turtle or JSON-LD, both parseable with a
standard RDF parser (verified in `tests/test_export_prov.py`).

## 6. Gaps and proposals (for discussion, no schema change)

1. **Order is not expressible in plain PROV.** `underwent.sequence` is real in
   the private tier but the plain export cannot carry it without qualified
   annotation. Proposal: in a future slice, emit ordered links as
   `prov:qualifiedUsage` with a `prov:atTime`/sequence annotation so order is
   preserved for private-tier exports.
2. **`flags` and `alternate_for` have no PROV counterpart.** Proposal: define a
   small OCP extension vocabulary (namespace already reserved in the exporter)
   for risk statements, and document it here if it is accepted.
3. **`CriticalItem` is a judgment.** Neither QIF nor STEP AP242 expresses
   programme-level risk; any future adoption should keep critical items out of
   real (non-synthetic) records, as the validator's CI-001–CI-004 rules
   already require.
4. **QIF/STEP mapping depth.** Both standards have richer process models than
   the schema needs. The mapping above stays at the level of *kind of concept*;
   a full element-by-element mapping would be a separate, much larger
   deliverable and is not needed for the acceptance test.
5. **STEP AP242 revision semantics.** `Component` (part number + revision)
   maps cleanly to AP242, which suggests that when the schema needs to express
   design lineage (revisions superseding each other), AP242's
   `product_definition_formation` could inform a future `supersedes` link.

## 7. Sources and citation discipline

- W3C PROV-O: https://www.w3.org/TR/prov-o/ — cited by section only above.
- ISO 23952:2020 (QIF) and ISO 10303-242:2020 (STEP AP242) are cited by
  clause number only. No standard text is copied into this repository; the
  mappings above are original descriptions of the relationship between the
  OpenChokepoint schema and those standards.
- All example records referenced here are the fictional examples in
  `examples/synthetic-turbopump-thread.yaml` and `examples/synthetic-example.yaml`.
