Handling: Unclassified — public

# OpenChokepoint v0.2.1 Standards Crosswalk: W3C PROV-O, QIF (ISO 23952), and STEP AP242 (ISO 10303-242)

Part of #3 (Closes #19).

## 1. Purpose and Scope

Manufacturing organisations record provenance, quality evidence, and part configuration in established international standards:

- **W3C PROV-O** (*W3C Recommendation, PROV-O: The PROV Ontology, 30 April 2013*, Sections 2–3);
- **QIF 3.0 / ISO 23952:2020** (*Automation systems and integration — Quality Information Framework*, Clauses 5–10);
- **STEP AP242 / ISO 10303-242:2022** (*Industrial automation systems and integration — Product data representation and exchange — Part 242: Managed model-based 3D engineering*, Clauses 4–6).

This document maps every OpenChokepoint v0.2.1 digital-thread type and relationship link to its closest concept in each standard, classifies each mapping as `exact`, `partial`, or `none`, and documents schema gaps for future discussion without altering `schema/openchokepoint.yaml`.

---

## 2. Entity Type Crosswalk (OpenChokepoint v0.2.1)

| OpenChokepoint v0.2.1 Type | W3C PROV-O Concept | Match | QIF (ISO 23952:2020) Concept | Match | STEP AP242 (ISO 10303-242:2022) Concept | Match | Rationale & Section Citations |
|---|---|---|---|---|---|---|---|
| `Component` | `prov:Entity` (W3C PROV-O §2.1) | `partial` | `Part` / `ProductDefinition` (ISO 23952:2020 Clause 6.3 `QIFProduct`) | `exact` | `product` / `product_definition` (ISO 10303-242:2022 Clause 4.2.1) | `exact` | `Component` represents a catalog/design-level part definition. PROV-O treats both type-level designs and physical instances as `prov:Entity`, whereas QIF and STEP AP242 explicitly separate design-level `Part`/`product_definition` from physical serialised instances. |
| `SerialItem` | `prov:Entity` (W3C PROV-O §2.1) | `exact` | `ActualComponent` / `SerialNumber` (ISO 23952:2020 Clause 6.4) | `exact` | `product_as_individual` / `product_definition_formation` (ISO 10303-242:2022 Clause 4.2.4) | `exact` | `SerialItem` is a physical, serial-numbered instance of a `Component` (`ser-1007`), corresponding directly to STEP AP242 `product_as_individual` and QIF `ActualComponent`. |
| `MaterialLot` | `prov:Entity` (W3C PROV-O §2.1) | `exact` | `Material` / `BatchLot` qualifier (ISO 23952:2020 Clause 6.4.2) | `partial` | `material_designation` + `product_as_individual` batch/lot (ISO 10303-242:2022 Clause 4.2.5) | `partial` | `MaterialLot` captures feedstock heat/batch identity (`lot-718-a`, `lot-cu-c`) without disclosing proprietary alloy chemistry; QIF and STEP AP242 attach material specification properties that OpenChokepoint intentionally omits for export-control safety. |
| `ProcessStep` | `prov:Activity` (W3C PROV-O §2.1) | `exact` | `ActionMethod` / `ProcessStep` (ISO 23952:2020 Clause 7.2 `QIFPlans`) | `partial` | `process_operation` / `action_activity` (ISO 10303-242:2022 Clause 4.2.8) | `exact` | `ProcessStep` (`build`, `hip`, `machining`, `inspection`, etc.) is a time-bounded transformation (`prov:Activity`, STEP `action_activity`). QIF focuses primarily on measurement/inspection actions (`MeasureActionMethod`) rather than full thermal/forming steps. |
| `EvidenceRecord` | `prov:Entity` with `prov:Bundle` metadata (W3C PROV-O §2.1, §3.3) | `exact` | `MeasurementResults` / `QualityRecord` (ISO 23952:2020 Clause 9 `QIFResults`) | `partial` | `applied_document_reference` / `approval` (ISO 10303-242:2022 Clause 4.2.12) | `partial` | `EvidenceRecord` records public-source or certificate pointers (`ev-2001`) and an `evidence_grade` (`confirmed`, `reported`, `inferred`, `speculative`, `no_evidence`). QIF `QIFResults` embeds dimensional readings, whereas OpenChokepoint records only external provenance pointers. |
| `CriticalItem` | `prov:Entity` with domain constraint attributes (W3C PROV-O §3.1) | `none` | `CharacteristicNominal` criticality / severity classification (ISO 23952:2020 Clause 6.5) | `none` | `certification` / `security_classification` / `risk_perception` (ISO 10303-242:2022 Clause 4.2.15) | `partial` | `CriticalItem` captures supply-chain chokepoint metadata (lead-time band, qualification barrier, sole-source exposure). Neither W3C PROV-O nor QIF models supply-chain bottlenecks; STEP AP242 Risk & Configuration Management covers criticality only partially. |

