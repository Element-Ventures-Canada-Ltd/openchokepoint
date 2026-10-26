#!/usr/bin/env python3
# Handling: Unclassified — public
# SPDX-License-Identifier: Apache-2.0
'''Validate instance files against the OpenChokepoint schema.

Usage:
    python3 tools/validate.py [--tier public|private] [instance.yaml ...]

--tier public (default) is for this public repository and its CI. --tier private is for private clones that hold full data.

Defaults to the synthetic examples. Requires PyYAML. Exits non-zero on any error.
Records outside data/ must carry `synthetic: true`. Real records are accepted only under data/ with a provenance.yaml (see DATA-CONTRIBUTIONS.md).

Schema v0.2 adds digital-thread rules. Each error starts with a stable rule ID so reviewers can cite it:
  EV-001  EvidenceRecord must carry a content hash or a public citation
  EV-002  EvidenceRecord must not carry inline content; content_hash must be sha256:<64 hex>; short strings only
  EV-003  EvidenceRecord citation must be a public https URL
  EV-004  A real EvidenceRecord must use a public citation (public reports only)
  CI-001  CriticalItem must be synthetic: true
  CI-002  CriticalItem must not flag, or be offered an alternate by, a real record
  CI-003  CriticalItem must not reach a real record through its target (mixed graphs)
  CI-004  CriticalItem flags must be consistent with the graph (alternate linked; missing evidence really missing)
  DT-001  underwent.sequence must be unique per SerialItem
  DT-002  Real digital-thread records must be graded confirmed or reported (gaps are shown, never inferred)
  DT-003  Public tier: a real underwent link must not carry a sequence (steps that happened, not their order)
  DT-004  An underwent link needs a sequence, except a real link in the public tier
  RT-001  Free text must not carry a number with an engineering unit
  RT-002  Free text must not carry a tolerance or a numeric range
  RT-003  Free text must not carry an encoded or split numeric value
  RT-004  Free text must not carry look-alike characters that hide a value
  RT-005  Identifiers must not carry a unit or tolerance
'''
import datetime
import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
ISO3166 = re.compile(r'^[A-Z]{2}(-[A-Z0-9]{1,3})?$')
URL = re.compile(r'^https?://\S+$')


def load(path):
    with open(path, encoding='utf-8') as fh:
        return yaml.safe_load(fh)


def check_value(spec, value, label, errors, known_ids):
    vtype = spec['type']
    values = value if spec.get('many') else [value]
    if spec.get('many') and (not isinstance(value, list) or not value):
        errors.append(f'{label}: expected a non-empty list')
        return
    for v in values:
        ok = {
            'string': lambda x: isinstance(x, str) and x.strip() != '',
            'integer': lambda x: isinstance(x, int) and not isinstance(x, bool),
            'decimal': lambda x: isinstance(x, (int, float)) and not isinstance(x, bool),
            'boolean': lambda x: isinstance(x, bool),
            'date': lambda x: isinstance(x, datetime.date),
            'iso3166': lambda x: isinstance(x, str) and bool(ISO3166.match(x)),
            'url': lambda x: isinstance(x, str) and bool(URL.match(x)),
            'enum': lambda x: x in spec.get('values', []),
            'ref': lambda x: x in known_ids,
        }[vtype](v)
        if not ok:
            errors.append(f'{label}: value {v!r} is not a valid {vtype}')


def check_props(record, props, label, errors, known_ids, reserved):
    for name, spec in props.items():
        if name in record:
            check_value(spec, record[name], f'{label}.{name}', errors, known_ids)
        elif spec.get('required'):
            errors.append(f'{label}: missing required property {name!r}')
    for name in record:
        if name not in props and name not in reserved:
            errors.append(f'{label}: unknown property {name!r}')


PERSONAL = re.compile(r'[\w.+-]+@[\w-]+\.[a-z]{2,}|\(?\b\d{3}\)?[ .-]\d{3}[ .-]\d{4}\b')


def check_public_data(path, records):
    '''Real (non-synthetic) records are accepted only under data/, with a complete provenance.yaml,
    public http(s) sources on every record, and no personal contact details (DATA-CONTRIBUTIONS.md).'''
    errs = []
    rel = path.resolve().relative_to(ROOT) if path.resolve().is_relative_to(ROOT) else path
    if not str(rel).startswith('data/'):
        return [f'{path}: real records are accepted only under data/ — everything else must be synthetic']
    prov_path = path.parent / 'provenance.yaml'
    if not prov_path.exists():
        return [f'{path}: real records need a provenance.yaml in the same folder']
    prov = load(prov_path) or {}
    if prov.get('personal_information') != 'none':
        errs.append(f'{prov_path}: personal_information must be none')
    if prov.get('export_controlled') is not False:
        errs.append(f'{prov_path}: export_controlled must be false')
    if not prov.get('sources'):
        errs.append(f'{prov_path}: sources missing')
    for rec in records:
        if rec.get('synthetic') is not False:
            errs.append(f'{rec.get("id")}: set synthetic: false explicitly on real records')
        if rec.get('evidence_grade') in ('speculative', 'no_evidence'):
            errs.append(f'{rec.get("id")}: real records need evidence grade confirmed, reported or inferred')
        for s in rec.get('sources') or []:
            if not str(s).startswith('https://'):
                errs.append(f'{rec.get("id")}: sources must be public https URLs')
        if PERSONAL.search(' '.join(str(v) for v in rec.values() if isinstance(v, str))):
            errs.append(f'{rec.get("id")}: looks like an email address or phone number — no personal contact details')
    return errs


