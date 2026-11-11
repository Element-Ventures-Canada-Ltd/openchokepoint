#!/usr/bin/env python3
# Handling: Unclassified — public
# SPDX-License-Identifier: Apache-2.0
"""Compute public-evidence coverage scores and generate the gap atlas for OpenChokepoint digital-thread traces.

Usage:
    python3 tools/coverage.py [--json] [trace.yaml ...]
    python3 tools/coverage.py --atlas [trace.yaml ...]
    python3 tools/coverage.py --write-atlas [output.md] [trace.yaml ...]

Offline only: reads local YAML traces under data/digital-thread/ and examples/ using PyYAML
and the Python standard library. Never makes network requests.
"""
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Iterable

import yaml

ROOT = Path(__file__).resolve().parent.parent

# The 10 canonical ProcessStep.step_kind values defined in schema/openchokepoint.yaml
# for a flight-critical rotating part digital thread.
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
    "missing": 0.0,
}

GRADE_RANK: dict[str, int] = {
    "confirmed": 2,
    "reported": 1,
    "missing": 0,
}


@dataclass(frozen=True)
class StepKindStatus:
    step_kind: str
    status: str  # "confirmed" | "reported" | "missing"
    weight: float
    gap_kind: str | None  # None | "un_evidenced_step" | "not_recorded"
    step_ids: list[str] = field(default_factory=list)
    evidence_ids: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class SerialCoverage:
    serial_id: str
    serial_name: str
    component_id: str | None
    required_step_score: float
    recorded_step_score: float
    recorded_steps_count: int
    evidenced_steps_count: int
    confirmed_kinds: int
    reported_kinds: int
    missing_kinds: int
    by_step_kind: dict[str, StepKindStatus]


@dataclass(frozen=True)
class TraceCoverage:
    trace_path: str
    trace_label: str
    is_synthetic: bool
    required_step_score: float
    recorded_step_score: float
    confirmed_kinds: int
    reported_kinds: int
    missing_kinds: int
    by_step_kind: dict[str, StepKindStatus]
    serials: list[SerialCoverage]


def load_yaml(path: Path) -> dict:
    with open(path, encoding="utf-8") as fh:
        return yaml.safe_load(fh) or {}


def _normalize_grade(raw_grade: str | None) -> str:
    if raw_grade == "confirmed":
        return "confirmed"
    if raw_grade == "reported":
        return "reported"
    return "missing"


def _weaker_grade(grade_a: str, grade_b: str) -> str:
    """An evidenced step's effective grade is bounded by both the ProcessStep and its EvidenceRecord."""
    ga = _normalize_grade(grade_a)
    gb = _normalize_grade(grade_b)
    return ga if GRADE_RANK[ga] <= GRADE_RANK[gb] else gb


def _stronger_grade(grade_a: str, grade_b: str) -> str:
    ga = _normalize_grade(grade_a)
    gb = _normalize_grade(grade_b)
    return ga if GRADE_RANK[ga] >= GRADE_RANK[gb] else gb


