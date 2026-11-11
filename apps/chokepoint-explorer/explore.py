#!/usr/bin/env python3
# Handling: Unclassified — public
# SPDX-License-Identifier: Apache-2.0
"""Chokepoint explorer: a sample application built on the OpenChokepoint Python SDK.

Reads one instance file and writes a plain-language Markdown report (or structured JSON
when `--format json` is passed): who controls the organizations, who is listed against
each capability, how each physical piece is traced, where evidence is missing, and which
critical items are declared.

Usage:
    python3 apps/chokepoint-explorer/explore.py examples/synthetic-turbopump-thread.yaml
    python3 apps/chokepoint-explorer/explore.py examples/synthetic-example.yaml --format json
    python3 apps/chokepoint-explorer/explore.py data/registry/launch-chain.yaml --out report.md

Guardrails (the report is a reading aid, not an assessment):
  - Fail closed. A file that does not pass tools/validate.py produces no report.
  - Facts only. The explorer counts and lists what the file states. It never scores, ranks or
    labels a real organization or part. Critical-item judgments are reported only as declared
    in the file, which the validator restricts to synthetic records.
  - No inferred order. Steps are shown in order only when the file gives the order.
"""
import argparse
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "sdk" / "python"))
from openchokepoint import Registry, validate  # noqa: E402

DELAY = {"d30_90": "30 to 90 days", "d90_180": "90 to 180 days", "d180_365": "180 to 365 days", "over_365": "over 365 days"}


def label(rec):
    if rec is None:
        return "(unknown)"
    return f"{rec.name or rec.id} (`{rec.id}`)"


def yes_no(v):
    return "yes" if v else "no"


def data_status(reg):
    real = len(reg.real_records())
    if real == 0:
        return "Synthetic. Every record is fictional."
    if real == len(reg):
        return "Public record. Real records drawn from cited public sources."
    return f"Mixed. {real} of {len(reg)} records are real."


def section_jurisdiction(reg):
    entities = reg.of_type("Entity")
    if not entities:
        return []
    lines = ["## Jurisdiction of control", "",
             "Where each organization is controlled from, as the file states it (control, not residency).", "",
             "| Controlling jurisdiction | Organizations |", "|---|---|"]
    for juris, n in sorted(Counter(e.get("controlling_jurisdiction") for e in entities).items()):
        lines.append(f"| {juris} | {n} |")
    split = [e for e in entities if e.get("incorporation_jurisdiction") != e.get("controlling_jurisdiction")]
    lines.append("")
    if split:
        lines += ["Incorporated in one jurisdiction, controlled from another:", ""]
        for e in split:
            lines.append(f"- {label(e)}: incorporated {e.get('incorporation_jurisdiction')}, "
                         f"controlled {e.get('controlling_jurisdiction')} (evidence: {e.get('evidence_grade')})")
    else:
        lines.append("No organization in this file is incorporated in one jurisdiction and controlled from another.")
    return lines + [""]


def section_capabilities(reg):
    caps = reg.of_type("Capability")
    if not caps:
        return []
    lines = ["## Capabilities", "",
             "Providers and requiring programmes listed **in this file**. A count describes the file, "
             "not the market, and is not a judgment about any provider.", "",
             "| Capability | Listed providers | Required by |", "|---|---|---|"]
    for c in caps:
        providers = reg.sources(c.id, "provides_capability")
        programmes = reg.sources(c.id, "requires_capability")
        prov = "; ".join(label(p) for p in providers) or "none listed"
        prog = "; ".join(label(p) for p in programmes) or "none listed"
        lines.append(f"| {label(c)} | {prov} | {prog} |")
    return lines + [""]


