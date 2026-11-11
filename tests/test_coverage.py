#!/usr/bin/env python3
# Handling: Unclassified — public
# SPDX-License-Identifier: Apache-2.0
"""Unit tests for tools/coverage.py using synthetic traces only.

Run:
    python3 -m unittest discover -s tests -v
"""
from __future__ import annotations

import datetime
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import coverage as C  # noqa: E402

SRC = ["https://example.org/synthetic/coverage-test"]
AS_OF = datetime.date(2026, 10, 7)


def _make_synthetic_trace(step_grades: dict[str, str | None]) -> dict:
    """Build an in-memory synthetic trace where step_grades maps step_kind -> evidence_grade (or None for un-evidenced)."""
    objects = [
        {
            "type": "Component",
            "id": "cmp-synth-1",
            "part_number": "TP-100",
            "revision": "A",
            "component_kind": "rotor",
            "evidence_grade": "confirmed",
            "sources": SRC,
            "as_of": AS_OF,
            "lifecycle": "active",
            "synthetic": True,
        },
        {
            "type": "SerialItem",
            "id": "ser-synth-1",
            "serial": "TP-100-0001",
            "evidence_grade": "confirmed",
            "sources": SRC,
            "as_of": AS_OF,
            "lifecycle": "active",
            "synthetic": True,
        },
    ]
    links = [
        {
            "type": "instance_of",
            "id": "lnk-inst-1",
            "from": "ser-synth-1",
            "to": "cmp-synth-1",
            "evidence_grade": "confirmed",
            "sources": SRC,
            "as_of": AS_OF,
            "lifecycle": "active",
            "synthetic": True,
        }
    ]
    for idx, (kind, grade) in enumerate(step_grades.items(), start=1):
        stp_id = f"stp-{idx}"
        objects.append(
            {
                "type": "ProcessStep",
                "id": stp_id,
                "step_kind": kind,
                "evidence_grade": grade or "reported",
                "sources": SRC,
                "as_of": AS_OF,
                "lifecycle": "active",
                "synthetic": True,
            }
        )
        links.append(
            {
                "type": "underwent",
                "id": f"lnk-und-{idx}",
                "from": "ser-synth-1",
                "to": stp_id,
                "sequence": idx,
                "evidence_grade": grade or "reported",
                "sources": SRC,
                "as_of": AS_OF,
                "lifecycle": "active",
                "synthetic": True,
            }
        )
        if grade is not None:
            evd_id = f"evd-{idx}"
            objects.append(
                {
                    "type": "EvidenceRecord",
                    "id": evd_id,
                    "record_kind": "inspection_report",
                    "issuer": "Synthetic Test Lab",
                    "issued_on": AS_OF,
                    "content_hash": "sha256:" + f"{idx:064x}",
                    "evidence_grade": grade,
                    "sources": SRC,
                    "as_of": AS_OF,
                    "lifecycle": "active",
                    "synthetic": True,
                }
            )
            links.append(
                {
                    "type": "evidenced_by",
                    "id": f"lnk-evd-{idx}",
                    "from": stp_id,
                    "to": evd_id,
                    "evidence_grade": grade,
                    "sources": SRC,
                    "as_of": AS_OF,
                    "lifecycle": "active",
                    "synthetic": True,
                }
            )
    return {"objects": objects, "links": links}


