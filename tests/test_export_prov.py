#!/usr/bin/env python3
# Handling: Unclassified — public
# SPDX-License-Identifier: Apache-2.0
"""Tests for tools/export_prov.py: PROV-O export of OpenChokepoint instance files.

Run:  python3 -m unittest discover -s tests -v

Requires rdflib (installed in CI for this test file only). Every fixture is
invented: fictional names and identifiers on the reserved example.org domain.
"""
import importlib.util
import sys
import unittest
from pathlib import Path

from rdflib import Graph
from rdflib.namespace import RDF

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "sdk" / "python"))

import openchokepoint  # noqa: E402
from openchokepoint.registry import Registry  # noqa: E402

PROV = "http://www.w3.org/ns/prov#"
OCPR = "https://openchokepoint.example/record/"

THREAD = ROOT / "examples" / "synthetic-turbopump-thread.yaml"
PLAIN = ROOT / "examples" / "synthetic-example.yaml"


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


EXPORT = _load("export_prov", ROOT / "tools" / "export_prov.py")


class ExportBasics(unittest.TestCase):
    def test_every_object_becomes_a_prov_node(self):
        reg = Registry.load(THREAD)
        g = EXPORT.build_graph(reg)
        for obj in reg.objects:
            uri = EXPORT.OCP_RECORD[obj.id]
            self.assertTrue((uri, RDF.type, None) in g, f"{obj.id} lacks an rdf:type")

    def test_turtle_output_parses(self):
        reg = Registry.load(THREAD)
        g = EXPORT.build_graph(reg)
        ttl = g.serialize(format="turtle")
        parsed = Graph().parse(data=ttl, format="turtle")
        self.assertEqual(len(parsed), len(g), "Turtle output must round-trip without loss")

    def test_jsonld_output_parses(self):
        reg = Registry.load(PLAIN)
        g = EXPORT.build_graph(reg)
        jld = g.serialize(format="json-ld")
        parsed = Graph().parse(data=jld, format="json-ld")
        self.assertEqual(len(parsed), len(g), "JSON-LD output must round-trip without loss")


class ExportMappings(unittest.TestCase):
    """Spot-check the PROV-O mapping declared in docs/standards-crosswalk.md section 3."""

    def setUp(self):
        self.g = EXPORT.build_graph(Registry.load(THREAD))

    def triple(self, subj, pred, obj):
        return (EXPORT.OCP_RECORD[subj], EXPORT.PROV[pred], EXPORT.OCP_RECORD[obj])

    def test_instance_of_is_specialization(self):
        self.assertIn(self.triple("ser-1007", "specializationOf", "cmp-1001"), self.g)

    def test_made_from_is_derivation(self):
        self.assertIn(self.triple("ser-1007", "wasDerivedFrom", "lot-1001"), self.g)

    def test_underwent_is_activity_use(self):
        # ProcessStep (activity) used SerialItem (entity)
        self.assertIn(self.triple("stp-1701", "used", "ser-1007"), self.g)

    def test_evidenced_by_is_generated_by(self):
        # EvidenceRecord wasGeneratedBy ProcessStep
        self.assertIn(self.triple("evd-1701", "wasGeneratedBy", "stp-1701"), self.g)

    def test_performed_at_is_at_location(self):
        self.assertIn(self.triple("stp-1701", "atLocation", "fac-1001"), self.g)

    def test_produced_by_is_attributed_to(self):
        self.assertIn(self.triple("lot-1001", "wasAttributedTo", "ent-1001"), self.g)

    def test_provides_capability_flips_to_attribution(self):
        # capability prov:wasAttributedTo the provider
        g = EXPORT.build_graph(Registry.load(PLAIN))
        self.assertIn(
            (EXPORT.OCP_RECORD["cap-0001"], EXPORT.PROV["wasAttributedTo"], EXPORT.OCP_RECORD["fac-0001"]),
            g,
        )

    def test_no_inferred_sequence(self):
        """A link without a `sequence` never gets one invented. located_at links carry
        no sequence in the source; the exporter must not add ocp:sequence to them."""
        triples = [t for t in self.g if t[0] == EXPORT.OCP_RECORD["fac-1001"] and str(t[1]).endswith("sequence")]
        self.assertEqual(triples, [])


if __name__ == "__main__":
    unittest.main()
