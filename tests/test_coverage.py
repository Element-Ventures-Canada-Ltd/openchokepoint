#!/usr/bin/env python3
# Handling: Unclassified — public
# SPDX-License-Identifier: Apache-2.0
"""Tests for tools/coverage.py. Standard library only (unittest); PyYAML is already required by the validator.

Run:  python3 -m unittest discover -s tests -v

Every fixture is invented: fictional names and identifiers on the reserved example.org domain,
no real organization, part or technical parameter.
"""
import contextlib
import datetime
import io
import sys
import tempfile
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import coverage as C  # noqa: E402

SRC = ["https://example.org/synthetic/test"]
BASE = {
    "evidence_grade": "confirmed",
    "sources": SRC,
    "as_of": datetime.date(2026, 10, 7),
    "lifecycle": "active",
    "synthetic": True,
}


def obj(rtype, rid, **kw):
    record = {"type": rtype, "id": rid, **BASE}
    record.update(kw)
    return record


def link(ltype, lid, frm, to, **kw):
    record = {"type": ltype, "id": lid, "from": frm, "to": to, **BASE}
    record.update(kw)
    return record


def evidence(rid, grade="confirmed"):
    return obj(
        "EvidenceRecord",
        rid,
        record_kind="inspection_report",
        issuer="Example Issuer",
        issued_on=datetime.date(2026, 4, 1),
        content_hash="sha256:" + "0" * 64,
        evidence_grade=grade,
    )


def trace(step_kinds, evidence_grade="confirmed", with_records=True):
    """One serial item going through `step_kinds`, each with one evidence record."""
    objects = [obj("SerialItem", "ser-1", name="R-1", serial="R-1")]
    links = []
    for index, kind in enumerate(step_kinds, start=1):
        step_id = f"stp-{index}"
        objects.append(obj("ProcessStep", step_id, step_kind=kind))
        links.append(link("underwent", f"lnk-u{index}", "ser-1", step_id, sequence=index))
        if with_records:
            evidence_id = f"evd-{index}"
            objects.append(evidence(evidence_id, grade=evidence_grade))
            links.append(link("evidenced_by", f"lnk-e{index}", step_id, evidence_id))
    return {"objects": objects, "links": links}


def write(tmpdir, name, document):
    path = Path(tmpdir) / name
    path.write_text(yaml.safe_dump(document, sort_keys=False), encoding="utf-8")
    return path


class Score(unittest.TestCase):
    def score(self, document):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = write(tmpdir, "trace.yaml", document)
            return C.score_trace(path)["traces"][0]

    def test_fully_covered_trace_scores_one(self):
        result = self.score(trace(C.REQUIRED_STEP_KINDS))
        self.assertEqual(result["coverage"], 1.0)
        self.assertEqual(result["recorded_coverage"], 1.0)
        self.assertEqual(result["step_kinds_missing"], [])

    def test_empty_trace_scores_zero(self):
        result = self.score(trace([]))
        self.assertEqual(result["coverage"], 0.0)
        self.assertEqual(result["recorded_coverage"], 0.0)
        self.assertEqual(len(result["step_kinds_missing"]), len(C.REQUIRED_STEP_KINDS))

    def test_only_reported_evidence_scores_half(self):
        result = self.score(trace(C.REQUIRED_STEP_KINDS, evidence_grade="reported"))
        self.assertEqual(result["coverage"], 0.5)
        self.assertEqual(result["recorded_coverage"], 0.5)
        for kind in C.REQUIRED_STEP_KINDS:
            self.assertEqual(result["required"][kind]["strength"], "reported")

    def test_steps_without_evidence_records_are_gaps(self):
        result = self.score(trace(C.REQUIRED_STEP_KINDS, with_records=False))
        self.assertEqual(result["coverage"], 0.0)
        self.assertEqual(result["step_kinds_present"], sorted(C.REQUIRED_STEP_KINDS))
        for kind in C.REQUIRED_STEP_KINDS:
            entry = result["required"][kind]
            self.assertEqual(entry["strength"], "missing")
            self.assertTrue(entry["present"], "a step that happened but is unevidenced must be present, not absent")

    def test_one_missing_kind_costs_one_share(self):
        kinds = tuple(k for k in C.REQUIRED_STEP_KINDS if k != "balancing")
        result = self.score(trace(kinds))
        self.assertEqual(result["coverage"], round(1 - 1 / len(C.REQUIRED_STEP_KINDS), 4))
        self.assertEqual(result["step_kinds_missing"], ["balancing"])

    def test_confirmed_outranks_reported_for_the_same_kind(self):
        document = trace([])
        document["objects"].append(obj("ProcessStep", "stp-a", step_kind="inspection"))
        document["objects"].append(obj("ProcessStep", "stp-b", step_kind="inspection"))
        document["objects"].append(evidence("evd-a", grade="reported"))
        document["objects"].append(evidence("evd-b", grade="confirmed"))
        document["links"].append(link("underwent", "lnk-a", "ser-1", "stp-a", sequence=1))
        document["links"].append(link("underwent", "lnk-b", "ser-1", "stp-b", sequence=2))
        document["links"].append(link("evidenced_by", "lnk-ea", "stp-a", "evd-a"))
        document["links"].append(link("evidenced_by", "lnk-eb", "stp-b", "evd-b"))
        result = self.score(document)
        self.assertEqual(result["required"]["inspection"]["strength"], "confirmed")
        self.assertEqual(result["required"]["inspection"]["evidence"], "evd-b")