class CoverageScoreTests(unittest.TestCase):
    def test_fully_covered_synthetic_trace_scores_one(self) -> None:
        trace = _make_synthetic_trace({k: "confirmed" for k in C.REQUIRED_STEP_KINDS})
        cov = C.score_trace_data(trace, trace_path="examples/full-synth.yaml", trace_label="full-synth")
        self.assertEqual(cov.required_step_score, 1.0)
        self.assertEqual(cov.recorded_step_score, 1.0)
        self.assertEqual(cov.confirmed_kinds, 10)
        self.assertEqual(cov.reported_kinds, 0)
        self.assertEqual(cov.missing_kinds, 0)
        self.assertEqual(len(cov.serials), 1)
        self.assertEqual(cov.serials[0].required_step_score, 1.0)

    def test_empty_synthetic_trace_scores_zero(self) -> None:
        trace = _make_synthetic_trace({})
        cov = C.score_trace_data(trace, trace_path="examples/empty-synth.yaml", trace_label="empty-synth")
        self.assertEqual(cov.required_step_score, 0.0)
        self.assertEqual(cov.recorded_step_score, 0.0)
        self.assertEqual(cov.confirmed_kinds, 0)
        self.assertEqual(cov.reported_kinds, 0)
        self.assertEqual(cov.missing_kinds, 10)
        for st in cov.by_step_kind.values():
            self.assertEqual(st.status, "missing")
            self.assertEqual(st.gap_kind, "not_recorded")

    def test_reported_only_synthetic_trace_scores_half(self) -> None:
        trace = _make_synthetic_trace({k: "reported" for k in C.REQUIRED_STEP_KINDS})
        cov = C.score_trace_data(trace, trace_path="examples/reported-synth.yaml", trace_label="reported-synth")
        self.assertEqual(cov.required_step_score, 0.5)
        self.assertEqual(cov.recorded_step_score, 0.5)
        self.assertEqual(cov.confirmed_kinds, 0)
        self.assertEqual(cov.reported_kinds, 10)
        self.assertEqual(cov.missing_kinds, 0)

    def test_un_evidenced_step_distinguished_from_not_recorded(self) -> None:
        trace = _make_synthetic_trace({"build": "confirmed", "cleaning": None})
        cov = C.score_trace_data(trace, trace_path="examples/gap-synth.yaml", trace_label="gap-synth")
        self.assertEqual(cov.by_step_kind["build"].status, "confirmed")
        self.assertIsNone(cov.by_step_kind["build"].gap_kind)
        self.assertEqual(cov.by_step_kind["cleaning"].status, "missing")
        self.assertEqual(cov.by_step_kind["cleaning"].gap_kind, "un_evidenced_step")
        self.assertEqual(cov.by_step_kind["balancing"].status, "missing")
        self.assertEqual(cov.by_step_kind["balancing"].gap_kind, "not_recorded")
        self.assertEqual(cov.required_step_score, 0.1)
        self.assertEqual(cov.recorded_step_score, 0.5)

    def test_synthetic_turbopump_thread_example_deterministic_score(self) -> None:
        example_path = ROOT / "examples" / "synthetic-turbopump-thread.yaml"
        cov = C.score_trace_file(example_path, ROOT)
        self.assertEqual(cov.required_step_score, 0.8)
        self.assertEqual(cov.confirmed_kinds, 8)
        self.assertEqual(cov.reported_kinds, 0)
        self.assertEqual(cov.missing_kinds, 2)
        self.assertEqual(cov.by_step_kind["finishing"].status, "missing")
        self.assertEqual(cov.by_step_kind["balancing"].status, "missing")
        by_serial = {s.serial_id: s for s in cov.serials}
        self.assertEqual(by_serial["ser-1007"].required_step_score, 0.8)
        self.assertEqual(by_serial["ser-1007"].recorded_step_score, 1.0)
        self.assertEqual(by_serial["ser-1008"].required_step_score, 0.0)
        self.assertEqual(by_serial["ser-1008"].recorded_step_score, 0.0)
        self.assertEqual(by_serial["ser-1008"].by_step_kind["cleaning"].gap_kind, "un_evidenced_step")

    def test_gap_atlas_rendering_and_json_cli(self) -> None:
        traces = [C.score_trace_file(p, ROOT) for p in C.discover_default_traces(ROOT)]
        atlas_md = C.render_gap_atlas(traces)
        self.assertIn("Handling: Unclassified — public", atlas_md)
        self.assertIn("# Public-Evidence Gap Atlas", atlas_md)
        self.assertIn("`synthetic-turbopump-thread`", atlas_md)
        self.assertIn("missing (un-evidenced step)", atlas_md)


if __name__ == "__main__":
    unittest.main()