def evaluate_steps(
    steps: Iterable[dict],
    evidenced_by_links: list[dict],
    evidence_by_id: dict[str, dict],
) -> tuple[dict[str, StepKindStatus], float, float, int, int]:
    """Evaluate coverage across a set of ProcessStep objects."""
    steps_list = [s for s in steps if s.get("type") == "ProcessStep"]
    ev_links_by_step: dict[str, list[str]] = {}
    for link in evidenced_by_links:
        if link.get("type") == "evidenced_by":
            ev_links_by_step.setdefault(link.get("from", ""), []).append(link.get("to", ""))

    # Track per-step effective grade and whether each recorded step has at least one valid EvidenceRecord
    recorded_count = len(steps_list)
    evidenced_count = 0
    recorded_weight_sum = 0.0

    steps_by_kind: dict[str, list[dict]] = {k: [] for k in REQUIRED_STEP_KINDS}
    for step in steps_list:
        sk = step.get("step_kind")
        if sk in steps_by_kind:
            steps_by_kind[sk].append(step)

        step_id = step.get("id", "")
        linked_ev_ids = [eid for eid in ev_links_by_step.get(step_id, []) if eid in evidence_by_id]
        if linked_ev_ids:
            evidenced_count += 1
            best_ev_grade = "missing"
            for eid in linked_ev_ids:
                best_ev_grade = _stronger_grade(best_ev_grade, evidence_by_id[eid].get("evidence_grade"))
            eff_grade = _weaker_grade(step.get("evidence_grade"), best_ev_grade)
            recorded_weight_sum += GRADE_WEIGHTS[eff_grade]

    by_kind: dict[str, StepKindStatus] = {}
    for kind in REQUIRED_STEP_KINDS:
        kind_steps = steps_by_kind[kind]
        if not kind_steps:
            by_kind[kind] = StepKindStatus(
                step_kind=kind,
                status="missing",
                weight=0.0,
                gap_kind="not_recorded",
                step_ids=[],
                evidence_ids=[],
            )
            continue

        best_kind_grade = "missing"
        all_step_ids: list[str] = []
        all_ev_ids: list[str] = []
        for step in kind_steps:
            sid = step.get("id", "")
            all_step_ids.append(sid)
            linked_ev_ids = [eid for eid in ev_links_by_step.get(sid, []) if eid in evidence_by_id]
            for eid in linked_ev_ids:
                if eid not in all_ev_ids:
                    all_ev_ids.append(eid)
            if linked_ev_ids:
                best_ev_grade = "missing"
                for eid in linked_ev_ids:
                    best_ev_grade = _stronger_grade(best_ev_grade, evidence_by_id[eid].get("evidence_grade"))
                eff_grade = _weaker_grade(step.get("evidence_grade"), best_ev_grade)
                best_kind_grade = _stronger_grade(best_kind_grade, eff_grade)

        if best_kind_grade == "missing":
            by_kind[kind] = StepKindStatus(
                step_kind=kind,
                status="missing",
                weight=0.0,
                gap_kind="un_evidenced_step",
                step_ids=all_step_ids,
                evidence_ids=[],
            )
        else:
            by_kind[kind] = StepKindStatus(
                step_kind=kind,
                status=best_kind_grade,
                weight=GRADE_WEIGHTS[best_kind_grade],
                gap_kind=None,
                step_ids=all_step_ids,
                evidence_ids=all_ev_ids,
            )

    req_score = round(sum(s.weight for s in by_kind.values()) / len(REQUIRED_STEP_KINDS), 4)
    rec_score = round(recorded_weight_sum / recorded_count, 4) if recorded_count > 0 else 0.0
    return by_kind, req_score, rec_score, recorded_count, evidenced_count


def score_trace_data(data: dict, trace_path: str = "<memory>", trace_label: str = "memory") -> TraceCoverage:
    """Compute public-evidence coverage for a parsed OpenChokepoint YAML dictionary."""
    objects = data.get("objects") or []
    links = data.get("links") or []

    obj_by_id = {o.get("id"): o for o in objects if isinstance(o, dict) and o.get("id")}
    evidence_by_id = {
        oid: o for oid, o in obj_by_id.items() if o.get("type") == "EvidenceRecord"
    }
    evidenced_by_links = [
        l for l in links if isinstance(l, dict) and l.get("type") == "evidenced_by"
    ]

    all_steps = [o for o in objects if isinstance(o, dict) and o.get("type") == "ProcessStep"]
    is_synthetic = all(o.get("synthetic") is True for o in objects) if objects else True

    by_kind, req_score, rec_score, _, _ = evaluate_steps(
        all_steps, evidenced_by_links, evidence_by_id
    )

    # Evaluate each SerialItem individually
    instance_of_map: dict[str, str] = {}
    underwent_map: dict[str, list[str]] = {}
    for link in links:
        if not isinstance(link, dict):
            continue
        if link.get("type") == "instance_of":
            instance_of_map[link.get("from", "")] = link.get("to", "")
        elif link.get("type") == "underwent":
            underwent_map.setdefault(link.get("from", ""), []).append(link.get("to", ""))

    serial_coverages: list[SerialCoverage] = []
    for obj in objects:
        if not isinstance(obj, dict) or obj.get("type") != "SerialItem":
            continue
        sid = obj.get("id", "")
        sname = obj.get("serial") or obj.get("name") or sid
        step_ids = underwent_map.get(sid, [])
        serial_steps = [obj_by_id[stid] for stid in step_ids if stid in obj_by_id]
        s_by_kind, s_req_score, s_rec_score, s_rec_cnt, s_ev_cnt = evaluate_steps(
            serial_steps, evidenced_by_links, evidence_by_id
        )
        serial_coverages.append(
            SerialCoverage(
                serial_id=sid,
                serial_name=sname,
                component_id=instance_of_map.get(sid),
                required_step_score=s_req_score,
                recorded_step_score=s_rec_score,
                recorded_steps_count=s_rec_cnt,
                evidenced_steps_count=s_ev_cnt,
                confirmed_kinds=sum(1 for v in s_by_kind.values() if v.status == "confirmed"),
                reported_kinds=sum(1 for v in s_by_kind.values() if v.status == "reported"),
                missing_kinds=sum(1 for v in s_by_kind.values() if v.status == "missing"),
                by_step_kind=s_by_kind,
            )
        )

    return TraceCoverage(
        trace_path=trace_path,
        trace_label=trace_label,
        is_synthetic=is_synthetic,
        required_step_score=req_score,
        recorded_step_score=rec_score,
        confirmed_kinds=sum(1 for v in by_kind.values() if v.status == "confirmed"),
        reported_kinds=sum(1 for v in by_kind.values() if v.status == "reported"),
        missing_kinds=sum(1 for v in by_kind.values() if v.status == "missing"),
        by_step_kind=by_kind,
        serials=serial_coverages,
    )


