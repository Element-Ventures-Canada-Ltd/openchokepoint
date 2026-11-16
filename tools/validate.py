import hashlib

def validate_evidence_record(record):
    if "content" in record:
        raise ValueError("Security Violation: EvidenceRecord must not contain raw content.")
    
    if record.get("hash_algorithm") != "sha256":
        raise ValueError("Unsupported hash algorithm.")
    
    if len(record.get("digest", "")) != 64:
        raise ValueError("Malformed digest: expected 64-character hex string.")
    
    return True
