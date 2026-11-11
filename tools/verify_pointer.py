#!/usr/bin/env python3
# Handling: Unclassified — public
# SPDX-License-Identifier: Apache-2.0
"""Offline verifier and synthetic demo generator for Slice B Verifiable Evidence Pointers (#17).

Uses only the Python standard library (hashlib, hmac, base64, json) + PyYAML so CI runs with zero network access.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import hmac
import json
import sys
from pathlib import Path
from typing import Any

import yaml


def canonical_claim_bytes(claim_payload: dict[str, Any]) -> bytes:
    """Return deterministic RFC 8785-style canonical JSON bytes for signing/verification."""
    return json.dumps(claim_payload, sort_keys=True, separators=(",", ":")).encode("utf-8")


def compute_salted_digest(record_bytes: bytes, salt_hex: str, algorithm: str = "sha256") -> str:
    """Compute H(salt_bytes || record_bytes) using sha256, sha384, or sha512."""
    if algorithm not in ("sha256", "sha384", "sha512"):
        raise ValueError(f"Unsupported hash_algorithm: {algorithm}")
    h = hashlib.new(algorithm)
    h.update(bytes.fromhex(salt_hex))
    h.update(record_bytes)
    return h.hexdigest()


def sign_detached_claim(
    *,
    evidence_record: dict[str, Any],
    record_bytes: bytes,
    salt_hex: str,
    signing_key_hex: str,
) -> dict[str, Any]:
    """Produce a W3C VC-aligned detached EvidencePointerClaim signed with a synthetic key."""
    alg = str(evidence_record.get("hash_algorithm", "sha256"))
    digest = compute_salted_digest(record_bytes, salt_hex, alg)
    key_bytes = bytes.fromhex(signing_key_hex)
    pub_Verifier_id = hashlib.sha256(key_bytes).hexdigest()

    payload = {
        "type": ["VerifiableCredential", "OpenChokepointEvidencePointer"],
        "version": "0.3.0-draft",
        "evidence_record_id": str(evidence_record["id"]),
        "record_kind": str(evidence_record["record_kind"]),
        "issuer": str(evidence_record["issuer"]),
        "issuer_id": str(evidence_record["issuer_id"]),
        "issued_on": str(evidence_record["issued_on"]),
        "hash_algorithm": alg,
        "digest": digest,
        "salt_sha256": hashlib.sha256(bytes.fromhex(salt_hex)).hexdigest(),
        "signature_ref": str(evidence_record["signature_ref"]),
    }
    sig_bytes = hmac.new(key_bytes, canonical_claim_bytes(payload), hashlib.sha256).digest()
    return {
        "claim": payload,
        "proof": {
            "type": "SyntheticDetachedHmacSha256Signature2026",
            "verificationMethod": f"{evidence_record['issuer_id']}#key-1",
            "publicKeyFingerprintSha256": pub_Verifier_id,
            "signatureValue": base64.urlsafe_b64encode(sig_bytes).decode("ascii").rstrip("="),
        },
    }


def verify_detached_claim(
    *,
    evidence_record: dict[str, Any],
    detached_envelope: dict[str, Any],
    record_bytes: bytes,
    salt_hex: str,
    signing_key_hex: str,
) -> tuple[bool, list[str]]:
    """Verify a detached claim envelope against an EvidenceRecord YAML node and disclosed bytes."""
    errors: list[str] = []
    claim = detached_envelope.get("claim") or {}
    proof = detached_envelope.get("proof") or {}

    for field in ("id", "record_kind", "issuer", "issuer_id", "issued_on", "hash_algorithm", "digest", "signature_ref"):
        claim_key = "evidence_record_id" if field == "id" else field
        if str(evidence_record.get(field)) != str(claim.get(claim_key)):
            errors.append(
                f"Envelope mismatch on {field}: YAML has {evidence_record.get(field)!r}, claim has {claim.get(claim_key)!r}"
            )

    alg = str(evidence_record.get("hash_algorithm", "sha256"))
    computed_digest = compute_salted_digest(record_bytes, salt_hex, alg)
    if computed_digest != str(evidence_record.get("digest")):
        errors.append(
            f"Digest mismatch: computed {computed_digest}, EvidenceRecord has {evidence_record.get('digest')}"
        )

    expected_salt_commit = hashlib.sha256(bytes.fromhex(salt_hex)).hexdigest()
    if expected_salt_commit != str(claim.get("salt_sha256")):
        errors.append("Salt commitment mismatch")

    key_bytes = bytes.fromhex(signing_key_hex)
    expected_sig = hmac.new(key_bytes, canonical_claim_bytes(claim), hashlib.sha256).digest()
    expected_b64 = base64.urlsafe_b64encode(expected_sig).decode("ascii").rstrip("=")
    provided_b64 = str(proof.get("signatureValue", ""))
    if not hmac.compare_digest(expected_b64, provided_b64):
        errors.append("Cryptographic signature verification failed")

    return (len(errors) == 0), errors


SYNTHETIC_DEMO_RECORD_BYTES = b"SYNTHETIC-ONLY-DO-NOT-USE-REAL-DATA: lot=NF-0042 step=hip cert=evd-2101\n"
SYNTHETIC_DEMO_SALT_HEX = "a1b2c3d4e5f60718293a4b5c6d7e8f90a1b2c3d4e5f60718293a4b5c6d7e8f90"
SYNTHETIC_DEMO_KEY_HEX = "0f1e2d3c4b5a69788796a5b4c3d2e1f00f1e2d3c4b5a69788796a5b4c3d2e1f0"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Verify synthetic verifiable EvidenceRecord pointers offline.")
    parser.add_argument(
        "instance",
        nargs="?",
        default=str(Path(__file__).resolve().parent.parent / "examples" / "synthetic-verifiable-pointer.yaml"),
        help="Path to YAML trace containing verifiable EvidenceRecord pointer",
    )
    args = parser.parse_args(argv)
    data = yaml.safe_load(Path(args.instance).read_text(encoding="utf-8"))
    ev_records = [o for o in data.get("objects", []) if o.get("type") == "EvidenceRecord" and "digest" in o]
    if not ev_records:
        print("FAIL: no EvidenceRecord with Slice B verifiable pointer found", file=sys.stderr)
        return 1

    ev = ev_records[0]
    envelope = sign_detached_claim(
        evidence_record=ev,
        record_bytes=SYNTHETIC_DEMO_RECORD_BYTES,
        salt_hex=SYNTHETIC_DEMO_SALT_HEX,
        signing_key_hex=SYNTHETIC_DEMO_KEY_HEX,
    )
    ok, errs = verify_detached_claim(
        evidence_record=ev,
        detached_envelope=envelope,
        record_bytes=SYNTHETIC_DEMO_RECORD_BYTES,
        salt_hex=SYNTHETIC_DEMO_SALT_HEX,
        signing_key_hex=SYNTHETIC_DEMO_KEY_HEX,
    )
    if not ok:
        for e in errs:
            print(f"FAIL: {e}", file=sys.stderr)
        return 1
    print(f"OK   Verified Slice B pointer {ev['id']} ({ev['hash_algorithm']}:{ev['digest'][:16]}...)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
