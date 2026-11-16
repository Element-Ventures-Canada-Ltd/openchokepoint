import hashlib
import ed25519 # Requires: pip install ed25519

def run_demo():
    # 1. Setup
    signing_key, verifying_key = ed25519.create_keypair()
    record_content = b"Sensitive Heat-Treatment Certificate Data"
    
    # 2. Create Digest
    digest = hashlib.sha256(record_content).hexdigest()
    
    # 3. Sign
    signature = signing_key.sign(digest.encode())
    
    # 4. Construct Pointer
    pointer = {
        "id": "evidence-001",
        "digest": digest,
        "hash_algorithm": "sha256",
        "issuer_id": "did:example:supplier-a",
        "signature": signature.hex()
    }
    
    # 5. Verify
    verifying_key.verify(bytes.fromhex(pointer["signature"]), digest.encode())
    print("Verification Successful: Record integrity confirmed.")

if __name__ == "__main__":
    run_demo()
