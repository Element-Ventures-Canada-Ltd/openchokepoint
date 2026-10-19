# Standards Crosswalk

Mapping OpenChokepoint v0.2.1 to industry standards.

| Type/Link | W3C PROV-O | QIF (ISO 23952) | STEP AP242 (ISO 10303-242) | Notes |
| :--- | :--- | :--- | :--- | :--- |
| Component | prov:Entity | QIF:Part | PartDefinition | Exact mapping to entity/part |
| SerialItem | prov:Entity | QIF:IndividualPart | PartOccurrence | Exact mapping to instance |
| MaterialLot | prov:Entity | QIF:Material | MaterialDefinition | Partial: QIF focus is on properties |
| ProcessStep | prov:Activity | QIF:ProcessStep | ProcessOperation | Exact mapping to activity |
| EvidenceRecord | prov:Entity | QIF:InspectionResult | ProductDataManagement | Partial: QIF is specific to inspection |
| CriticalItem | prov:Entity | None | None | No direct standard equivalent |
| instance_of | rdf:type | QIF:partDefinition | - | Exact |
| made_from | prov:wasDerivedFrom | - | - | Exact |
| underwent | prov:wasAssociatedWith | - | - | Exact |
| evidenced_by | prov:wasGeneratedBy | - | - | Exact |
| performed_at | prov:atLocation | - | - | Exact |
| alternate_for | prov:alternateOf | - | - | Exact |