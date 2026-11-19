#!/usr/bin/env python3
# Handling: Unclassified — public
"""Pure-function public-evidence coverage scorer and gap atlas generator.

Measures the completeness of the *public record* across ProcessStep kinds
defined in schema/openchokepoint.yaml. Never scores real organizations'
technical capability and performs zero network access.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parent.parent

REQUIRED_STEP_KINDS: tuple[str, ...] = (
    "build",
    "stress_relief",
    "hip",
    "heat_treatment",
    "machining",
    "finishing",
    "cleaning",
    "inspection",
    "balancing",
    "assembly",
)

GRADE_WEIGHTS: dict[str, float] = {
    "confirmed": 1.0,
    "reported": 0.5,
    "inferred": 0.25,
}

STATUS_BADGES: dict[str, str] = {
    "confirmed": "confirmed (1.0)",
    "reported": "reported (0.5)",
    "inferred": "inferred (0.25)",
    "unverified": "no evidence (0.0)",
    "missing": "missing (0.0)",
}


def score_trace(doc: dict[str, Any]) -> dict[str, Any]:
    """Compute public-evidence coverage for a parsed YAML trace dictionary.

    Pure function of the parsed YAML structure; performs no I/O or network calls.
    """
    objects = doc.get("objects") or []
    links = doc.get("links") or []

    steps_by_id: dict[str, str] = {}
    evidence_grade_by_id: dict[str, str] = {}
    present_step_kinds: set[str] = set()

    for obj in objects:
        if not isinstance(obj, dict):
            continue
        otype = obj.get("type")
        oid = obj.get("id")
        if not oid:
            continue
        if otype == "ProcessStep":
            kind = obj.get("step_kind")
            if isinstance(kind, str):
                steps_by_id[oid] = kind
                present_step_kinds.add(kind)
        elif otype == "EvidenceRecord":
            grade = obj.get("evidence_grade")
            if isinstance(grade, str):
                evidence_grade_by_id[oid] = grade

    best_grade_by_kind: dict[str, str] = {}
    for lnk in links:
        if not isinstance(lnk, dict):
            continue
        if lnk.get("type") != "evidenced_by":
            continue
        step_id = lnk.get("from")
        evd_id = lnk.get("to")
        if step_id not in steps_by_id or evd_id not in evidence_grade_by_id:
            continue
        kind = steps_by_id[step_id]
        evd_grade = evidence_grade_by_id[evd_id]
        prev = best_grade_by_kind.get(kind)
        if GRADE_WEIGHTS.get(evd_grade, 0.0) > GRADE_WEIGHTS.get(prev or "", 0.0):
            best_grade_by_kind[kind] = evd_grade

    by_kind: dict[str, dict[str, Any]] = {}
    total_points = 0.0
    for kind in REQUIRED_STEP_KINDS:
        if kind in best_grade_by_kind:
            status = best_grade_by_kind[kind]
            score = GRADE_WEIGHTS.get(status, 0.0)
        elif kind in present_step_kinds:
            status = "unverified"
            score = 0.0
        else:
            status = "missing"
            score = 0.0
        total_points += score
        by_kind[kind] = {"status": status, "score": score}

    overall_pct = round((total_points / len(REQUIRED_STEP_KINDS)) * 100.0, 2)
    return {
        "overall_score_pct": overall_pct,
        "points": round(total_points, 2),
        "max_points": float(len(REQUIRED_STEP_KINDS)),
        "by_kind": by_kind,
    }


def score_file(path: Path) -> dict[str, Any]:
    """Load a YAML trace file from disk and return its coverage report."""
    with path.open("r", encoding="utf-8") as fh:
        doc = yaml.safe_load(fh) or {}
    result = score_trace(doc)
    result["path"] = path.relative_to(ROOT).as_posix() if path.is_relative_to(ROOT) else str(path)
    return result


def discover_traces(root: Path = ROOT) -> list[Path]:
    """Return all YAML trace files under data/digital-thread/ and examples/."""
    candidates: list[Path] = []
    for base in (root / "data" / "digital-thread", root / "examples"):
        if base.exists():
            candidates.extend(
                p for p in sorted(base.rglob("*.yaml")) if p.name != "provenance.yaml"
            )
    return candidates


def render_gap_atlas(root: Path = ROOT) -> str:
    """Generate the Markdown gap atlas table across all discovered traces."""
    traces = discover_traces(root)
    reports = [score_file(p) for p in traces]

    lines = [
        "# Public-Evidence Gap Atlas",
        "",
        "Generated automatically by `python tools/coverage.py --atlas --write docs/gap-atlas.md`.",
        "",
        "This table measures the completeness of the **public record** across the 10",
        "required `ProcessStep` kinds in `schema/openchokepoint.yaml`. It does **not**",
        "score any organization's technical capability.",
        "",
        "| Trace | Score | " + " | ".join(REQUIRED_STEP_KINDS) + " |",
        "| :--- | :---: | " + " | ".join([":---:"] * len(REQUIRED_STEP_KINDS)) + " |",
    ]

    for rep in reports:
        cells = [STATUS_BADGES[rep["by_kind"][k]["status"]] for k in REQUIRED_STEP_KINDS]
        lines.append(
            f"| `{rep['path']}` | **{rep['overall_score_pct']:.1f}%** ({rep['points']:.1f}/{rep['max_points']:.0f}) | "
            + " | ".join(cells)
            + " |"
        )

    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Score public-evidence coverage for digital-thread traces.")
    parser.add_argument("trace", nargs="?", help="Path to a trace YAML file to score.")
    parser.add_argument("--json", action="store_true", help="Output JSON instead of human-readable text.")
    parser.add_argument("--atlas", action="store_true", help="Generate the cross-trace gap atlas.")
    parser.add_argument("--write", help="Write gap atlas Markdown to this path (use with --atlas).")
    args = parser.parse_args()

    if args.atlas:
        atlas_md = render_gap_atlas(ROOT)
        if args.write:
            out_path = Path(args.write)
            if not out_path.is_absolute():
                out_path = ROOT / out_path
            out_path.parent.mkdir(parents=True, exist_ok=True)
            out_path.write_text(atlas_md, encoding="utf-8", newline="\n")
        else:
            print(atlas_md)
        return 0

    if not args.trace:
        parser.error("Specify a trace YAML file or --atlas.")

    report = score_file(Path(args.trace).resolve())
    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print(f"Trace: {report['path']}")
        print(f"Overall Public-Evidence Coverage: {report['overall_score_pct']:.1f}% ({report['points']:.1f}/{report['max_points']:.0f})")
        for kind, info in report["by_kind"].items():
            print(f"  - {kind:15s}: {info['status']} ({info['score']:.2f})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
