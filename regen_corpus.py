#!/usr/bin/env python3
"""Regenerate the boundary red-team corpus — schema-clean fixtures.

Every fixture is fictional: invented values only, example.org domain reserved
for examples, no real organization / part / parameter. The attack lives ONLY
in the smuggled value; otherwise each record is schema-valid, so the error
list for an attack case contains exactly the RT-0xx rule(s) that caught it.
"""
import datetime
import os

import yaml

os.chdir(os.path.dirname(os.path.abspath(__file__)))

D = "tests/red-team/cases"
SRC = "https://example.org/synthetic/red-team"
BASE = {"evidence_grade": "confirmed", "sources": [SRC], "as_of": datetime.date(2026, 10, 19),
        "lifecycle": "active", "synthetic": True}


def rec(rtype, rid, **kw):
    r = {"type": rtype, "id": rid, **BASE}
    r.update(kw)
    return r


COMP = dict(name="Demo impeller blank", part_number="PN-100", revision="A",
            component_kind="impeller")
EV = dict(record_kind="inspection_report", issuer="Example Issuer",
          issued_on=datetime.date(2026, 4, 1), citation="https://example.org/report/9")

cases = {
    # RT-001 — engineering-unit payloads in free-text fields
    "RT-001a-unit-in-name": {"objects": [rec("Component", "comp-1",
                                             **{**COMP, "name": "Inducer forging batch, min 325 MPa yield"})],
                             "links": []},
    "RT-001b-unit-in-lot-number": {"objects": [rec("MaterialLot", "lot-1",
                                                   name="Demo supplier lot",
                                                   lot_number="LOT-2026-325MPa-HT",
                                                   material_class="forging")], "links": []},
    "RT-001c-unit-in-issuer": {"objects": [rec("EvidenceRecord", "ev-1",
                                               **{**EV, "issuer": "Acme Test Labs, quench 60 °C"})],
                               "links": []},
    # RT-002 — URL query-string smuggling
    "RT-002a-params-in-citation": {"objects": [rec("EvidenceRecord", "ev-2",
                                                   **{**EV, "citation": "https://example.org/report/9?yield_min=325MPa&temp=-54C"})],
                                   "links": []},
    # RT-003 — invisible / look-alike characters
    "RT-003a-zero-width-split": {"objects": [rec("Component", "comp-3",
                                                 **{**COMP, "name": "Inducer 325​ MPa yield"})],
                                 "links": []},
    "RT-003b-fullwidth-digits": {"objects": [rec("SerialItem", "ser-1", name="Demo blank",
                                                 serial="３２５ ＭＰａ")], "links": []},
    "RT-003c-cyrillic-homoglyph": {"objects": [rec("SerialItem", "ser-2", name="Demo blank",
                                                   serial="SN-325-МРа")], "links": []},
    # RT-004 — encoded payloads
    "RT-004a-base64-in-lot": {"objects": [rec("MaterialLot", "lot-4", name="Demo supplier lot",
                                              lot_number="MzI1IE1QYSB5aWVsZA==",
                                              material_class="forging")], "links": []},
    "RT-004b-split-digits": {"objects": [rec("SerialItem", "ser-4", name="Demo blank",
                                             serial="3-2-5 M-P-A")], "links": []},
    # RT-005 — specification language in identifiers
    "RT-005a-tolerance-in-part-number": {"objects": [rec("Component", "comp-5",
                                                         name="Demo impeller blank",
                                                         part_number="PN-4421-TOL-0.02mm",
                                                         revision="A", component_kind="impeller")],
                                         "links": []},
    "RT-005b-range-in-serial": {"objects": [rec("SerialItem", "ser-5", name="Demo blank",
                                                serial="SN-001-range-(-54C-to-177C)")],
                                "links": []},
    # RT-006 — citation_section carrying parameters
    "RT-006a-section-carries-values": {"objects": [rec("EvidenceRecord", "ev-6",
                                                       **{**EV, "citation": "https://example.org/report/12",
                                                          "citation_section": "Table 5, row 12 (min 325 MPa, max 360 MPa)"})],
                                       "links": []},
    # RT-007 — process heat-words in identifiers
    "RT-007a-process-word-in-part-number": {"objects": [rec("Component", "comp-7",
                                                            name="Demo impeller blank",
                                                            part_number="PN-77-HEATTREAT-AGED-T73",
                                                            revision="A", component_kind="impeller")],
                                            "links": []},
    # Negative controls — must stay accepted (false-positive guard)
    "NEG-1-clean-identifier": {"expected": "accept",
                               "objects": [rec("Component", "comp-n1", name="Demo impeller supplier",
                                               part_number="PN-2026-0007", revision="A",
                                               component_kind="impeller"),
                                           rec("MaterialLot", "lot-n1", name="Demo supplier lot 718 alloy",
                                               lot_number="LOT-88-0001", material_class="bar")],
                               "links": []},
    "NEG-2-clean-url-with-query": {"expected": "accept",
                                   "objects": [rec("EvidenceRecord", "ev-n2",
                                                   **{**EV, "citation": "https://example.org/report?id=889"})],
                                   "links": []},
    "NEG-3-clean-section-ref": {"expected": "accept",
                                "objects": [rec("EvidenceRecord", "ev-n3",
                                                **{**EV, "citation": "https://example.org/report/12",
                                                   "citation_section": "Section 7.3"})],
                                "links": []},
}

for name, c in cases.items():
    doc = {"case": name,
           "category": name.split("-")[0],
           "expected": c.get("expected", "reject"),
           "expected_rule": name.split("-")[0] + "-" + name.split("-")[1][:3].rstrip("abcd"),
           "note": ("Fictional record — invented values only (example.org). "
                    "Boundary red-team corpus, issue #18 Slice C."),
           "objects": c["objects"], "links": c["links"]}
    with open(f"{D}/{name}.yaml", "w") as f:
        yaml.safe_dump(doc, f, sort_keys=False, allow_unicode=True)
print("重生成", len(cases), "个case（schema-clean）")
