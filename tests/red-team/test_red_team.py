#!/usr/bin/env python3
# Handling: Unclassified — public
# SPDX-License-Identifier: Apache-2.0
"""Boundary red-team corpus runner (issue #18, Slice C).

Runs every case in tests/red-team/cases/ through tools/validate.py and asserts
the expected outcome:

  expected: reject  -> validator must emit at least one error carrying the
                       expected RT rule id
  expected: accept  -> validator must emit no errors (false-positive guard)

Every fixture is fictional: invented values only, reserved example.org domain,
no real organization, part or technical parameter. See docs/boundary-red-team.md.

Run:  python3 -m unittest discover -s tests -v   (picked up with the main suite)
"""
import sys
import tempfile
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import validate as V  # noqa: E402

CASES = sorted((Path(__file__).parent / "cases").glob("*.yaml"))


class BoundaryRedTeam(unittest.TestCase):
    def test_all_cases(self):
        self.assertGreater(len(CASES), 0, "corpus must not be empty")
        for case_path in CASES:
            with self.subTest(case=case_path.stem):
                case = yaml.safe_load(case_path.read_text())
                expected = case["expected"]
                with tempfile.NamedTemporaryFile("w", suffix=".yaml", delete=False) as f:
                    yaml.safe_dump({"objects": case["objects"], "links": case.get("links", [])}, f,
                                   allow_unicode=True)
                    tmp = f.name
                try:
                    errors = V.validate(tmp, V.load(ROOT / "schema" / "openchokepoint.yaml"), "public")
                finally:
                    Path(tmp).unlink(missing_ok=True)
                if expected == "reject":
                    rule = case.get("expected_rule", "")
                    hit = [e for e in errors if e.startswith(rule)]
                    self.assertTrue(
                        errors, f"{case_path.stem}: attack NOT caught — smuggled content passed validation")
                    self.assertTrue(
                        hit, f"{case_path.stem}: caught but not by {rule}; errors={errors}")
                else:
                    self.assertEqual(
                        [], errors, f"{case_path.stem}: FALSE POSITIVE — clean record rejected: {errors}")


if __name__ == "__main__":
    unittest.main()
