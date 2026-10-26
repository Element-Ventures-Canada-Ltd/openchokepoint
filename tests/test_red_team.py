#!/usr/bin/env python3
# Handling: Unclassified — public
# SPDX-License-Identifier: Apache-2.0
'''Run the adversarial red-team corpus against tools/validate.py.'''
import copy
import datetime
import sys
import tempfile
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'tools'))
import validate as V  # noqa: E402

ONTO = V.load(ROOT / 'schema' / 'openchokepoint.yaml')
BASE = {'evidence_grade': 'confirmed', 'sources': ['https://example.org/synthetic/test'],
        'as_of': datetime.date(2026, 10, 7), 'lifecycle': 'active', 'synthetic': True}


def rec(rtype, rid, **kw):
    r = {'type': rtype, 'id': rid, **copy.deepcopy(BASE)}
    r.update(kw)
    return r


def run(objects, links):
    with tempfile.TemporaryDirectory(dir=ROOT / 'examples', prefix='.rt-') as d:
        path = Path(d) / 'instance.yaml'
        path.write_text(yaml.safe_dump({'objects': objects, 'links': links}, sort_keys=False), encoding='utf-8')
        return V.validate(path, ONTO)


class RedTeam(unittest.TestCase):
    def test_cases(self):
        cases = yaml.safe_load((ROOT / 'tests' / 'red-team' / 'cases.yaml').read_text(encoding='utf-8'))
        for c in cases:
            if c['kind'] == 'identifier':
                objects = [rec('Component', 'cmp-1', part_number=c['value'], revision='A', component_kind='rotor')]
            else:
                objects = [rec('Entity', 'ent-1', name=c['value'], entity_kind='company',
                               incorporation_jurisdiction='CA', controlling_jurisdiction='CA')]
            errs = run(objects, [])
            if c['expect'] == 'reject':
                self.assertTrue(any(e.startswith(c['rule']) for e in errs), (c, errs))
            else:
                self.assertFalse(any(e.startswith('RT-') for e in errs), (c, errs))


if __name__ == '__main__':
    unittest.main()
