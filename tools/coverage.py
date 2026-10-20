#!/usr/bin/env python3
# Handling: Unclassified — public
# SPDX-License-Identifier: Apache-2.0
"""Public-evidence coverage score and gap atlas for digital-thread traces.

A trace shows where the public record runs out. This tool turns that into a
number and a table, so two traces can be compared and a gap can be cited.

Usage:
    python3 tools/coverage.py [--json] [trace.yaml ...]
    python3 tools/coverage.py --write-gap-atlas [PATH]
    python3 tools/coverage.py --check-gap-atlas [PATH]

Defaults to every trace under examples/ and data/digital-thread/.

The score is a pure function of the YAML: same file, same number. No network,
no clock, no randomness. See docs/coverage-score.md for the method and for why
these step kinds are the required ones.

Exit codes: 0 success, 1 stale gap atlas (--check-gap-atlas), 2 usage error.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_ATLAS = ROOT / "docs" / "gap-atlas.md"
TRACE_DIRS = (ROOT / "data" / "digital-thread", ROOT / "examples")

# The required public-evidence steps for a flight-critical rotating part.
# Policy choice, not a schema rule — argued in docs/coverage-score.md.
REQUIRED_STEP_KINDS = (
    "build",
    "heat_treatment",
    "machining",
    "cleaning",
    "inspection",
    "balancing",
)

# Weight per evidence strength. A pass on a reported record is worth half a pass
# on a confirmed one: the record is named, but nobody has checked it.
STRENGTH_WEIGHT = {"confirmed": 1.0, "reported": 0.5, "missing": 0.0}
STRENGTH_RANK = {"missing": 0, "reported": 1, "confirmed": 2}


def load(path: Path) -> dict:
    with open(path, encoding="utf-8") as fh:
        return yaml.safe_load(fh) or {}


def index(document: dict) -> tuple[dict, dict]:
    """Return (records by id, outgoing links by (from, type))."""
    records = {}
    for rec in document.get("objects") or []:
        records[rec.get("id")] = rec
    for link in document.get("links") or []:
        records[link.get("id")] = link

    edges: dict[tuple, list] = {}
    for link in document.get("links") or []:
        edges.setdefault((link.get("from"), link.get("type")), []).append(link.get("to"))
    return records, edges


def evidence_strength(step_id, records, edges) -> tuple[str, str | None]:
    """Strongest evidence attached to one step, and the record that carries it."""
    best, best_id = "missing", None
    for target in edges.get((step_id, "evidenced_by"), []):
        record = records.get(target)
        if record is None:
            continue
        grade = record.get("evidence_grade")
        strength = "confirmed" if grade == "confirmed" else "reported"
        if STRENGTH_RANK[strength] > STRENGTH_RANK[best]:
            best, best_id = strength, target
    return best, best_id


def steps_of(serial_id, records, edges) -> list[dict]:
    """Ordered process steps reachable from one serial item."""
    steps = []
    for target in edges.get((serial_id, "underwent"), []):
        step = records.get(target)
        if step is None or step.get("type") != "ProcessStep":
            continue
        steps.append(step)
    # Order by the link's sequence where present (synthetic traces carry it);
    # fall back to id so the result stays deterministic on real public links.
    sequenced = []
    for link in _underwent_links(serial_id, records):
        sequenced.append((link.get("sequence", sys.maxsize), link.get("to")))
    order = {target: rank for rank, (_, target) in enumerate(sorted(sequenced))}
    return sorted(steps, key=lambda step: (order.get(step.get("id"), sys.maxsize), str(step.get("id"))))


def _underwent_links(serial_id, records) -> list[dict]:
    return [
        rec
        for rec in records.values()
        if rec.get("type") == "underwent" and rec.get("from") == serial_id
    ]


def score_trace(path: Path) -> dict:
    """Coverage of one trace file, per serial item it contains."""
    document = load(path)
    records, edges = index(document)

    serials = sorted(
        (rec for rec in document.get("objects") or [] if rec.get("type") == "SerialItem"),
        key=lambda rec: str(rec.get("id")),
    )
    traces = []
    for serial in serials:
        steps = steps_of(serial.get("id"), records, edges)
        by_kind: dict[str, list[dict]] = {}
        for step in steps:
            kind = step.get("step_kind")
            strength, evidence_id = evidence_strength(step.get("id"), records, edges)
            by_kind.setdefault(kind, []).append(
                {"step": step.get("id"), "strength": strength, "evidence": evidence_id}
            )

        required = {}
        for kind in REQUIRED_STEP_KINDS:
            entries = by_kind.get(kind, [])
            if not entries:
                required[kind] = {"strength": "missing", "step": None, "evidence": None, "present": False}
                continue
            strongest = max(entries, key=lambda entry: STRENGTH_RANK[entry["strength"]])
            required[kind] = {
                "strength": strongest["strength"],
                "step": strongest["step"],
                "evidence": strongest["evidence"],
                "present": True,
            }

        total = sum(STRENGTH_WEIGHT[required[kind]["strength"]] for kind in REQUIRED_STEP_KINDS)
        coverage = total / len(REQUIRED_STEP_KINDS)

        present_kinds = sorted(kind for kind in by_kind if kind)
        recorded_total = sum(
            STRENGTH_WEIGHT[max((e["strength"] for e in by_kind[kind]), key=lambda s: STRENGTH_RANK[s])]
            for kind in present_kinds
        )
        recorded = recorded_total / len(present_kinds) if present_kinds else 0.0

        traces.append(
            {
                "trace": path.name,
                "path": _display(path),
                "serial": serial.get("name") or serial.get("id"),
                "serial_id": serial.get("id"),
                "coverage": round(coverage, 4),
                "recorded_coverage": round(recorded, 4),
                "required": required,
                "step_kinds_present": present_kinds,
                "step_kinds_missing": [k for k in REQUIRED_STEP_KINDS if hard_missing(required, k)],
            }
        )
    return {"file": _display(path), "traces": traces}


def hard_missing(required: dict, kind: str) -> bool:
    entry = required[kind]
    return entry["strength"] == "missing" and not entry["present"]


def _display(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def default_traces() -> list[Path]:
    found: list[Path] = []
    for directory in TRACE_DIRS:
        if directory.is_dir():
            found.extend(sorted(directory.rglob("*.yaml")))
    return found


def render_atlas(results: list[dict]) -> str:
    """The gap atlas as Markdown. Deterministic: no timestamps, sorted input."""
    lines = [
        "# Gap atlas",
        "",
        "Handling: Unclassified — public",
        "",
        "Generated by `python3 tools/coverage.py --write-gap-atlas`. Do not edit by hand;",
        "re-run the command. Method: [`docs/coverage-score.md`](coverage-score.md).",
        "",
        "Each row is one serial item. `confirmed` means a record is named and graded",
        "confirmed, `reported` means only a reported record names it, `none` means the",
        "step is absent or unevidenced. A lower score is a shorter public record, not a",
        "worse part: the tool measures the record, never a supplier.",
        "",
        "| Trace | Serial | " + " | ".join(REQUIRED_STEP_KINDS) + " | Score |",
        "| :-- | :-- | " + " | ".join(":--" for _ in REQUIRED_STEP_KINDS) + " | --: |",
    ]
    for result in results:
        for trace in result["traces"]:
            cells = []
            for kind in REQUIRED_STEP_KINDS:
                entry = trace["required"][kind]
                if entry["strength"] == "confirmed":
                    cells.append("confirmed")
                elif entry["strength"] == "reported":
                    cells.append("reported")
                else:
                    cells.append("none")
            lines.append(
                "| `{file}` | `{serial}` | {cells} | {score} |".format(
                    file=result["file"],
                    serial=trace["serial"],
                    cells=" | ".join(cells),
                    score=_percent(trace["coverage"]),
                )
            )
    lines.append("")
    return "\n".join(lines)


def _percent(value: float) -> str:
    return f"{value * 100:.1f}%"


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        description="Score public-evidence coverage and render the gap atlas.",
        add_help=True,
    )
    parser.add_argument("traces", nargs="*", help="trace YAML files (default: examples/ and data/digital-thread/)")
    parser.add_argument("--json", action="store_true", help="machine-readable output")
    parser.add_argument("--write-gap-atlas", nargs="?", const=str(DEFAULT_ATLAS), metavar="PATH")
    parser.add_argument("--check-gap-atlas", nargs="?", const=str(DEFAULT_ATLAS), metavar="PATH")
    args = parser.parse_args(argv)

    targets = [Path(t) for t in args.traces] if args.traces else default_traces()
    if not targets:
        print("no trace files found", file=sys.stderr)
        return 2
    missing = [t for t in targets if not t.is_file()]
    if missing:
        for t in missing:
            print(f"no such trace: {t}", file=sys.stderr)
        return 2

    results = [score_trace(path) for path in targets]

    if args.write_gap_atlas or args.check_gap_atlas:
        target = Path(args.write_gap_atlas or args.check_gap_atlas)
        rendered = render_atlas(results)
        if args.check_gap_atlas:
            existing = target.read_text(encoding="utf-8") if target.is_file() else ""
            if existing != rendered:
                print(f"STALE {target}: re-run --write-gap-atlas", file=sys.stderr)
                return 1
            print(f"OK   {target}")
            return 0
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(rendered, encoding="utf-8", newline="\n")
        print(f"wrote {target}")
        return 0

    if args.json:
        print(json.dumps(results, indent=2, sort_keys=True))
        return 0

    for result in results:
        for trace in result["traces"]:
            print(f"{result['file']}  {trace['serial']}")
            print(f"  coverage: {_percent(trace['coverage'])} of required public evidence")
            print(f"  recorded coverage: {_percent(trace['recorded_coverage'])} of the steps this trace shows")
            for kind in REQUIRED_STEP_KINDS:
                entry = trace["required"][kind]
                note = ""
                if entry["strength"] == "missing":
                    note = " (step absent)" if not entry["present"] else " (step present, no evidence record)"
                evidence = f" <- {entry['evidence']}" if entry["evidence"] else ""
                print(f"    {kind:<16} {entry['strength']}{note}{evidence}")
            gaps = trace["step_kinds_missing"]
            if gaps:
                print(f"  gaps: {', '.join(gaps)}")
            print()
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
