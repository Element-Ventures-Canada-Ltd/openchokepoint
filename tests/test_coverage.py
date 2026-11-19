# Handling: Unclassified — public
"""Unit tests for tools/coverage.py using synthetic traces only."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

import coverage  # noqa: E402


def _make_synthetic_trace(step_grades: dict[str, str | None]) -> dict:
    """Build a minimal synthetic trace dict mapping step_kind -> evidence_grade (or None for unlinked)."""
    objects = []
    links = []
    for idx, (kind, grade) in enumerate(step_grades.items(), start=1):
        step_id = f"stp-{idx}"
        objects.append({"type": "ProcessStep", "id": step_id, "step_kind": kind, "synthetic": True})
        if grade is not None:
            evd_id = f"evd-{idx}"
            objects.append({"type": "EvidenceRecord", "id": evd_id, "evidence_grade": grade, "synthetic": True})
            links.append({"type": "evidenced_by", "id": f"lnk-{idx}", "from": step_id, "to": evd_id, "synthetic": True})
    return {"objects": objects, "links": links}


class CoverageTests(unittest.TestCase):
    def test_fully_covered_confirmed_trace_scores_100(self) -> None:
        trace = _make_synthetic_trace({k: "confirmed" for k in coverage.REQUIRED_STEP_KINDS})
        res = coverage.score_trace(trace)
        self.assertEqual(res["overall_score_pct"], 100.0)
        self.assertEqual(res["points"], 10.0)
        for kind in coverage.REQUIRED_STEP_KINDS:
            self.assertEqual(res["by_kind"][kind]["status"], "confirmed")

    def test_empty_trace_scores_zero(self) -> None:
        res = coverage.score_trace({"objects": [], "links": []})
        self.assertEqual(res["overall_score_pct"], 0.0)
        self.assertEqual(res["points"], 0.0)
        for kind in coverage.REQUIRED_STEP_KINDS:
            self.assertEqual(res["by_kind"][kind]["status"], "missing")

    def test_reported_only_trace_scores_50_percent(self) -> None:
        trace = _make_synthetic_trace({k: "reported" for k in coverage.REQUIRED_STEP_KINDS})
        res = coverage.score_trace(trace)
        self.assertEqual(res["overall_score_pct"], 50.0)
        self.assertEqual(res["points"], 5.0)
        for kind in coverage.REQUIRED_STEP_KINDS:
            self.assertEqual(res["by_kind"][kind]["status"], "reported")

    def test_step_without_evidence_scores_zero_and_marks_unverified(self) -> None:
        trace = _make_synthetic_trace({"build": None, "machining": "confirmed"})
        res = coverage.score_trace(trace)
        self.assertEqual(res["overall_score_pct"], 10.0)
        self.assertEqual(res["by_kind"]["build"]["status"], "unverified")
        self.assertEqual(res["by_kind"]["machining"]["status"], "confirmed")
        self.assertEqual(res["by_kind"]["assembly"]["status"], "missing")

    def test_synthetic_turbopump_example_is_deterministic(self) -> None:
        path = ROOT / "examples" / "synthetic-turbopump-thread.yaml"
        first = coverage.score_file(path)
        second = coverage.score_file(path)
        self.assertEqual(first, second)
        self.assertEqual(first["overall_score_pct"], 80.0)
        self.assertEqual(first["points"], 8.0)


if __name__ == "__main__":
    unittest.main()