---

## 3. Relationship Link Crosswalk (OpenChokepoint v0.2.1)

| OpenChokepoint v0.2.1 Link | Domain -> Range | W3C PROV-O Property | Match | QIF (ISO 23952:2020) Reference | Match | STEP AP242 (ISO 10303-242:2022) Entity | Match | Rationale & Section Citations |
|---|---|---|---|---|---|---|---|---|
| `instance_of` | `SerialItem -> Component` | `prov:specializationOf` (W3C PROV-O §3.2) | `exact` | `ActualComponent -> Part` (`PartId` reference, ISO 23952:2020 Clause 6.4) | `exact` | `product_design_to_individual` (ISO 10303-242:2022 Clause 4.2.4) | `exact` | Links a physical serialised item to its catalog part definition. |
| `made_from` | `SerialItem -> MaterialLot` (or child `SerialItem`) | `prov:wasDerivedFrom` (W3C PROV-O §2.1) | `exact` | `ActualComponent` traceability to `Material` lot (ISO 23952:2020 Clause 6.4.2) | `partial` | `make_from_usage_option` / `next_assembly_usage_occurrence` (ISO 10303-242:2022 Clause 4.2.6) | `exact` | Captures raw-material lot lineage and sub-tier assembly genealogy. |
| `undergwent` | `SerialItem -> ProcessStep` | `prov:wasGeneratedBy` / inverse `prov:used` (W3C PROV-O §2.1) | `exact` | `ActualComponent` linked to `Action` in `QIFResults` (ISO 23952:2020 Clause 9.2) | `partial` | `process_product_association` (ISO 10303-242:2022 Clause 4.2.8) | `exact` | Connects a serialised item to each ordered manufacturing/inspection `ProcessStep`. |
| `evidenced_by` | `ProcessStep / SerialItem / Entity -> EvidenceRecord` | `prov:wasDerivedFrom` / `prov:hadPrimarySource` (W3C PROV-O §3.1) | `exact` | `MeasurementResults` reference to `ExternalFileReference` (ISO 23952:2020 Clause 9.4) | `partial` | `applied_document_reference` (ISO 10303-242:2022 Clause 4.2.12) | `exact` | Attaches verifiable public or certificate evidence records to a step or item. |
| `performed_at` | `ProcessStep -> Entity` (Facility / Supplier) | `prov:wasAssociatedWith` + `prov:atLocation` (W3C PROV-O §2.1, §3.1) | `exact` | `ManufacturingProcessTraceability` facility/machine ID (ISO 23952:2020 Clause 9.3) | `exact` | `applied_organization_assignment` / `site` (ISO 10303-242:2022 Clause 4.2.10) | `exact` | Identifies the responsible organisation (`prov:Agent`) and site (`prov:Location`) executing a `ProcessStep`. |
| `alternate_for` | `Component / Entity -> Component / Entity` | `prov:alternateOf` (W3C PROV-O §3.2) | `exact` | Alternate `Part` / qualified substitute (ISO 23952:2020 Clause 6.3) | `partial` | `alternate_product_relationship` (ISO 10303-242:2022 Clause 4.2.3) | `exact` | Expresses qualified second-source parts or substitute suppliers. |

---

## 4. Gaps and Proposals for Discussion (No Schema Change in Slice D)

1. **Temporal Ordering of `ProcessStep` (`prov:startedAtTime` / `prov:endedAtTime`)**:
   - *Gap*: W3C PROV-O (§2.1) and STEP AP242 (`action_directive`) support explicit sequence predecessors (`prov:wasInformedBy`) in addition to timestamps. OpenChokepoint v0.2.1 orders steps by list position or date.
   - *Proposal for v0.3*: Add an optional `preceded_by: <step_id>` field on `ProcessStep` so directed acyclic manufacturing graphs (e.g. parallel sub-component builds merging at braze/assembly) export directly to `prov:wasInformedBy`.
2. **Epistemic Confidence Grading (`evidence_grade`)**:
   - *Gap*: OpenChokepoint's five-tier `evidence_grade` (`confirmed`, `reported`, `inferred`, `speculative`, `no_evidence`) has no native attribute in W3C PROV-O, QIF, or STEP AP242, which assume internal enterprise records are authoritative.
   - *Export Mapping*: `tools/export_prov.py` preserves `ocp:evidenceGrade` in a dedicated namespace (`https://openchokepoint.org/ns#`).
3. **Verifiable Cryptographic Digests on `EvidenceRecord` (Cross-reference Slice B / #17)**:
   - *Gap*: STEP AP242 `digital_signature` and W3C Verifiable Credentials support detached content hashes, enabling suppliers to prove a QIF or AP242 certificate exists without disclosing export-controlled geometry or parameters.