def section_threads(reg):
    serials = reg.of_type("SerialItem")
    if not serials:
        return []
    lines = ["## Digital threads", "",
             "Each physical piece, the design it is made to, the material it came from, and the steps it went "
             "through. An evidence record is a pointer that a record exists; it is not proof the part was accepted.", ""]
    for s in serials:
        designs = reg.targets(s.id, "instance_of")
        lots = reg.targets(s.id, "made_from")
        lines.append(f"### {label(s)}")
        lines.append("")
        lines.append(f"- Design: {', '.join(label(d) + ' rev ' + str(d.get('revision')) for d in designs) or 'not stated'}")
        for lot in lots:
            producers = reg.targets(lot.id, "produced_by")
            lines.append(f"- Material lot: {label(lot)}, {lot.get('material_class')}, "
                         f"from {', '.join(label(p) for p in producers) or 'producer not stated'}")
        if not lots:
            lines.append("- Material lot: not stated")
        steps, ordered = reg.steps_for(s.id)
        lines.append("")
        if not steps:
            lines += ["No process steps recorded.", ""]
            continue
        if not ordered:
            lines += ["Order not published: the file records that these steps happened, not their sequence.", ""]
        lines += ["| # | Step | Where | Evidence |", "|---|---|---|---|"]
        for seq, step in steps:
            where = ", ".join(label(f) for f in reg.targets(step.id, "performed_at")) or "not stated"
            evidence = reg.evidence_for(step.id)
            ev = "; ".join(f"{e.get('record_kind')} from {e.get('issuer')}" for e in evidence) or "**missing**"
            lines.append(f"| {seq if ordered else '-'} | {step.get('step_kind')} | {where} | {ev} |")
        lines.append("")
    return lines


def section_gaps(reg):
    gaps = reg.steps_without_evidence()
    if not reg.of_type("ProcessStep"):
        return []
    lines = ["## Evidence gaps", ""]
    if not gaps:
        return lines + ["Every recorded step has at least one evidence record.", ""]
    lines += ["Steps with no evidence record. A gap is shown, never filled: it tells a reader where to ask.", ""]
    for g in gaps:
        pieces = reg.sources(g.id, "underwent")
        lines.append(f"- {g.get('step_kind')} step `{g.id}` on {', '.join(label(p) for p in pieces) or 'no piece stated'}")
    return lines + [""]


def section_critical(reg):
    items = [c for c in reg.of_type("CriticalItem") if c.synthetic]
    if not items:
        return []
    lines = ["## Declared critical items (synthetic)", "",
             "Judgments declared in the file: loss of the flagged item would delay a programme by more than 30 days. "
             "The validator permits these on fictional records only.", "",
             "| Item | Flags | Delay | Single source | Qualified alternate | Missing evidence |",
             "|---|---|---|---|---|---|"]
    for c in items:
        flagged = ", ".join(label(t) for t in reg.targets(c.id, "flags")) or "nothing"
        alternates = reg.sources(c.id, "alternate_for")
        alt = yes_no(c.get("qualified_alternate"))
        if alternates:
            alt += ": " + ", ".join(label(a) for a in alternates)
        lines.append(f"| {label(c)} | {flagged} | {DELAY.get(c.get('delay_band'), c.get('delay_band'))} | "
                     f"{yes_no(c.get('single_source'))} | {alt} | {yes_no(c.get('missing_evidence'))} |")
    return lines + [""]


