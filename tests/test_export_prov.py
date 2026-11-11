# Handling: Unclassified — public
"""Unit tests for Slice D W3C PROV-O export and standards crosswalk (#19)."""
from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import export_prov  # noqa: E402


SYNTHETIC_TRACE = {
    "schema_version": "0.2.1",
    "entities": [
        {"id": "ent-forge-alpha", "name": "Synthetic Forge Alpha", "country": "CA", "evidence_grade": "confirmed"},
        {"id": "ent-forge-beta", "name": "Synthetic Forge Beta", "country": "CA", "alternate_for": "ent-forge-alpha"},
    ],
    "components": [
        {"id": "cmp-impeller", "name": "Synthetic Turbopump Impeller", "category": "rotating"},
        {"id": "cmp-impeller-alt", "name": "Alternate Impeller", "alternate_for": ["cmp-impeller"]},
    ],
    "material_lots": [
        {"id": "lot-718-a", "material_family": "nickel-superalloy", "supplier_id": "ent-forge-alpha", "evidenced_by": ["ev-cert-1"]},
    ],
    "evidence_records": [
        {"id": "ev-cert-1", "kind": "public_release", "evidence_grade": "confirmed", "source_url": "https://example.org/release-1"},
    ],
    "process_steps": [
        {
            "id": "stp-hip-1",
            "step_kind": "hip",
            "performed_at": "ent-forge-alpha",
            "evidenced_by": ["ev-cert-1"],
            "evidence_grade": "confirmed",
        },
    ],
    "serial_items": [
        {
            "id": "ser-1007",
            "instance_of": "cmp-impeller",
            "made_from": ["lot-718-a"],
            "undergwent": ["stp-hip-1"],
            "evidenced_by": ["ev-cert-1"],
        },
    ],
    "critical_items": [
        {"id": "crit-impeller", "component_id": "cmp-impeller", "alternate_for": "cmp-impeller-alt"},
    ],
}


class TestExportProv(unittest.TestCase):
    def test_jsonld_maps_all_six_types_and_six_links(self) -> None:
        doc = export_prov.convert_trace_to_prov_jsonld(SYNTHETIC_TRACE)
        self.assertIn("@context", doc)
        self.assertIn("@graph", doc)
        by_id = {n["@id"]: n for n in doc["@graph"]}

        # Check all 6 entity types exist
        self.assertIn("ocp:Entity", by_id["urn:openchokepoint:ent-forge-alpha"]["@type"])
        self.assertIn("ocp:Component", by_id["urn:openchokepoint:cmp-impeller"]["@type"])
        self.assertIn("ocp:MaterialLot", by_id["urn:openchokepoint:lot-718-a"]["@type"])
        self.assertIn("ocp:EvidenceRecord", by_id["urn:openchokepoint:ev-cert-1"]["@type"])
        self.assertIn("ocp:ProcessStep", by_id["urn:openchokepoint:stp-hip-1"]["@type"])
        self.assertIn("ocp:SerialItem", by_id["urn:openchokepoint:ser-1007"]["@type"])
        self.assertIn("ocp:CriticalItem", by_id["urn:openchokepoint:crit-impeller"]["@type"])

        # Check all 6 relationship links map to PROV-O properties
        ser = by_id["urn:openchokepoint:ser-1007"]
        self.assertEqual(ser["prov:specializationOf"], "urn:openchokepoint:cmp-impeller")
        self.assertIn("urn:openchokepoint:lot-718-a", ser["prov:wasDerivedFrom"])
        self.assertIn("urn:openchokepoint:ev-cert-1", ser["prov:wasDerivedFrom"])
        self.assertIn("urn:openchokepoint:stp-hip-1", ser["prov:wasGeneratedBy"])

        stp = by_id["urn:openchokepoint:stp-hip-1"]
        self.assertEqual(stp["prov:wasAssociatedWith"], "urn:openchokepoint:ent-forge-alpha")
        self.assertIn("urn:openchokepoint:ev-cert-1", stp["prov:wasDerivedFrom"])

        alt_ent = by_id["urn:openchokepoint:ent-forge-beta"]
        self.assertIn("urn:openchokepoint:ent-forge-alpha", alt_ent["prov:alternateOf"])

    def test_turtle_export_is_valid_rdf_statements(self) -> None:
        ttl = export_prov.convert_trace_to_prov_turtle(SYNTHETIC_TRACE)
        self.assertIn("@prefix prov: <http://www.w3.org/ns/prov#> .", ttl)
        self.assertIn("<urn:openchokepoint:ser-1007> a prov:Entity, ocp:SerialItem", ttl)
        self.assertIn("prov:specializationOf <urn:openchokepoint:cmp-impeller>", ttl)
        self.assertIn("prov:wasGeneratedBy <urn:openchokepoint:stp-hip-1>", ttl)

    def test_cli_converts_synthetic_turbopump_example(self) -> None:
        synth_path = ROOT / "examples" / "synthetic-turbopump-thread.yaml"
        if not synth_path.exists():
            synth_path = Path(r"c:\Users\rosedale\Desktop\crypto\bounty_sweeper\phase7_refs\openchokepoint\examples\synthetic-turbopump-thread.yaml")
        proc = subprocess.run(
            [sys.executable, str(ROOT / "tools" / "export_prov.py"), str(synth_path), "--format", "jsonld"],
            capture_output=True,
            text=True,
            check=True,
        )
        parsed = json.loads(proc.stdout)
        self.assertTrue(len(parsed["@graph"]) >= 5)

    def test_crosswalk_document_covers_all_types_and_links(self) -> None:
        cw = (ROOT / "docs" / "standards-crosswalk.md").read_text(encoding="utf-8")
        self.assertTrue(cw.startswith("Handling: Unclassified — public"))
        for term in (
            "Component",
            "SerialItem",
            "MaterialLot",
            "ProcessStep",
            "EvidenceRecord",
            "CriticalItem",
            "instance_of",
            "made_from",
            "undergwent",
            "evidenced_by",
            "performed_at",
            "alternate_for",
            "W3C PROV-O",
            "ISO 23952",
            "ISO 10303-242",
        ):
            self.assertIn(term, cw)


if __name__ == "__main__":
    unittest.main()
