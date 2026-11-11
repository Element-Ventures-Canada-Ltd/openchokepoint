Handling: Unclassified — public

# Verifiable Evidence Pointers: Threat Model, Claim Envelope, and Offline Verification (Slice B)

Part of #3 (Closes #17).

## 1. Problem Statement & Design Boundary

Real aerospace and defence supply-chain evidence records—such as additive-manufacturing build logs, Hot Isostatic Pressing (HIP) furnace charts, heat-treatment certificates, and dimensional inspection reports—cannot be published in an open repository because they contain proprietary or export-controlled technical data.

In OpenChokepoint v0.2.1, an `EvidenceRecord` can state that a certificate is claimed to exist (`content_hash: sha256:<64 hex>` or `citation: https://...`), but a bare hash does not prove **who** issued the claim, **when** it was bound to a specific `EvidenceRecord` metadata header, or whether an attacker replayed a hash from an unrelated record.

**Slice B** introduces **Verifiable Evidence Pointers** (`schema/openchokepoint.yaml` `0.3.0-draft`):
1. An issuer computes a salted canonical digest over the private record and signs a detached **Evidence Pointer Claim** binding `(record_id, record_kind, issuer, issuer_id, issued_on, hash_algorithm, digest)`.
2. The public OpenChokepoint YAML trace stores **only the pointer fields** (`hash_algorithm`, `digest`, `issuer_id`, `signature_ref`, and `content_hash`)—**never** the underlying record content.
3. An authorised auditor who is later shown the private record (under NDA or regulatory inspection) runs `python3 tools/verify_pointer.py` offline to confirm that:
   - the detached signature under `issuer_id`'s public key is cryptographically valid, and
   - the canonical digest of the disclosed file matches the pointer published on the digital thread.

---

## 2. Threat Model

| Threat Actor / Vector | Attack Description | Mitigation in Slice B |
|---|---|---|
| **T1 — Unauthorised Claim Forgery** | A third party fabricates an `EvidenceRecord` claiming that `Northfield Test Foundry` issued a material certificate (`evd-1700`) for a lot it never produced. | `issuer_id` (`did:web:...` or `urn:ietf:params:oauth:jwk-thumbprint:sha-256:...`) and `signature_ref` bind the pointer to a detached Ed25519 signature over the canonical JSON claim envelope. Forgery requires the issuer's private key. |
| **T2 — Post-Hoc Record Substitution (Tampering)** | A supplier alters a heat-treatment or inspection report after an incident while keeping the same `EvidenceRecord.id` (`evd-1702`). | `digest` (`sha256`, `sha384`, or `sha512`) is cryptographically bound inside the signed claim envelope; any single-bit modification to the underlying document invalidates verification (`tools/verify_pointer.py` exits non-zero). |
| **T3 — Cross-Step / Cross-Serial Replay** | A supplier reuses a valid signed hash from serial `R-100-0007` (`evd-1706`) to cover an un-evidenced cleaning step on serial `R-100-0008`. | The signed payload binds `evidence_record_id`, `record_kind`, `issuer_id`, and `issued_on` alongside `digest`. Replaying a signature onto a different `EvidenceRecord.id` or `record_kind` fails canonical envelope verification. |
| **T4 — Low-Entropy Dictionary / Rainbow Guessing** | Public observers attempt to brute-force a predictable short certificate template from its public `sha256` hash. | Detached claim envelopes include a 256-bit random `salt_nonce` held with the private record (or RFC 9421 / W3C VC salted digest), preventing offline dictionary recovery from the public repository alone. |
| **T5 — Accidental Technical Data Leakage in YAML** | A contributor pastes raw test measurements or base64 blobs into `EvidenceRecord` fields. | `tools/validate.py` rules `EV-002` and `EV-005`–`EV-008` strictly reject inline content fields, enforce string length caps (`<= 120` chars), and validate strict algorithm/digest syntax. |

### What This Design Does **Not** Protect Against (Explicit Non-Goals)
1. **Physical Sensor or Lab Fraud Prior to Signing**: Cryptographic signing proves *origin and integrity since issuance*, not that a thermocouple was calibrated or that the physical alloy matches the certificate without physical audit.
2. **Key Compromise Without Revocation**: If an issuer's private signing key is stolen and not rotated in their `did:web` document, an attacker with the key can sign claims until revocation.
3. **Public Verification of Private Content**: By design, a member of the public who does *not* possess the underlying record can verify the detached signature over the pointer metadata, but cannot verify the file bytes without authorised disclosure.

---

## 3. Standards Alignment: W3C Verifiable Credentials 2.0 & W3C PROV-O

- **W3C Verifiable Credentials Data Model 2.0** (*W3C Candidate Recommendation, 2024*, §4): Our detached claim envelope uses the `VerifiableCredential` / `EvidencePointerCredential` structure (`issuer`, `validFrom`, `credentialSubject.id`, `credentialSubject.digestMultibase`, and `proof` with Ed25519 / RFC 8032 signature).
- **W3C PROV-O** (*W3C Recommendation, 2013*, §3.1): `EvidenceRecord` maps to `prov:Entity` with `prov:wasAttributedTo` (`issuer_id`) and `prov:generatedAtTime` (`issued_on`).

---

## 4. Schema v0.3.0-draft Additions (`EvidenceRecord`)

All existing v0.2.1 traces remain 100% valid. `EvidenceRecord` adds four optional properties:
- `hash_algorithm`: `enum [sha256, sha384, sha512]`
- `digest`: lowercase hex digest matching `hash_algorithm` (`64`, `96`, or `128` hex chars)
- `issuer_id`: URI (`did:...` or `urn:...`) identifying the issuer's cryptographic authority
- `signature_ref`: URI (`https://...` or `urn:sig:...`) pointing to the detached signature envelope