def score_trace_file(path: Path, root: Path = ROOT) -> TraceCoverage:
    data = load_yaml(path)
    resolved = path.resolve()
    try:
        rel_path = resolved.relative_to(root.resolve()).as_posix()
    except ValueError:
        rel_path = path.as_posix()
    label = path.stem
    return score_trace_data(data, trace_path=rel_path, trace_label=label)


def discover_default_traces(root: Path = ROOT) -> list[Path]:
    """Find all digital-thread traces under data/digital-thread/ plus the synthetic turbopump thread example."""
    found: list[Path] = []
    dt_dir = root / "data" / "digital-thread"
    if dt_dir.exists():
        for p in sorted(dt_dir.rglob("*.yaml")):
            if p.name != "provenance.yaml":
                found.append(p)
    synth = root / "examples" / "synthetic-turbopump-thread.yaml"
    if synth.exists():
        found.append(synth)
    return found


def format_cell(st: StepKindStatus) -> str:
    if st.status == "confirmed":
        return "confirmed"
    if st.status == "reported":
        return "reported"
    if st.gap_kind == "un_evidenced_step":
        return "missing (un-evidenced step)"
    return "missing"


def render_gap_atlas(traces: list[TraceCoverage]) -> str:
    """Render the complete docs/gap-atlas.md markdown document."""
    lines: list[str] = [
        "Handling: Unclassified — public",
        "",
        "# Public-Evidence Gap Atlas",
        "",
        "This gap atlas is generated offline by `python3 tools/coverage.py --write-atlas` across all",
        "digital-thread traces in `data/digital-thread/` and the reference synthetic thread in",
        "`examples/synthetic-turbopump-thread.yaml`. See [`docs/coverage-score.md`](coverage-score.md)",
        "for the scoring methodology, step-kind baseline, and evidence-grade weights.",
        "",
        "## Trace Summary",
        "",
        "| Trace | Tier / Kind | Serial Items | Confirmed Step Kinds | Reported Step Kinds | Missing Step Kinds | Required-Step Score | Recorded-Step Coverage |",
        "|---|---|---:|---:|---:|---:|---:|---:|",
    ]
    for t in traces:
        tier_label = "synthetic example" if t.is_synthetic else "public real trace"
        lines.append(
            f"| `{t.trace_path}` | {tier_label} | {len(t.serials)} | "
            f"{t.confirmed_kinds}/10 | {t.reported_kinds}/10 | {t.missing_kinds}/10 | "
            f"**{t.required_step_score * 100:.1f}%** ({t.required_step_score:.2f}) | "
            f"{t.recorded_step_score * 100:.1f}% ({t.recorded_step_score:.2f}) |"
        )

    lines.extend(
        [
            "",
            "## Step-Kind Coverage Matrix (All Traces)",
            "",
            "Each cell reports the strongest public evidence grade backing that `ProcessStep.step_kind`",
            "(`confirmed` = 1.0, `reported` = 0.5, `missing` = 0.0). When a `ProcessStep` is recorded",
            "in the trace without an `evidenced_by` link to an `EvidenceRecord`, the cell highlights",
            "`missing (un-evidenced step)` to distinguish an explicit visibility gap from an unrecorded operation.",
            "",
        ]
    )

    headers = ["Step Kind"] + [f"`{t.trace_label}`" for t in traces]
    lines.append("| " + " | ".join(headers) + " |")
    lines.append("|" + "|".join(["---"] * len(headers)) + "|")

    for kind in REQUIRED_STEP_KINDS:
        row = [f"`{kind}`"]
        for t in traces:
            row.append(format_cell(t.by_step_kind[kind]))
        lines.append("| " + " | ".join(row) + " |")

    score_row = ["**Required-Step Score**"] + [
        f"**{t.required_step_score * 100:.1f}%** ({t.required_step_score:.2f})" for t in traces
    ]
    lines.append("| " + " | ".join(score_row) + " |")

    lines.extend(
        [
            "",
            "## Per-Serial Breakdown",
            "",
            "| Trace | Serial ID | Serial | Component | Recorded Steps | Evidenced Steps | Confirmed | Reported | Missing | Required-Step Score | Recorded-Step Coverage |",
            "|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for t in traces:
        for s in t.serials:
            lines.append(
                f"| `{t.trace_label}` | `{s.serial_id}` | `{s.serial_name}` | `{s.component_id or '-'}` | "
                f"{s.recorded_steps_count} | {s.evidenced_steps_count} | "
                f"{s.confirmed_kinds} | {s.reported_kinds} | {s.missing_kinds} | "
                f"**{s.required_step_score * 100:.1f}%** ({s.required_step_score:.2f}) | "
                f"{s.recorded_step_score * 100:.1f}% ({s.recorded_step_score:.2f}) |"
            )

    lines.extend(
        [
            "",
            "## Explicit Visibility Gaps (`un_evidenced_step`)",
            "",
            "Steps that are recorded on a `SerialItem` in the trace but have no `evidenced_by` link:",
            "",
        ]
    )
    for t in traces:
        gaps = [
            st for st in t.by_step_kind.values() if st.gap_kind == "un_evidenced_step"
        ]
        if gaps:
            for g in gaps:
                steps_str = ", ".join(f"`{sid}`" for sid in g.step_ids)
                lines.append(
                    f"- **`{t.trace_path}`** — `{g.step_kind}` ({steps_str}): step recorded without an `EvidenceRecord` (`missing`)."
                )
        else:
            lines.append(f"- **`{t.trace_path}`** — no un-evidenced recorded step kinds at the trace level.")

    lines.append("")
    return "\n".join(lines)


def render_text_report(traces: list[TraceCoverage]) -> str:
    lines: list[str] = []
    for t in traces:
        tier = "synthetic" if t.is_synthetic else "real"
        lines.append(
            f"TRACE {t.trace_path} [{tier}] — required_score={t.required_step_score:.2f} "
            f"({t.required_step_score * 100:.1f}%), recorded_score={t.recorded_step_score:.2f} "
            f"[confirmed={t.confirmed_kinds}, reported={t.reported_kinds}, missing={t.missing_kinds}]"
        )
        for kind in REQUIRED_STEP_KINDS:
            st = t.by_step_kind[kind]
            lines.append(f"  - {kind:<16} {format_cell(st)} (weight={st.weight:.1f})")
        for s in t.serials:
            lines.append(
                f"  serial {s.serial_id} ({s.serial_name}): required_score={s.required_step_score:.2f} "
                f"({s.required_step_score * 100:.1f}%), recorded_score={s.recorded_step_score:.2f} "
                f"({s.evidenced_steps_count}/{s.recorded_steps_count} steps evidenced)"
            )
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Compute public-evidence coverage scores and gap atlas for OpenChokepoint traces."
    )
    parser.add_argument(
        "traces",
        nargs="*",
        help="YAML trace files to score (defaults to data/digital-thread/**/*.yaml and examples/synthetic-turbopump-thread.yaml).",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit coverage report as JSON.",
    )
    parser.add_argument(
        "--atlas",
        action="store_true",
        help="Print the markdown gap atlas table to stdout.",
    )
    parser.add_argument(
        "--write-atlas",
        nargs="?",
        const=str(ROOT / "docs" / "gap-atlas.md"),
        metavar="PATH",
        help="Write the generated markdown gap atlas to PATH (default: docs/gap-atlas.md).",
    )
    args = parser.parse_args(argv if argv is not None else sys.argv[1:])

    target_paths = [Path(p) for p in args.traces] if args.traces else discover_default_traces(ROOT)
    if not target_paths:
        print("No trace files found.", file=sys.stderr)
        return 1

    scored = [score_trace_file(p, ROOT) for p in target_paths]

    if args.write_atlas:
        out_path = Path(args.write_atlas)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(render_gap_atlas(scored), encoding="utf-8", newline="\n")
        print(f"Wrote gap atlas to {out_path}")
        return 0

    if args.atlas:
        print(render_gap_atlas(scored), end="")
        return 0

    if args.json:
        print(json.dumps([asdict(t) for t in scored], indent=2))
        return 0

    print(render_text_report(scored))
    return 0


if __name__ == "__main__":
    sys.exit(main())
