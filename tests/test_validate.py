#!/usr/bin/env python3
# Handling: Unclassified — public
# SPDX-License-Identifier: Apache-2.0
"""Tests for tools/validate.py. Standard library only (unittest); PyYAML is already required by the validator.

Run:  python3 -m unittest discover -s tests -v

Every fixture is invented: fictional names and identifiers on the reserved example.org domain,
no real organization, part or technical parameter.
"""
import copy
import datetime
import sys
import tempfile
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import validate as V  # noqa: E402

ONTO = V.load(ROOT / "schema" / "openchokepoint.yaml")
SRC = ["https://example.org/synthetic/test"]
BASE = {"evidence_grade": "confirmed", "sources": SRC, "as_of": datetime.date(2026, 10, 7), "lifecycle": "active", "synthetic": True}


def rec(rtype, rid, **kw):
    r = {"type": rtype, "id": rid, **copy.deepcopy(BASE)}
    r.update(kw)
    return r


def ev(rid="evd-1", **kw):
    r = rec("EvidenceRecord", rid, record_kind="inspection_report", issuer="Example Issuer", issued_on=datetime.date(2026, 4, 1))
    r.update(kw)
    return r


def thread():
    """Minimal valid synthetic thread: one serial, one step with evidence, one design and lot."""
    objects = [
        rec("Entity", "ent-1", name="Example Co", entity_kind="company", incorporation_jurisdiction="CA", controlling_jurisdiction="CA"),
        rec("Facility", "fac-1", name="Example Site", facility_kind="processing", host_jurisdiction="CA"),
        rec("Facility", "fac-2", name="Example Alternate Site", facility_kind="processing", host_jurisdiction="CA"),
        rec("Component", "cmp-1", part_number="X-1", revision="A", component_kind="rotor"),
        rec("MaterialLot", "lot-1", lot_number="L-1", material_class="metal_powder"),
        rec("SerialItem", "ser-1", serial="X-1-0001"),
        rec("ProcessStep", "stp-1", step_kind="cleaning"),
        rec("ProcessStep", "stp-2", step_kind="inspection"),
        ev("evd-1", content_hash="sha256:" + "a" * 64),
    ]
    links = [
        rec("instance_of", "l-1", **{"from": "ser-1", "to": "cmp-1"}),
        rec("made_from", "l-2", **{"from": "ser-1", "to": "lot-1"}),
        rec("produced_by", "l-3", **{"from": "lot-1", "to": "ent-1"}),
        rec("underwent", "l-4", sequence=1, **{"from": "ser-1", "to": "stp-1"}),
        rec("underwent", "l-5", sequence=2, **{"from": "ser-1", "to": "stp-2"}),
        rec("evidenced_by", "l-6", **{"from": "stp-1", "to": "evd-1"}),
        rec("performed_at", "l-7", **{"from": "stp-1", "to": "fac-1"}),
    ]
    return objects, links


def run(objects, links, where="examples"):
    """Write a temporary instance file inside the repo (so location rules apply) and validate it."""
    folder = ROOT / where
    created = not folder.exists()
    folder.mkdir(parents=True, exist_ok=True)
    try:
        return _run_in(folder, objects, links, where)
    finally:
        if created:
            folder.rmdir()


def _run_in(folder, objects, links, where):
    with tempfile.TemporaryDirectory(dir=folder, prefix=".test-") as d:
        path = Path(d) / "instance.yaml"
        path.write_text(yaml.safe_dump({"objects": objects, "links": links}, sort_keys=False), encoding="utf-8")
        if where.startswith("data"):
            (Path(d) / "provenance.yaml").write_text(yaml.safe_dump({
                "personal_information": "none", "export_controlled": False,
                "sources": ["https://example.org/public-report"]}), encoding="utf-8")
        return V.validate(path, ONTO)


def rules(errors):
    return {e.split(" ", 1)[0] for e in errors}


class Regression(unittest.TestCase):
    def test_v01_example_unchanged(self):
        self.assertEqual(V.validate(ROOT / "examples" / "synthetic-example.yaml", ONTO), [])

    def test_registry_extract_unchanged(self):
        path = ROOT / "data" / "registry" / "launch-chain.yaml"
        if path.exists():
            self.assertEqual(V.validate(path, ONTO), [])

    def test_thread_example_passes(self):
        self.assertEqual(V.validate(ROOT / "examples" / "synthetic-turbopump-thread.yaml", ONTO), [])

    def test_minimal_thread_passes(self):
        self.assertEqual(run(*thread()), [])

    def test_unknown_type_fails_closed(self):
        o, l = thread()
        o.append(rec("Drawing", "drw-1"))
        self.assertTrue(any("unknown object type" in e for e in run(o, l)))

    def test_real_record_outside_data_fails(self):
        o, l = thread()
        o[0]["synthetic"] = False
        self.assertTrue(any("accepted only under data/" in e for e in run(o, l)))

    def test_real_record_http_source_fails(self):
        o = [rec("Entity", "ent-9", name="Example Co", entity_kind="company", incorporation_jurisdiction="CA",
                 controlling_jurisdiction="CA", synthetic=False, sources=["http://example.org/x"])]
        self.assertTrue(any("public https" in e for e in run(o, [], where="data/.tests")))