class Determinism(unittest.TestCase):
    def test_same_file_scores_the_same_twice(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = write(tmpdir, "trace.yaml", trace(C.REQUIRED_STEP_KINDS))
            first = C.score_trace(path)
            second = C.score_trace(path)
            self.assertEqual(first, second)

    def test_atlas_rendering_is_stable(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = write(tmpdir, "trace.yaml", trace(C.REQUIRED_STEP_KINDS))
            results = [C.score_trace(path)]
            self.assertEqual(C.render_atlas(results), C.render_atlas(results))

    def test_atlas_lists_every_required_kind_once(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = write(tmpdir, "trace.yaml", trace([]))
            rendered = C.render_atlas([C.score_trace(path)])
            headers = [line for line in rendered.splitlines() if line.startswith("| Trace | Serial |")]
            self.assertEqual(len(headers), 1, "the atlas needs exactly one column header row")
            for kind in C.REQUIRED_STEP_KINDS:
                self.assertEqual(headers[0].count(kind), 1, f"{kind} missing or duplicated in the atlas header")


class AtlasCommand(unittest.TestCase):
    def run_main(self, argv):
        """Call the CLI with its chatter captured, so a passing run stays quiet."""
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            return C.main(argv)

    def test_write_then_check_is_clean(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = write(tmpdir, "trace.yaml", trace(C.REQUIRED_STEP_KINDS))
            atlas = Path(tmpdir) / "gap-atlas.md"
            self.assertEqual(self.run_main([str(path), "--write-gap-atlas", str(atlas)]), 0)
            self.assertTrue(atlas.is_file())
            self.assertEqual(self.run_main([str(path), "--check-gap-atlas", str(atlas)]), 0)

    def test_check_reports_a_stale_atlas(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = write(tmpdir, "trace.yaml", trace(C.REQUIRED_STEP_KINDS))
            atlas = Path(tmpdir) / "gap-atlas.md"
            self.run_main([str(path), "--write-gap-atlas", str(atlas)])
            atlas.write_text("stale\n", encoding="utf-8")
            self.assertEqual(self.run_main([str(path), "--check-gap-atlas", str(atlas)]), 1)

    def test_missing_trace_is_a_usage_error(self):
        self.assertEqual(self.run_main([str(ROOT / "no-such-trace.yaml")]), 2)


class RepoExamples(unittest.TestCase):
    """The checked-in examples must stay scoreable, and the gap atlas must match them."""

    def test_gap_atlas_is_current(self):
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(C.main(["--check-gap-atlas", str(C.DEFAULT_ATLAS)]), 0)

    def test_turbopump_example_reports_a_number_for_both_serials(self):
        path = ROOT / "examples" / "synthetic-turbopump-thread.yaml"
        traces = C.score_trace(path)["traces"]
        self.assertEqual(len(traces), 2)
        by_serial = {t["serial"]: t for t in traces}
        self.assertIn("R-100-0007", by_serial)
        self.assertIn("R-100-0008", by_serial)
        # R-100-0008's cleaning step exists and has no evidence record: a gap, not a zero-length trace.
        self.assertTrue(by_serial["R-100-0008"]["required"]["cleaning"]["present"])
        self.assertEqual(by_serial["R-100-0008"]["required"]["cleaning"]["strength"], "missing")


if __name__ == "__main__":
    unittest.main()
