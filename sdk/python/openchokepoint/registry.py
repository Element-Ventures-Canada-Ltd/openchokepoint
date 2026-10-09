# Handling: Unclassified — public
# SPDX-License-Identifier: Apache-2.0
"""Load an OpenChokepoint instance file and answer graph questions about it.

Read-only by design: the SDK never writes records, never fills a gap and never
infers an order that the file does not state.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, Iterator

import yaml

ENV_ROOT = "OPENCHOKEPOINT_ROOT"


def find_root(start: str | os.PathLike | None = None) -> Path:
    """Locate the OpenChokepoint checkout that holds schema/openchokepoint.yaml.

    Order: the OPENCHOKEPOINT_ROOT environment variable, then the folders above
    `start` (default: this file). Raises FileNotFoundError if none is found.
    """
    candidates = []
    if os.environ.get(ENV_ROOT):
        candidates.append(Path(os.environ[ENV_ROOT]))
    here = Path(start or __file__).resolve()
    candidates.extend([here, *here.parents])
    for c in candidates:
        if (c / "schema" / "openchokepoint.yaml").is_file() and (c / "tools" / "validate.py").is_file():
            return c
    raise FileNotFoundError(
        "Could not find an OpenChokepoint checkout (schema/openchokepoint.yaml and tools/validate.py). "
        f"Set {ENV_ROOT} to the repository folder."
    )


@dataclass(frozen=True)
class Record:
    """One object or link from an instance file. `data` is the record exactly as written."""

    data: dict = field(repr=False)

    @property
    def id(self) -> str:
        return self.data.get("id")

    @property
    def type(self) -> str:
        return self.data.get("type")

    @property
    def name(self) -> str | None:
        return self.data.get("name")

    @property
    def synthetic(self) -> bool:
        """True only when the record says `synthetic: true`. Anything else is treated as real."""
        return self.data.get("synthetic") is True

    def get(self, key, default=None):
        return self.data.get(key, default)

    def __getitem__(self, key):
        return self.data[key]


class Registry:
    """An in-memory view of one instance file: objects, links and the graph between them."""

    def __init__(self, objects: Iterable[dict], links: Iterable[dict], path: Path | None = None):
        self.path = path
        self.objects = [Record(o) for o in objects or []]
        self.links = [Record(l) for l in links or []]
        self._by_id = {r.id: r for r in self.objects + self.links}

    @classmethod
    def load(cls, path: str | os.PathLike) -> "Registry":
        p = Path(path)
        with open(p, encoding="utf-8") as fh:
            data = yaml.safe_load(fh) or {}
        return cls(data.get("objects", []), data.get("links", []), path=p)

    # ---- lookup ----
    def get(self, record_id: str) -> Record | None:
        return self._by_id.get(record_id)

    def of_type(self, record_type: str) -> list[Record]:
        return [r for r in self.objects + self.links if r.type == record_type]

    def links_from(self, record_id: str, link_type: str | None = None) -> list[Record]:
        return [l for l in self.links if l.get("from") == record_id and (link_type is None or l.type == link_type)]

    def links_to(self, record_id: str, link_type: str | None = None) -> list[Record]:
        return [l for l in self.links if l.get("to") == record_id and (link_type is None or l.type == link_type)]

    def targets(self, record_id: str, link_type: str) -> list[Record]:
        return [self._by_id[l.get("to")] for l in self.links_from(record_id, link_type) if l.get("to") in self._by_id]

    def sources(self, record_id: str, link_type: str) -> list[Record]:
        return [self._by_id[l.get("from")] for l in self.links_to(record_id, link_type) if l.get("from") in self._by_id]

    # ---- composition ----
    @property
    def is_synthetic(self) -> bool:
        """True when every record in the file is marked synthetic."""
        return all(r.synthetic for r in self.objects + self.links)

    def real_records(self) -> list[Record]:
        return [r for r in self.objects + self.links if not r.synthetic]

    # ---- the digital thread ----
    def steps_for(self, serial_id: str) -> tuple[list[tuple[int | None, Record]], bool]:
        """Process steps a SerialItem underwent.

        Returns (steps, ordered). When every step link carries a sequence, steps come back in
        that order and `ordered` is True. Otherwise they come back in file order with
        `ordered` False: the public tier records that steps happened, not their order, and the
        SDK never infers one.
        """
        out = []
        for l in self.links_from(serial_id, "underwent"):
            step = self._by_id.get(l.get("to"))
            if step is not None:
                out.append((l.get("sequence"), step))
        ordered = bool(out) and all(seq is not None for seq, _ in out)
        if ordered:
            out.sort(key=lambda pair: pair[0])
        return out, ordered

    def evidence_for(self, step_id: str) -> list[Record]:
        return self.targets(step_id, "evidenced_by")

    def steps_without_evidence(self) -> list[Record]:
        """ProcessSteps with no evidenced_by link. A gap shown, never a gap filled."""
        evidenced = {l.get("from") for l in self.links if l.type == "evidenced_by"}
        return [s for s in self.of_type("ProcessStep") if s.id not in evidenced]

    def __iter__(self) -> Iterator[Record]:
        return iter(self.objects + self.links)

    def __len__(self) -> int:
        return len(self.objects) + len(self.links)