THREAD_TYPES = {'Component', 'SerialItem', 'MaterialLot', 'ProcessStep', 'EvidenceRecord'}
SHA256 = re.compile(r'^sha256:[0-9a-f]{64}$')
INLINE_CONTENT = {'content', 'body', 'text', 'data', 'attachment', 'payload', 'excerpt', 'value', 'values',
                  'result', 'results', 'measurements', 'parameters', 'notes'}
EVIDENCE_STRING_MAX = 120
RESERVED = {'type', 'id', 'evidence_grade', 'sources', 'as_of', 'lifecycle', 'synthetic', 'from', 'to', 'sequence'}


def is_real(rec):
    return rec.get('synthetic') is not True


def check_thread(objects, links, tier='public'):
    '''Digital-thread and critical-item rules (schema v0.2). Fail closed; every error names the rule and the record.'''
    errs = []
    by_id = {r.get('id'): r for r in objects + links}

    for o in objects:
        if o.get('type') != 'EvidenceRecord':
            continue
        rid = o.get('id')
        has_hash, has_cite = 'content_hash' in o, 'citation' in o
        if not (has_hash or has_cite):
            errs.append(f'EV-001 {rid}: EvidenceRecord needs content_hash or citation (a pointer to the record, never the record)')
        bad = sorted(INLINE_CONTENT & set(o))
        if bad:
            errs.append(f'EV-002 {rid}: inline content field(s) {bad} not allowed; point to the record with content_hash or citation')
        if has_hash and not SHA256.match(str(o['content_hash'])):
            errs.append(f'EV-002 {rid}: content_hash must be sha256:<64 lowercase hex>')
        for k in ('issuer', 'citation_section', 'name'):
            if isinstance(o.get(k), str) and len(o[k]) > EVIDENCE_STRING_MAX:
                errs.append(f'EV-002 {rid}: {k!r} longer than {EVIDENCE_STRING_MAX} characters looks like content, not a pointer')
        if has_cite and not str(o['citation']).startswith('https://'):
            errs.append(f'EV-003 {rid}: citation must be a public https URL')
        if is_real(o) and not has_cite:
            errs.append(f'EV-004 {rid}: a real EvidenceRecord must cite a publicly released report (citation), not only a hash')

    for o in objects:
        if o.get('type') in THREAD_TYPES and is_real(o) and o.get('evidence_grade') not in ('confirmed', 'reported'):
            errs.append(f'DT-002 {o.get("id")}: real digital-thread records must be graded confirmed or reported; show gaps, do not infer')

    seen = {}
    for l in links:
        if l.get('type') != 'underwent':
            continue
        rid = l.get('id')
        src = l.get('from')
        if tier == 'public' and is_real(l) and 'sequence' in l:
            errs.append(f'DT-003 {rid}: public tier real underwent link must not carry a sequence')
        if 'sequence' not in l:
            if not (tier == 'public' and is_real(l)):
                errs.append(f'DT-004 {rid}: underwent link needs a sequence')
        else:
            key = (src, l.get('sequence'))
            if key in seen:
                errs.append(f'DT-001 {rid}: duplicate sequence {l.get("sequence")} for {src}')
            seen[key] = rid

    for o in objects:
        if o.get('type') != 'CriticalItem':
            continue
        rid = o.get('id')
        if o.get('synthetic') is not True:
            errs.append(f'CI-001 {rid}: CriticalItem must be synthetic: true')
        target = by_id.get(o.get('target'))
        if target is not None and is_real(target):
            errs.append(f'CI-003 {rid}: CriticalItem target reaches a real record')
        for key in ('flags', 'alternate'):
            vals = o.get(key)
            if vals is None:
                continue
            if not isinstance(vals, list):
                vals = [vals]
            for v in vals:
                r = by_id.get(v)
                if r is not None and is_real(r):
                    errs.append(f'CI-002 {rid}: {key} reaches a real record')
        flags = set(o.get('flags') or [])
        if 'no_alternate' in flags and o.get('alternate'):
            errs.append(f'CI-004 {rid}: flag no_alternate but an alternate is linked')
        if 'missing_evidence' in flags:
            has = any(l.get('type') == 'evidenced_by' and l.get('from') == o.get('target') for l in links)
            if has:
                errs.append(f'CI-004 {rid}: flag missing_evidence but the target has evidence')
    return errs


