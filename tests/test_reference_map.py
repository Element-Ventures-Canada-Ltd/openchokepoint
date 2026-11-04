# Handling: Unclassified — public
"""Consistency checks for docs/reference-maps/sovereign-space-supply-chain/ (standard library + PyYAML)."""
import re
import sys
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import validate as V  # noqa: E402

MAP = ROOT / "docs" / "reference-maps" / "sovereign-space-supply-chain"
GRAPH = ROOT / "examples" / "synthetic-space-supply-chain-archetypes.yaml"


def load(p):
    return yaml.safe_load(Path(p).read_text(encoding="utf-8"))


class ReferenceMapTests(unittest.TestCase):
    def test_graph_validates(self):
        onto = V.load(ROOT / "schema" / "openchokepoint.yaml")
        self.assertEqual(V.validate(GRAPH, onto), [])

    def test_ids_and_edges_consistent(self):
        arche = load(MAP / "archetypes.yaml")["archetypes"]
        ids = {a["id"] for a in arche}
        self.assertEqual(len(ids), len(arche))
        edges = load(MAP / "dependency-edges.yaml")
        codes = set(edges["edge_codes"])
        for e in edges["edges"]:
            self.assertIn(e["feeds"], ids)
            self.assertIn(e["consumer"], ids)
            self.assertIn(e["code"], codes)
        graph = load(GRAPH)
        self.assertEqual({o["id"] for o in graph["objects"]}, {f"ent-ssc-{i}" for i in ids})
        self.assertEqual(len(graph["links"]), len(edges["edges"]))

    def test_risk_placement_uses_known_categories(self):
        cats = {c["code"] for c in load(MAP / "annex-b-risk-categories.yaml")["categories"]}
        self.assertEqual(len(cats), 13)
        for a in load(MAP / "archetypes.yaml")["archetypes"]:
            self.assertTrue(a["annex_b_primary"], a["id"])
            self.assertLessEqual(set(a["annex_b_primary"] + a["annex_b_secondary"]), cats, a["id"])

    def test_every_archetype_has_hs_or_service_marker(self):
        for a in load(MAP / "archetypes.yaml")["archetypes"]:
            hs = a["hs_2022"]
            if isinstance(hs, str):
                self.assertEqual(hs, "n/a (service)", a["id"])
            else:
                for code in hs:
                    self.assertRegex(code, r"^\d{4}\.\d{2}$", a["id"])

    def test_chokepoints_reference_archetypes(self):
        ids = {a["id"] for a in load(MAP / "archetypes.yaml")["archetypes"]}
        cps = load(MAP / "generic-chokepoints.yaml")["chokepoints"]
        self.assertEqual(len(cps), 10)
        for c in cps:
            self.assertLessEqual(set(c["archetypes"]), ids)


if __name__ == "__main__":
    unittest.main()
