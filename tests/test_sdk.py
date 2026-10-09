#!/usr/bin/env python3
# Handling: Unclassified — public
# SPDX-License-Identifier: Apache-2.0
"""Tests for the Python SDK, the JSON Schema export and the chokepoint explorer.

Run:  python3 -m unittest discover -s tests -v

Standard library only (unittest); PyYAML is already required by the validator.
Every fixture is invented: fictional names and identifiers on the reserved example.org domain.
"""
import copy
import datetime
import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "sdk" / "python"))
from openchokepoint import Registry, find_root, validate  # noqa: E402


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


EXPORT = _load("export_jsonschema", ROOT / "tools" / "export_jsonschema.py")
EXPLORE = _load("explore", ROOT / "apps" / "chokepoint-explorer" / "explore.py")

THREAD = ROOT / "examples" / "synthetic-turbopump-thread.yaml"
SRC = ["https://example.org/synthetic/test"]
BASE = {"evidence_grade": "confirmed", "sources": SRC, "as_of": datetime.date(2026, 10, 7), "lifecycle": "active", "synthetic": True}


def rec(rtype, rid, **kw):
    r = {"type": rtype, "id": rid, **copy.deepcopy(BASE)}
    r.update(kw)
    return r


class RegistryTests(unittest.TestCase):
    def setUp(self):
        self.reg = Registry.load(THREAD)

    def test_finds_repository_root(self):
        self.assertEqual(find_root(), ROOT)

    def test_loads_every_record(self):
        raw = yaml.safe_load(THREAD.read_text(encoding="utf-8"))
        self.assertEqual(len(self.reg), len(raw["objects"]) + len(raw["links"]))
        self.assertTrue(self.reg.is_synthetic)
        self.assertEqual(self.reg.real_records(), [])

    def test_graph_walk(self):
        self.assertEqual([d.id for d in self.reg.targets("ser-1007", "instance_of")], ["cmp-1001"])
        self.assertEqual([p.id for p in self.reg.targets("lot-1001", "produced_by")], ["ent-1001"])

    def test_steps_in_stated_order(self):
        steps, ordered = self.reg.steps_for("ser-1007")
        self.assertTrue(ordered)
        self.assertEqual([seq for seq, _ in steps], list(range(1, 9)))

    def test_gap_shown_not_filled(self):
        self.assertEqual([s.id for s in self.reg.steps_without_evidence()], ["stp-1806"])
        self.assertEqual(self.reg.evidence_for("stp-1806"), [])

    def test_no_inferred_order(self):
        objects = [rec("SerialItem", "ser-1", serial="X-1", synthetic=False),
                   rec("ProcessStep", "stp-b", step_kind="inspection", synthetic=False),
                   rec("ProcessStep", "stp-a", step_kind="cleaning", synthetic=False)]
        links = [rec("underwent", "l-1", synthetic=False, **{"from": "ser-1", "to": "stp-b"}),
                 rec("underwent", "l-2", synthetic=False, **{"from": "ser-1", "to": "stp-a"})]
        steps, ordered = Registry(objects, links).steps_for("ser-1")
        self.assertFalse(ordered)
        self.assertEqual([s.id for _, s in steps], ["stp-b", "stp-a"])  # file order, untouched

    def test_missing_synthetic_flag_counts_as_real(self):
        r = Registry([{"type": "Entity", "id": "e-1"}], [])
        self.assertFalse(r.is_synthetic)


class ValidationTests(unittest.TestCase):
    def _write(self, data):
        tmp = tempfile.NamedTemporaryFile("w", suffix=".yaml", delete=False, encoding="utf-8")
        yaml.safe_dump(data, tmp, sort_keys=False)
        tmp.close()
        self.addCleanup(Path(tmp.name).unlink)
        return tmp.name

    def test_examples_pass(self):
        for path in sorted((ROOT / "examples").glob("*.yaml")):
            self.assertEqual(validate(path), [], path.name)

    def test_rule_ids_are_structured(self):
        bad = {"objects": [rec("EvidenceRecord", "evd-1", record_kind="inspection_report", issuer="Example Issuer",
                               issued_on=datetime.date(2026, 4, 1))], "links": []}
        issues = validate(self._write(bad))
        self.assertIn("EV-001", [i.rule for i in issues])

    def test_tier_is_checked(self):
        with self.assertRaises(ValueError):
            validate(THREAD, tier="open")


class JsonSchemaTests(unittest.TestCase):
    def test_committed_export_is_current(self):
        committed = (ROOT / "schema" / "openchokepoint.schema.json").read_text(encoding="utf-8")
        self.assertEqual(committed, EXPORT.render(), "run: python3 tools/export_jsonschema.py")

    def test_every_type_exported(self):
        onto = yaml.safe_load((ROOT / "schema" / "openchokepoint.yaml").read_text(encoding="utf-8"))
        defs = EXPORT.build(onto)["$defs"]
        for name in onto["object_types"]:
            self.assertIn(name, defs)
            self.assertFalse(defs[name]["additionalProperties"])
        for name in onto["link_types"]:
            self.assertIn("from", defs[f"link.{name}"]["required"])


class ExplorerTests(unittest.TestCase):
    def test_report_on_synthetic_thread(self):
        md, issues = EXPLORE.report(THREAD)
        self.assertEqual(issues, [])
        self.assertTrue(md.startswith("Handling: Unclassified — public"))
        self.assertIn("**missing**", md)
        self.assertIn("Declared critical items (synthetic)", md)

    def test_fails_closed_on_invalid_file(self):
        bad = {"objects": [{"type": "Entity", "id": "e-1", "synthetic": True}], "links": []}
        with tempfile.NamedTemporaryFile("w", suffix=".yaml", delete=False, encoding="utf-8") as tmp:
            yaml.safe_dump(bad, tmp)
        self.addCleanup(Path(tmp.name).unlink)
        md, issues = EXPLORE.report(tmp.name)
        self.assertIsNone(md)
        self.assertTrue(issues)

    def test_never_reports_real_judgments(self):
        reg = Registry([rec("CriticalItem", "cri-1", delay_band="d30_90", single_source=True,
                            qualified_alternate=False, synthetic=False)], [])
        self.assertEqual(EXPLORE.section_critical(reg), [])

    def test_unordered_steps_say_so(self):
        objects = [rec("SerialItem", "ser-1", serial="X-1", synthetic=False),
                   rec("ProcessStep", "stp-1", step_kind="cleaning", synthetic=False)]
        links = [rec("underwent", "l-1", synthetic=False, **{"from": "ser-1", "to": "stp-1"})]
        text = "\n".join(EXPLORE.section_threads(Registry(objects, links)))
        self.assertIn("Order not published", text)


if __name__ == "__main__":
    unittest.main()
