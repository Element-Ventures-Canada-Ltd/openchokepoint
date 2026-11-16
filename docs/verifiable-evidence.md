# Verifiable EvidenceRecord Pointer

## Threat Model
- **Forgery:** Prevented by requiring a cryptographic signature from a known issuer.
- **Alteration:** The content hash (digest) ensures that if the underlying record changes by even one bit, the pointer becomes invalid.
- **Replay:** The `EvidenceRecord` should include a timestamp or nonce (if implemented in future versions) to prevent replay of old claims.
- **Non-Disclosure:** The design explicitly forbids the inclusion of raw record content in the `EvidenceRecord` object.

## Claim Format
We adopt a simplified W3C Verifiable Credential-inspired structure:
- `digest`: Hex-encoded SHA-256 hash of the record.
- `hash_algorithm`: Currently "sha256".
- `issuer_id`: URI identifying the supplier.
- `signature`: Ed25519 signature of the digest.

## Limitations
This design does not protect against an issuer providing a hash of a fraudulent document. It only proves that the document *as it existed at the time of signing* has not been altered.