class EvidenceRecordRules(unittest.TestCase):
    def check(self, record, where="examples"):
        o, l = thread()
        o[-1] = record
        return run(o, l, where)

    def test_hash_passes(self):
        self.assertEqual(self.check(ev(content_hash="sha256:" + "b" * 64)), [])

    def test_https_citation_passes(self):
        self.assertEqual(self.check(ev(citation="https://example.org/report", citation_section="Section 3")), [])

    def test_no_pointer_fails_ev001(self):
        self.assertIn("EV-001", rules(self.check(ev())))

    def test_inline_body_fails_ev002(self):
        self.assertIn("EV-002", rules(self.check(ev(content_hash="sha256:" + "c" * 64, body="the full record text"))))

    def test_bad_hash_fails_ev002(self):
        self.assertIn("EV-002", rules(self.check(ev(content_hash="the record, pasted here"))))

    def test_long_section_fails_ev002(self):
        self.assertIn("EV-002", rules(self.check(ev(citation="https://example.org/r", citation_section="x" * 200))))

    def test_unknown_property_fails(self):
        errs = self.check(ev(content_hash="sha256:" + "d" * 64, colour="blue"))
        self.assertTrue(any("unknown property 'colour'" in e for e in errs))

    def test_http_citation_fails_ev003(self):
        self.assertIn("EV-003", rules(self.check(ev(citation="http://example.org/report"))))

    def test_real_evidence_hash_only_fails_ev004(self):
        o = [ev("evd-9", content_hash="sha256:" + "e" * 64, synthetic=False)]
        self.assertIn("EV-004", rules(run(o, [], where="data/.tests")))

    def test_real_evidence_with_public_citation_passes(self):
        o = [ev("evd-9", citation="https://example.org/public-report", citation_section="Section 4", synthetic=False)]
        self.assertEqual(run(o, [], where="data/.tests"), [])


class ThreadRules(unittest.TestCase):
    def test_duplicate_sequence_fails_dt001(self):
        o, l = thread()
        l[4]["sequence"] = 1
        self.assertIn("DT-001", rules(run(o, l)))

    def test_real_inferred_fails_dt002(self):
        o = [rec("Component", "cmp-9", part_number="X-9", revision="A", component_kind="rotor",
                 synthetic=False, evidence_grade="inferred")]
        self.assertIn("DT-002", rules(run(o, [], where="data/.tests")))


class CriticalItemRules(unittest.TestCase):
    def ci(self, rid="cri-1", **kw):
        r = rec("CriticalItem", rid, delay_band="d30_90", single_source=True, qualified_alternate=False, evidence_grade="inferred")
        r.update(kw)
        return r

    def flag(self, lid, ci, target, **kw):
        return rec("flags", lid, **{"from": ci, "to": target}, **kw)

    def test_synthetic_on_synthetic_passes(self):
        o, l = thread()
        o.append(self.ci())
        l.append(self.flag("l-90", "cri-1", "cmp-1"))
        self.assertEqual(run(o, l), [])

    def test_real_critical_item_fails_ci001(self):
        o, l = thread()
        o.append(self.ci(synthetic=False))
        l.append(self.flag("l-90", "cri-1", "cmp-1"))
        self.assertIn("CI-001", rules(run(o, l, where="data/.tests")))

    def test_flagging_real_component_fails_ci002(self):
        o, l = thread()
        o[3]["synthetic"] = False                       # cmp-1 becomes a real record
        o.append(self.ci())
        l.append(self.flag("l-90", "cri-1", "cmp-1"))
        self.assertIn("CI-002", rules(run(o, l, where="data/.tests")))

    def test_alternate_from_real_facility_fails_ci002(self):
        o, l = thread()
        o[2]["synthetic"] = False                       # fac-2 becomes a real record
        o.append(self.ci(single_source=False, qualified_alternate=True))
        l += [self.flag("l-90", "cri-1", "cmp-1"), rec("alternate_for", "l-91", **{"from": "fac-2", "to": "cri-1"})]
        self.assertIn("CI-002", rules(run(o, l, where="data/.tests")))

    def test_synthetic_looking_flag_reaching_real_record_fails_ci003(self):
        o, l = thread()
        o[0]["synthetic"] = False                       # ent-1 (the lot's producer) is real; lot-1 stays synthetic
        o.append(self.ci(name="Fictional feedstock risk"))
        l.append(self.flag("l-90", "cri-1", "lot-1"))
        self.assertIn("CI-003", rules(run(o, l, where="data/.tests")))

    def test_qualified_alternate_without_link_fails_ci004(self):
        o, l = thread()
        o.append(self.ci(single_source=False, qualified_alternate=True))
        l.append(self.flag("l-90", "cri-1", "cmp-1"))
        self.assertIn("CI-004", rules(run(o, l)))

    def test_qualified_alternate_with_link_passes(self):
        o, l = thread()
        o.append(self.ci(single_source=False, qualified_alternate=True))
        l += [self.flag("l-90", "cri-1", "cmp-1"), rec("alternate_for", "l-91", **{"from": "fac-2", "to": "cri-1"})]
        self.assertEqual(run(o, l), [])

    def test_missing_evidence_on_evidenced_step_fails_ci004(self):
        o, l = thread()
        o.append(self.ci(single_source=False, missing_evidence=True))
        l.append(self.flag("l-90", "cri-1", "stp-1"))   # stp-1 has an EvidenceRecord
        self.assertIn("CI-004", rules(run(o, l)))

    def test_missing_evidence_on_bare_step_passes(self):
        o, l = thread()
        o.append(self.ci(single_source=False, missing_evidence=True))
        l.append(self.flag("l-90", "cri-1", "stp-2"))   # stp-2 has none
        self.assertEqual(run(o, l), [])

    def test_unflagged_critical_item_fails_ci004(self):
        o, l = thread()
        o.append(self.ci())
        self.assertIn("CI-004", rules(run(o, l)))


if __name__ == "__main__":
    unittest.main()
