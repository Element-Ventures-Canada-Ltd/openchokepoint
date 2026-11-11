#!/usr/bin/env python3
# Handling: Unclassified — public
# SPDX-License-Identifier: Apache-2.0
"""Tests for apps/chokepoint-explorer/explore.py (--format json and default markdown output)."""
import io
import json
import importlib.util
import sys
import unittest
from contextlib import redirect_stdout
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EXPLORE_PATH = ROOT / "apps" / "chokepoint-explorer" / "explore.py"
spec = importlib.util.spec_from_file_location("explore", EXPLORE_PATH)
explore = importlib.util.module_from_spec(spec)
sys.modules["explore"] = explore
spec.loader.exec_module(explore)


class ExplorerJsonFormatTests(unittest.TestCase):
    def test_format_json_on_synthetic_example_prints_valid_json(self):
        buf = io.StringIO()
        with redirect_stdout(buf):
            rc = explore.main([str(ROOT / "examples" / "synthetic-example.yaml"), "--format", "json"])
        self.assertEqual(rc, 0)
        parsed = json.loads(buf.getvalue())
        self.assertEqual(parsed["file"], "synthetic-example.yaml")
        self.assertTrue(parsed["validation"]["passed"])
        self.assertEqual(parsed["validation"]["tier"], "public")
        self.assertIn("jurisdiction_of_control", parsed)
        self.assertIn("capabilities", parsed)
        self.assertGreater(parsed["counts"]["objects"], 0)

    def test_format_json_on_turbopump_thread_includes_threads_gaps_and_critical_items(self):
        out, issues = explore.report(
            ROOT / "examples" / "synthetic-turbopump-thread.yaml", fmt="json"
        )
        self.assertEqual(issues, [])
        parsed = json.loads(out)
        self.assertEqual(len(parsed["digital_threads"]), 2)
        self.assertEqual(len(parsed["evidence_gaps"]), 1)
        self.assertEqual(parsed["evidence_gaps"][0]["id"], "stp-1806")
        self.assertEqual(len(parsed["declared_critical_items"]), 3)

    def test_default_markdown_output_is_unchanged(self):
        buf = io.StringIO()
        with redirect_stdout(buf):
            rc = explore.main([str(ROOT / "examples" / "synthetic-example.yaml")])
        self.assertEqual(rc, 0)
        md = buf.getvalue()
        self.assertTrue(md.startswith("Handling: Unclassified — public\n\n# Chokepoint explorer: `synthetic-example.yaml`"))
        self.assertIn("## Jurisdiction of control", md)
        self.assertIn("## Capabilities", md)


if __name__ == "__main__":
    unittest.main()
