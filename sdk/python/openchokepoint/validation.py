# Handling: Unclassified — public
# SPDX-License-Identifier: Apache-2.0
"""Validation through the project's own validator.

The rules live in one place, tools/validate.py. This module loads that file and
returns its findings as structured issues, so the SDK can never drift from CI.
"""
from __future__ import annotations

import importlib.util
import os
import re
from dataclasses import dataclass
from pathlib import Path

from .registry import find_root

RULE_ID = re.compile(r"^([A-Z]{2}-\d{3})\s+(.*)$")
_CACHE: dict[Path, object] = {}


@dataclass(frozen=True)
class Issue:
    """One validator finding. `rule` is the stable rule ID (for example EV-001) when the validator gives one."""

    rule: str | None
    message: str

    def __str__(self) -> str:
        return f"{self.rule} {self.message}" if self.rule else self.message


def _validator(root: Path):
    root = root.resolve()
    if root not in _CACHE:
        spec = importlib.util.spec_from_file_location("openchokepoint_validate", root / "tools" / "validate.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        _CACHE[root] = module
    return _CACHE[root]


def validate(path: str | os.PathLike, tier: str = "public", root: str | os.PathLike | None = None) -> list[Issue]:
    """Validate one instance file. Returns an empty list when the file passes.

    tier: "public" (default, the rules this repository's CI applies) or "private".
    root: the OpenChokepoint checkout; found automatically when omitted (see find_root).
    """
    if tier not in ("public", "private"):
        raise ValueError("tier must be 'public' or 'private'")
    base = Path(root) if root else find_root()
    v = _validator(base)
    onto = v.load(base / "schema" / "openchokepoint.yaml")
    issues = []
    for err in v.validate(Path(path), onto, tier):
        m = RULE_ID.match(err)
        issues.append(Issue(m.group(1), m.group(2)) if m else Issue(None, err))
    return issues