def build_json_payload(path, reg, tier="public"):
    """Build structured JSON representation of the same findings shown in the Markdown report."""
    counts = dict(sorted(Counter(r.type for r in reg.objects).items()))
    entities = reg.of_type("Entity")
    juris_counts = dict(sorted(Counter(e.get("controlling_jurisdiction") for e in entities).items()))
    split_entities = [
        {
            "id": e.id,
            "name": e.name,
            "incorporation_jurisdiction": e.get("incorporation_jurisdiction"),
            "controlling_jurisdiction": e.get("controlling_jurisdiction"),
            "evidence_grade": e.get("evidence_grade"),
        }
        for e in entities
        if e.get("incorporation_jurisdiction") != e.get("controlling_jurisdiction")
    ]

    capabilities = [
        {
            "id": c.id,
            "name": c.name,
            "providers": [{"id": p.id, "name": p.name} for p in reg.sources(c.id, "provides_capability")],
            "required_by": [{"id": p.id, "name": p.name} for p in reg.sources(c.id, "requires_capability")],
        }
        for c in reg.of_type("Capability")
    ]

    threads = []
    for s in reg.of_type("SerialItem"):
        designs = reg.targets(s.id, "instance_of")
        lots = reg.targets(s.id, "made_from")
        steps, ordered = reg.steps_for(s.id)
        threads.append(
            {
                "id": s.id,
                "name": s.name,
                "serial": s.get("serial"),
                "designs": [
                    {"id": d.id, "name": d.name, "revision": d.get("revision")}
                    for d in designs
                ],
                "material_lots": [
                    {
                        "id": lot.id,
                        "name": lot.name,
                        "material_class": lot.get("material_class"),
                        "producers": [{"id": p.id, "name": p.name} for p in reg.targets(lot.id, "produced_by")],
                    }
                    for lot in lots
                ],
                "ordered": ordered,
                "steps": [
                    {
                        "sequence": seq if ordered else None,
                        "id": step.id,
                        "step_kind": step.get("step_kind"),
                        "performed_at": [{"id": f.id, "name": f.name} for f in reg.targets(step.id, "performed_at")],
                        "evidence": [
                            {
                                "id": e.id,
                                "record_kind": e.get("record_kind"),
                                "issuer": e.get("issuer"),
                            }
                            for e in reg.evidence_for(step.id)
                        ],
                    }
                    for seq, step in steps
                ],
            }
        )

    gaps = [
        {
            "id": g.id,
            "step_kind": g.get("step_kind"),
            "serial_items": [{"id": p.id, "name": p.name} for p in reg.sources(g.id, "underwent")],
        }
        for g in reg.steps_without_evidence()
    ]

    critical_items = [
        {
            "id": c.id,
            "name": c.name,
            "flags": [{"id": t.id, "name": t.name} for t in reg.targets(c.id, "flags")],
            "delay_band": c.get("delay_band"),
            "single_source": bool(c.get("single_source")),
            "qualified_alternate": bool(c.get("qualified_alternate")),
            "alternates": [{"id": a.id, "name": a.name} for a in reg.sources(c.id, "alternate_for")],
            "missing_evidence": bool(c.get("missing_evidence")),
        }
        for c in reg.of_type("CriticalItem")
        if c.synthetic
    ]

    return {
        "handling": "Unclassified — public",
        "file": Path(path).name,
        "data_status": data_status(reg),
        "validation": {"passed": True, "tier": tier},
        "counts": {
            "objects": len(reg.objects),
            "links": len(reg.links),
            "by_type": counts,
        },
        "jurisdiction_of_control": {
            "counts": juris_counts,
            "split_jurisdiction_entities": split_entities,
        },
        "capabilities": capabilities,
        "digital_threads": threads,
        "evidence_gaps": gaps,
        "declared_critical_items": critical_items,
    }


def report(path, tier="public", fmt="markdown"):
    """Return (output_text, issues). Output is None when validation fails."""
    issues = validate(path, tier=tier, root=ROOT)
    if issues:
        return None, issues
    reg = Registry.load(path)
    if fmt == "json":
        payload = build_json_payload(path, reg, tier=tier)
        return json.dumps(payload, indent=2) + "\n", []
    counts = Counter(r.type for r in reg.objects)
    lines = [
        "Handling: Unclassified — public",
        "",
        f"# Chokepoint explorer: `{Path(path).name}`",
        "",
        f"- Data: {data_status(reg)}",
        f"- Records: {len(reg.objects)} objects, {len(reg.links)} links "
        f"({', '.join(f'{n} {t}' for t, n in sorted(counts.items()))})",
        f"- Validation: passed ({tier} tier)",
        "",
        "This report lists what the file states. It does not score, rank or assess any organization or part.",
        "",
    ]
    for section in (section_jurisdiction, section_capabilities, section_threads, section_gaps, section_critical):
        lines += section(reg)
    return "\n".join(lines).rstrip() + "\n", []


def main(argv=None):
    ap = argparse.ArgumentParser(description="Plain-language report on one OpenChokepoint instance file.")
    ap.add_argument("file", help="instance file (.yaml)")
    ap.add_argument("--tier", choices=["public", "private"], default="public")
    ap.add_argument("--format", choices=["markdown", "json"], default="markdown", help="output format (default: markdown)")
    ap.add_argument("--out", help="write the report to this file instead of the screen")
    args = ap.parse_args(argv)
    out_text, issues = report(args.file, args.tier, fmt=args.format)
    if issues:
        print(f"No report: {args.file} does not pass validation.", file=sys.stderr)
        for i in issues:
            print(f"  - {i}", file=sys.stderr)
        return 2
    if args.out:
        Path(args.out).write_text(out_text, encoding="utf-8")
        print(f"wrote {args.out}")
    else:
        print(out_text, end="")
    return 0


if __name__ == "__main__":
    sys.exit(main())
