# Handling: Unclassified — public
# SPDX-License-Identifier: Apache-2.0
"""Unit tests for Slice B Verifiable Evidence Pointers (#17)."""
from __future__ import annotations

import copy
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import validate as val_mod  # noqa: E402
import verify_pointer as vp_mod  # noqa: E402


class TestVerifiablePointer(unittest.TestCase):
    def setUp(self) -> None:
        self.onto = val_mod.load(ROOT / "schema" / "openchokepoint.yaml")
        self.demo_path = ROOT / "examples" / "synthetic-verifiable-pointer.yaml"

    def test_schema_version_and_synthetic_demo_validate(self) -> None:
        self.assertEqual(self.onto["schema"]["version"], "0.3.0-draft")
        errs = val_mod.validate(self.demo_path, self.onto, tier="public")
        self.assertEqual(errs, [])

    def test_backward_compatible_with_v021_examples(self) -> None:
        ref_dir = Path(r"c:\Users\rosedale\Desktop\crypto\bounty_sweeper\phase7_refs\openchokepoint\examples")
        if ref_dir.exists():
            for yml in sorted(ref_dir.glob("*.yaml")):
                errs = val_mod.validate(yml, self.onto, tier="public")
                self.assertEqual(errs, [], f"Backward-compatibility failure on {yml}: {errs}")

    def test_validator_rejects_malformed_digest_and_inline_content(self) -> None:
        data = val_mod.load(self.demo_path)
        bad_objs = copy.deepcopy(data["objects"])
        ev = [o for o in bad_objs if o["type"] == "EvidenceRecord"][0]
        ev["digest"] = "not-a-valid-hex-digest"
        ev["payload"] = "inline technical data is forbidden"
        errs = val_mod.check_thread(bad_objs, data["links"], tier="public")
        joined = "\n".join(errs)
        self.assertIn("EV-002", joined)
        self.assertIn("EV-006", joined)

    def test_end_to_end_detached_signature_and_tamper_rejection(self) -> None:
        rc = vp_mod.main([str(self.demo_path)])
        self.assertEqual(rc, 0)

        data = val_mod.load(self.demo_path)
        ev = [o for o in data["objects"] if o["type"] == "EvidenceRecord"][0]
        env = vp_mod.sign_detached_claim(
            evidence_record=ev,
            record_bytes=vp_mod.SYNTHETIC_DEMO_RECORD_BYTES,
            salt_hex=vp_mod.SYNTHETIC_DEMO_SALT_HEX,
            signing_key_hex=vp_mod.SYNTHETIC_DEMO_KEY_HEX,
        )
        # Tampering with disclosed record bytes must fail verification
        ok, errs = vp_mod.verify_detached_claim(
            evidence_record=ev,
            detached_envelope=env,
            record_bytes=b"TAMPERED-RECORD-CONTENT",
            salt_hex=vp_mod.SYNTHETIC_DEMO_SALT_HEX,
            signing_key_hex=vp_mod.SYNTHETIC_DEMO_KEY_HEX,
        )
        self.assertFalse(ok)
        self.assertTrue(any("Digest mismatch" in e for e in errs))


if __name__ == "__main__":
    unittest.main()
