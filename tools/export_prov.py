#!/usr/bin/env python3
# Handling: Unclassified — public
"""Export an OpenChokepoint digital-thread YAML file to W3C PROV-O (JSON-LD or Turtle).

Implements Slice D (#19, Part of #3) using only PyYAML and the Python standard library.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import yaml

OCP_NS = "https://openchokepoint.org/ns#"
PROV_NS = "http://www.w3.org/ns/prov#"
XSD_NS = "http://www.w3.org/2001/XMLSchema#"


def _urn(item_id: str) -> str:
    clean = str(item_id).strip().replace(" ", "_")
    return f"urn:openchokepoint:{clean}"


def _append_ref(node: dict[str, Any], prop: str, target_urn: str) -> None:
    existing = node.get(prop)
    if existing is None:
        node[prop] = [target_urn]
    elif isinstance(existing, list):
        if target_urn not in existing:
            existing.append(target_urn)
    elif existing != target_urn:
        node[prop] = [existing, target_urn]


def convert_trace_to_prov_jsonld(data: dict[str, Any]) -> dict[str, Any]:
    """Convert a parsed OpenChokepoint YAML mapping into a W3C PROV-O JSON-LD document."""
    if not isinstance(data, dict):
        raise ValueError("OpenChokepoint trace root must be a YAML mapping")

    graph: list[dict[str, Any]] = []
    by_urn: dict[str, dict[str, Any]] = {}

    # Support OpenChokepoint v0.2.x `objects:` + `links:` structure
    if "objects" in data or "links" in data:
        for obj in data.get("objects", []) or []:
            if not isinstance(obj, dict) or not obj.get("id"):
                continue
            otype = obj.get("type", "Entity")
            u = _urn(obj["id"])
            if otype == "Entity":
                prov_types = ["prov:Agent", "prov:Organization", "ocp:Entity"]
            elif otype == "Facility":
                prov_types = ["prov:Location", "prov:Entity", "ocp:Facility"]
            elif otype == "ProcessStep":
                prov_types = ["prov:Activity", "ocp:ProcessStep"]
            else:
                prov_types = ["prov:Entity", f"ocp:{otype}"]
            node: dict[str, Any] = {
                "@id": u,
                "@type": prov_types,
            }
            if obj.get("name"):
                node["ocp:name"] = obj["name"]
            if obj.get("step_kind"):
                node["ocp:stepKind"] = obj["step_kind"]
            if obj.get("record_kind"):
                node["ocp:recordKind"] = obj["record_kind"]
            if obj.get("evidence_grade"):
                node["ocp:evidenceGrade"] = obj["evidence_grade"]
            if obj.get("content_hash"):
                node["ocp:contentHash"] = obj["content_hash"]
            graph.append(node)
            by_urn[u] = node

        for lnk in data.get("links", []) or []:
            if not isinstance(lnk, dict) or not lnk.get("from") or not lnk.get("to"):
                continue
            ltype = lnk.get("type", "")
            src_u = _urn(lnk["from"])
            dst_u = _urn(lnk["to"])
            src_node = by_urn.setdefault(src_u, {"@id": src_u, "@type": ["prov:Entity"]})
            if src_node not in graph:
                graph.append(src_node)
            if ltype == "instance_of":
                src_node["prov:specializationOf"] = dst_u
            elif ltype in ("made_from", "evidenced_by"):
                _append_ref(src_node, "prov:wasDerivedFrom", dst_u)
            elif ltype == "undergwent":
                _append_ref(src_node, "prov:wasGeneratedBy", dst_u)
            elif ltype == "performed_at":
                src_node["prov:wasAssociatedWith"] = dst_u
                src_node["prov:atLocation"] = dst_u
            elif ltype == "produced_by":
                src_node["prov:wasAttributedTo"] = dst_u
            elif ltype == "located_at":
                src_node["prov:atLocation"] = dst_u
            elif ltype == "alternate_for":
                _append_ref(src_node, "prov:alternateOf", dst_u)
            elif ltype == "flags":
                _append_ref(src_node, "ocp:flags", dst_u)

    # 1. Entities / Organisations (prov:Agent + prov:Organization)
    for ent in data.get("entities", []) or []:
        if not isinstance(ent, dict) or not ent.get("id"):
            continue
        node: dict[str, Any] = {
            "@id": _urn(ent["id"]),
            "@type": ["prov:Agent", "prov:Organization", "ocp:Entity"],
            "ocp:name": ent.get("name", ent["id"]),
        }
        if ent.get("country"):
            node["ocp:country"] = ent["country"]
        if ent.get("evidence_grade"):
            node["ocp:evidenceGrade"] = ent["evidence_grade"]
        if ent.get("alternate_for"):
            alt = ent["alternate_for"]
            alt_list = alt if isinstance(alt, list) else [alt]
            node["prov:alternateOf"] = [_urn(a) for a in alt_list]
        graph.append(node)

    # 2. Components (prov:Entity, STEP product_definition, QIF Part)
    for comp in data.get("components", []) or []:
        if not isinstance(comp, dict) or not comp.get("id"):
            continue
        node = {
            "@id": _urn(comp["id"]),
            "@type": ["prov:Entity", "ocp:Component"],
            "ocp:name": comp.get("name", comp["id"]),
        }
        if comp.get("category"):
            node["ocp:category"] = comp["category"]
        if comp.get("alternate_for"):
            alt = comp["alternate_for"]
            alt_list = alt if isinstance(alt, list) else [alt]
            node["prov:alternateOf"] = [_urn(a) for a in alt_list]
        graph.append(node)

    # 3. MaterialLots (prov:Entity)
    for lot in data.get("material_lots", []) or []:
        if not isinstance(lot, dict) or not lot.get("id"):
            continue
        node = {
            "@id": _urn(lot["id"]),
            "@type": ["prov:Entity", "ocp:MaterialLot"],
        }
        if lot.get("material_family") or lot.get("material"):
            node["ocp:materialFamily"] = lot.get("material_family") or lot.get("material")
        if lot.get("supplier_id") or lot.get("produced_by"):
            sup = lot.get("supplier_id") or lot.get("produced_by")
            node["prov:wasAttributedTo"] = _urn(sup)
        if lot.get("evidence_records") or lot.get("evidenced_by"):
            evs = lot.get("evidence_records") or lot.get("evidenced_by")
            ev_list = evs if isinstance(evs, list) else [evs]
            node["prov:wasDerivedFrom"] = [_urn(e) for e in ev_list]
        graph.append(node)

    # 4. EvidenceRecords (prov:Entity)
    for ev in data.get("evidence_records", []) or []:
        if not isinstance(ev, dict) or not ev.get("id"):
            continue
        node = {
            "@id": _urn(ev["id"]),
            "@type": ["prov:Entity", "ocp:EvidenceRecord"],
        }
        if ev.get("kind") or ev.get("record_kind"):
            node["ocp:recordKind"] = ev.get("kind") or ev.get("record_kind")
        if ev.get("evidence_grade") or ev.get("grade"):
            node["ocp:evidenceGrade"] = ev.get("evidence_grade") or ev.get("grade")
        if ev.get("source_url") or ev.get("uri"):
            node["prov:hadPrimarySource"] = ev.get("source_url") or ev.get("uri")
        graph.append(node)

    # 5. ProcessSteps (prov:Activity)
    for step in data.get("process_steps", []) or []:
        if not isinstance(step, dict) or not step.get("id"):
            continue
        node = {
            "@id": _urn(step["id"]),
            "@type": ["prov:Activity", "ocp:ProcessStep"],
        }
        if step.get("step_kind") or step.get("kind"):
            node["ocp:stepKind"] = step.get("step_kind") or step.get("kind")
        facility = step.get("performed_at") or step.get("facility_id") or step.get("entity_id")
        if facility:
            node["prov:wasAssociatedWith"] = _urn(facility)
            node["prov:atLocation"] = _urn(facility)
        evs = step.get("evidenced_by") or step.get("evidence_records")
        if evs:
            ev_list = evs if isinstance(evs, list) else [evs]
            node["prov:wasDerivedFrom"] = [_urn(e) for e in ev_list]
        if step.get("evidence_grade"):
            node["ocp:evidenceGrade"] = step["evidence_grade"]
        graph.append(node)

    # 6. SerialItems (prov:Entity)
    for item in data.get("serial_items", []) or []:
        if not isinstance(item, dict) or not item.get("id"):
            continue
        node = {
            "@id": _urn(item["id"]),
            "@type": ["prov:Entity", "ocp:SerialItem"],
        }
        comp_id = item.get("instance_of") or item.get("component_id")
        if comp_id:
            node["prov:specializationOf"] = _urn(comp_id)
        derived: list[str] = []
        for field in ("made_from", "material_lots", "input_lots", "sub_items"):
            vals = item.get(field)
            if vals:
                v_list = vals if isinstance(vals, list) else [vals]
                derived.extend(_urn(v) for v in v_list)
        evs = item.get("evidenced_by") or item.get("evidence_records")
        if evs:
            ev_list = evs if isinstance(evs, list) else [evs]
            derived.extend(_urn(e) for e in ev_list)
        if derived:
            node["prov:wasDerivedFrom"] = derived

        steps = item.get("undergwent") or item.get("process_steps")
        if steps:
            s_list = steps if isinstance(steps, list) else [steps]
            step_ids: list[str] = []
            for s in s_list:
                if isinstance(s, dict) and s.get("id"):
                    step_ids.append(_urn(s["id"]))
                    # Also register embedded ProcessStep if not top-level
                    emb: dict[str, Any] = {
                        "@id": _urn(s["id"]),
                        "@type": ["prov:Activity", "ocp:ProcessStep"],
                    }
                    if s.get("step_kind") or s.get("kind"):
                        emb["ocp:stepKind"] = s.get("step_kind") or s.get("kind")
                    fac = s.get("performed_at") or s.get("facility_id") or s.get("entity_id")
                    if fac:
                        emb["prov:wasAssociatedWith"] = _urn(fac)
                    s_evs = s.get("evidenced_by") or s.get("evidence_records")
                    if s_evs:
                        se_list = s_evs if isinstance(s_evs, list) else [s_evs]
                        emb["prov:wasDerivedFrom"] = [_urn(e) for e in se_list]
                    graph.append(emb)
                elif isinstance(s, str):
                    step_ids.append(_urn(s))
            if step_ids:
                node["prov:wasGeneratedBy"] = step_ids
        graph.append(node)

    # 7. CriticalItems (prov:Entity + ocp:CriticalItem)
    for crit in data.get("critical_items", []) or []:
        if not isinstance(crit, dict) or not crit.get("id"):
            continue
        node = {
            "@id": _urn(crit["id"]),
            "@type": ["prov:Entity", "ocp:CriticalItem"],
        }
        if crit.get("component_id"):
            node["prov:specializationOf"] = _urn(crit["component_id"])
        if crit.get("alternate_for"):
            alt = crit["alternate_for"]
            alt_list = alt if isinstance(alt, list) else [alt]
            node["prov:alternateOf"] = [_urn(a) for a in alt_list]
        graph.append(node)

    return {
        "@context": {
            "prov": PROV_NS,
            "xsd": XSD_NS,
            "ocp": OCP_NS,
            "prov:specializationOf": {"@type": "@id"},
            "prov:wasDerivedFrom": {"@type": "@id"},
            "prov:wasGeneratedBy": {"@type": "@id"},
            "prov:wasAssociatedWith": {"@type": "@id"},
            "prov:wasAttributedTo": {"@type": "@id"},
            "prov:atLocation": {"@type": "@id"},
            "prov:alternateOf": {"@type": "@id"},
        },
        "@graph": graph,
    }


def convert_trace_to_prov_turtle(data: dict[str, Any]) -> str:
    """Serialize the W3C PROV-O graph into deterministic W3C Turtle (RDF) syntax."""
    doc = convert_trace_to_prov_jsonld(data)
    lines = [
        f"@prefix prov: <{PROV_NS}> .",
        f"@prefix ocp: <{OCP_NS}> .",
        f"@prefix xsd: <{XSD_NS}> .",
        "",
    ]
    for node in doc["@graph"]:
        subj = f"<{node['@id']}>"
        types = ", ".join(node.get("@type", ["prov:Entity"]))
        stmts = [f"a {types}"]
        for key, val in sorted(node.items()):
            if key in ("@id", "@type"):
                continue
            vals = val if isinstance(val, list) else [val]
            rendered_objs: list[str] = []
            for v in vals:
                if isinstance(v, str) and v.startswith("urn:"):
                    rendered_objs.append(f"<{v}>")
                else:
                    escaped = str(v).replace("\\", "\\\\").replace('"', '\\"')
                    rendered_objs.append(f'"{escaped}"')
            stmts.append(f"{key} {', '.join(rendered_objs)}")
        lines.append(f"{subj} " + " ;\n    ".join(stmts) + " .")
        lines.append("")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Export an OpenChokepoint YAML trace to W3C PROV-O (JSON-LD or Turtle)."
    )
    parser.add_argument("path", type=Path, help="Path to OpenChokepoint YAML file")
    parser.add_argument(
        "--format",
        choices=("jsonld", "ttl"),
        default="jsonld",
        help="Output RDF serialisation format (default: jsonld)",
    )
    args = parser.parse_args(argv)

    if not args.path.exists():
        print(f"Error: file not found: {args.path}", file=sys.stderr)
        return 1

    raw = yaml.safe_load(args.path.read_text(encoding="utf-8"))
    if args.format == "ttl":
        print(convert_trace_to_prov_turtle(raw))
    else:
        print(json.dumps(convert_trace_to_prov_jsonld(raw), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
