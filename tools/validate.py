#!/usr/bin/env python3
# Handling: Unclassified — public
# SPDX-License-Identifier: Apache-2.0
"""Validate instance files against the OpenChokepoint schema.

Usage:
    python3 tools/validate.py [instance.yaml ...]

Defaults to the synthetic example. Requires PyYAML. Exits non-zero on any error.
Records outside data/ must carry `synthetic: true`. Real records are accepted only under data/ with a provenance.yaml (see DATA-CONTRIBUTIONS.md).
"""
import datetime
import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
ISO3166 = re.compile(r"^[A-Z]{2}(-[A-Z0-9]{1,3})?$")
URL = re.compile(r"^https?://\S+$")


def load(path):
    with open(path, encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def check_value(spec, value, label, errors, known_ids):
    vtype = spec["type"]
    values = value if spec.get("many") else [value]
    if spec.get("many") and (not isinstance(value, list) or not value):
        errors.append(f"{label}: expected a non-empty list")
        return
    for v in values:
        ok = {
            "string": lambda x: isinstance(x, str) and x.strip() != "",
            "integer": lambda x: isinstance(x, int) and not isinstance(x, bool),
            "decimal": lambda x: isinstance(x, (int, float)) and not isinstance(x, bool),
            "boolean": lambda x: isinstance(x, bool),
            "date": lambda x: isinstance(x, datetime.date),
            "iso3166": lambda x: isinstance(x, str) and bool(ISO3166.match(x)),
            "url": lambda x: isinstance(x, str) and bool(URL.match(x)),
            "enum": lambda x: x in spec.get("values", []),
            "ref": lambda x: x in known_ids,
        }[vtype](v)
        if not ok:
            errors.append(f"{label}: value {v!r} is not a valid {vtype}")


def check_props(record, props, label, errors, known_ids, reserved):
    for name, spec in props.items():
        if name in record:
            check_value(spec, record[name], f"{label}.{name}", errors, known_ids)
        elif spec.get("required"):
            errors.append(f"{label}: missing required property '{name}'")
    for name in record:
        if name not in props and name not in reserved:
            errors.append(f"{label}: unknown property '{name}'")


PERSONAL = re.compile(r"[\w.+-]+@[\w-]+\.[a-z]{2,}|\(?\b\d{3}\)?[ .-]\d{3}[ .-]\d{4}\b")


def check_public_data(path, records):
    """Real (non-synthetic) records are accepted only under data/, with a complete provenance.yaml,
    public http(s) sources on every record, and no personal contact details (DATA-CONTRIBUTIONS.md)."""
    errs = []
    rel = path.resolve().relative_to(ROOT) if path.resolve().is_relative_to(ROOT) else path
    if not str(rel).startswith("data/"):
        return [f"{path}: real records are accepted only under data/ — everything else must be synthetic"]
    prov_path = path.parent / "provenance.yaml"
    if not prov_path.exists():
        return [f"{path}: real records need a provenance.yaml in the same folder"]
    prov = load(prov_path) or {}
    if prov.get("personal_information") != "none":
        errs.append(f"{prov_path}: personal_information must be 'none'")
    if prov.get("export_controlled") is not False:
        errs.append(f"{prov_path}: export_controlled must be false")
    if not prov.get("sources"):
        errs.append(f"{prov_path}: sources missing")
    for rec in records:
        if rec.get("synthetic") is not False:
            errs.append(f"{rec.get('id')}: set synthetic: false explicitly on real records")
        if rec.get("evidence_grade") in ("speculative", "no_evidence"):
            errs.append(f"{rec.get('id')}: real records need evidence grade confirmed, reported or inferred")
        for s in rec.get("sources") or []:
            if not str(s).startswith("https://"):
                errs.append(f"{rec.get('id')}: sources must be public https URLs")
        if PERSONAL.search(" ".join(str(v) for v in rec.values() if isinstance(v, str))):
            errs.append(f"{rec.get('id')}: looks like an email address or phone number — no personal contact details")
    return errs


def validate(instance_path, onto):
    errors = []
    data = load(instance_path)
    shared = onto["shared_properties"]

    objects = data.get("objects", [])
    links = data.get("links", [])
    all_ids = [r.get("id") for r in objects + links]
    dupes = {i for i in all_ids if all_ids.count(i) > 1}
    for d in dupes:
        errors.append(f"duplicate id '{d}'")
    types_by_id = {o.get("id"): o.get("type") for o in objects}

    real = [r for r in objects + links if r.get("synthetic") is not True]
    if real:
        errors.extend(check_public_data(Path(instance_path), real))

    for obj in objects:
        label = f"object {obj.get('id')}"
        otype = onto["object_types"].get(obj.get("type"))
        if not otype:
            errors.append(f"{label}: unknown object type '{obj.get('type')}'")
            continue
        props = {**shared, **otype.get("properties", {})}
        check_props(obj, props, label, errors, types_by_id, {"type"})

    for link in links:
        label = f"link {link.get('id')}"
        ltype = onto["link_types"].get(link.get("type"))
        if not ltype:
            errors.append(f"{label}: unknown link type '{link.get('type')}'")
            continue
        props = {**shared, **ltype.get("properties", {})}
        check_props(link, props, label, errors, types_by_id, {"type", "from", "to"})
        for end in ("from", "to"):
            target = link.get(end)
            if target not in types_by_id:
                errors.append(f"{label}: '{end}' references unknown object '{target}'")
            elif types_by_id[target] not in ltype[end]:
                errors.append(f"{label}: '{end}' type {types_by_id[target]} not allowed (expects {ltype[end]})")
    return errors


def main(argv):
    onto = load(ROOT / "schema" / "openchokepoint.yaml")
    targets = argv[1:] or [ROOT / "examples" / "synthetic-example.yaml"]
    failed = False
    for target in targets:
        errors = validate(target, onto)
        if errors:
            failed = True
            print(f"FAIL {target}")
            for e in errors:
                print(f"  - {e}")
        else:
            print(f"OK   {target}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
