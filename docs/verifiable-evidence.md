# Verifiable Evidence Pointers: Design Note & Threat Model

## 1. Overview & Context
In supply chain and manufacturing ecosystems, real evidence records (such as material test certificates, heat-treatment logs, or non-destructive inspection results) contain proprietary or confidential business data that cannot be publicly exposed. However, downstream consumers and auditors require verifiable proof that a specific record exists, has not been tampered with, and was issued by an authorized entity.

This document specifies the design for a **Verifiable Evidence Pointer** (`EvidenceRecord`), establishing a cryptographic claim mechanism that references offline evidence without disclosing raw contents.

---

## 2. Threat Model

This threat model evaluates potential attack vectors against off-chain verifiable evidence claims and defines security guarantees provided by the `EvidenceRecord` 0.3.0 spec.

### 2.1 Threat Vectors & Mitigation Strategies

| Threat Vector | Description | Severity | Mitigation Strategy |
| :--- | :--- | :--- | :--- |
| **Record Forgery (Tampering)** | An attacker modifies the offline evidence document after issuance and claims it satisfies the original pointer. | High | Cryptographic digest enforcement. The validator checks that `digest` matches `sha256` or `blake3` over the exact byte stream of the original file. |
| **Claim Alteration** | An attacker alters metadata (e.g., `issuer`, `issuanceDate`) within the `EvidenceRecord` JSON pointer itself. | High | Digital signature verification. The `signature` block covers the canonicalized JSON representation of the claim metadata using the issuer's public key. |
| **Replay & Substitution** | An attacker takes a valid `EvidenceRecord` pointer from a legitimate component and attaches it to a different, non-compliant part. | Medium | Unique identifier binding (`id` or `subjectDid`). The evidence record pointer must explicitly bind to the parent `ChokepointTrace` entity or batch identifier. |
| **Data Disclosure / Exposure** | Raw evidence records accidentally get embedded or committed to public/ledger state. | Critical | Absolute isolation rule. The validator strictly rejects any `EvidenceRecord` containing embedded document bodies or raw base64 data payloads. |
| **Algorithm Downgrade** | An attacker attempts to use weak/broken cryptographic hash functions (e.g., MD5, SHA-1) to create hash collisions. | Medium | Strict algorithm whitelist (`sha256`, `blake3`). Unknown or insecure algorithms trigger immediate schema validation failure. |

---

## 3. Standard Alignments & Justification

### 3.1 W3C Verifiable Credentials Data Model 2.0
We align the `EvidenceRecord` structure with W3C VC Data Model 2.0 conventions:
- **`issuer`**: Identified via a URI or Decentralized Identifier (DID) representing the issuing entity (lab, supplier, inspector).
- **`credentialSubject`**: Binds the claim to the specific evidence digest and target resource without revealing underlying data.
- **`proof` / `signature`**: Contains signature algorithm metadata (`Ed25519Signature2020` or `EcdsaSecp256k1Signature2019`) and proof value.

*Justification:* Aligning with W3C VC 2.0 ensures interoperability with enterprise identity systems and standard cryptographic verification tools without reinventing credential schemas.

### 3.2 W3C PROV-O (Provenance Ontology)
The evidence provenance maps directly to PROV-O concepts:
- **`prov:Entity`**: The physical asset or batch under inspection.
- **`prov:Activity`**: The inspection/testing procedure performed.
- **`prov:Agent`**: The certified lab or supplier (`issuer`).

---

## 4. Key Management & Operational Assumptions

1. **Issuer Key Discovery:** Key resolution is handled out-of-band or via trusted DID registries / PKI anchors. The validator verifies the signature against the public key associated with `issuer`.
2. **Out-of-Band Verification:** Third parties with authorized access to raw files perform hash verification offline by running local validation tools against the published `digest`.
3. **Out-of-Scope:** This design does not protect against insider threats where a certified issuer intentionally issues a fraudulent certificate for a failing part before hashing it.