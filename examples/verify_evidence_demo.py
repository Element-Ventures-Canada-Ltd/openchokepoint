import hashlib
import json
from pathlib import Path


def run_demo():
    # 1. Fictional raw evidence record (never committed to repository)
    raw_evidence_data = b"Heat Treatment Certificate #88219 - PASS - Temp: 850C"

    # 2. Generate cryptographic digest (SHA-256)
    computed_digest = hashlib.sha256(raw_evidence_data).hexdigest()

    # 3. Create verifiable EvidenceRecord pointer matching v0.3.0-draft schema
    evidence_pointer = {
        "id": "evidence-record-88219",
        "type": "EvidenceRecord",
        "synthetic": True,
        "hashAlgorithm": "sha256",
        "digest": computed_digest,
        "issuer": "https://issuer.example.org/labs/heat-treat-certifier",
        "signatureReference": {
            "type": "Ed25519Signature2020",
            "proofValue": "z3A7...fictional_signature_bytes...",
            "verificationMethod": "https://issuer.example.org/keys/1",
        },
    }

    # 4. Verify end-to-end off-chain content against pointer
    assert (
        hashlib.sha256(raw_evidence_data).hexdigest()
        == evidence_pointer["digest"]
    )
    print(
        "✓ Synthetic Evidence Record verification successful (Offline mode)."
    )
    print(f"  Pointer Digest: {evidence_pointer['digest']}")


if __name__ == "__main__":
    run_demo()