UNIT = re.compile(r'(?<![\w.])\d+(?:[.,]\d+)?\s?(?:mm|cm|km|µm|um|nm|kg|mg|kN|MPa|kPa|Pa|bar|psi|°C|rpm|kHz|MHz|Hz|ms|µs|kW|MW|kJ|MJ|ml|ft|lb|lbf|Nm|N·m|m|g|t|N|K|s|V|A|W|J|L|in)\b', re.I)
TOL = re.compile(r'±\s?\d|\+/-|\+\s?/\s?-')
RANGE = re.compile(r'\d+\s?[-–—]\s?\d+')
ENCODED = re.compile(r'\b\d{1,3}(?:[ _]\d{3})+\b|0x[0-9A-Fa-f]+|\d+\.\d+[eE][+-]?\d+')
LOOKALIKE = re.compile(r'[×÷−–—°µΩ０-９]')
TEXT_FIELDS = {'name', 'item', 'citation_section', 'issuer', 'part_number', 'serial', 'lot_number', 'revision', 'title', 'description'}
IDENT_FIELDS = {'part_number', 'serial', 'lot_number', 'revision'}


def check_technical(objects, links):
    '''Reject technical data smuggled through free text or identifiers (red-team rules).'''
    errs = []
    for r in objects + links:
        rid = r.get('id')
        for f in TEXT_FIELDS:
            v = r.get(f)
            if not isinstance(v, str):
                continue
            if f in IDENT_FIELDS:
                if UNIT.search(v) or TOL.search(v):
                    errs.append(f'RT-005 {rid}.{f}: identifier looks like it carries a technical value: {v!r}')
                continue
            if UNIT.search(v):
                errs.append(f'RT-001 {rid}.{f}: number with engineering unit: {v!r}')
            if TOL.search(v) or RANGE.search(v):
                errs.append(f'RT-002 {rid}.{f}: tolerance or range: {v!r}')
            if ENCODED.search(v):
                errs.append(f'RT-003 {rid}.{f}: encoded or split numeric value: {v!r}')
            if LOOKALIKE.search(v):
                errs.append(f'RT-004 {rid}.{f}: look-alike character: {v!r}')
    return errs


def validate(path, onto, tier='public'):
    data = load(path) or {}
    errors = []
    objects = data.get('objects') or []
    links = data.get('links') or []
    if not isinstance(objects, list):
        errors.append(f'{path}: objects must be a list')
        objects = []
    if not isinstance(links, list):
        errors.append(f'{path}: links must be a list')
        links = []
    known_ids = {r.get('id') for r in objects + links if isinstance(r, dict)}
    obj_schema = onto.get('objects', {})
    lnk_schema = onto.get('links', {})
    reserved = set(onto.get('reserved', [])) | RESERVED
    for r in objects:
        if not isinstance(r, dict):
            errors.append(f'{path}: object entry is not a mapping')
            continue
        t = r.get('type')
        if t not in obj_schema:
            errors.append(f'{r.get("id")}: unknown object type {t!r}')
        else:
            check_props(r, obj_schema[t], str(r.get('id')), errors, known_ids, reserved)
    for r in links:
        if not isinstance(r, dict):
            errors.append(f'{path}: link entry is not a mapping')
            continue
        t = r.get('type')
        if t not in lnk_schema:
            errors.append(f'{r.get("id")}: unknown link type {t!r}')
        else:
            check_props(r, lnk_schema[t], str(r.get('id')), errors, known_ids, reserved)
    clean = [r for r in objects + links if isinstance(r, dict)]
    if any(is_real(r) for r in clean):
        errors += check_public_data(path, clean)
    errors += check_thread([r for r in objects if isinstance(r, dict)], [r for r in links if isinstance(r, dict)], tier)
    errors += check_technical([r for r in objects if isinstance(r, dict)], [r for r in links if isinstance(r, dict)])
    return errors


def main(argv):
    tier = 'public'
    args = list(argv)
    if '--tier' in args:
        i = args.index('--tier')
        tier = args[i + 1]
        del args[i:i + 2]
    paths = [Path(a) for a in args] or [ROOT / 'examples' / 'synthetic-example.yaml']
    onto = load(ROOT / 'schema' / 'openchokepoint.yaml')
    failed = False
    for p in paths:
        errs = validate(p, onto, tier)
        for e in errs:
            print(e)
        failed = failed or bool(errs)
    return 1 if failed else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
