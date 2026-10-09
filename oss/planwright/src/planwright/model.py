"""The data model: a Plan is an ordered set of work Items.

Estimates are parsed into hours so the critical path is a single comparable
number. Accepted forms: ``2h``, ``3d``, ``1w`` (and ``0.5d``), or the sizes
``S`` / ``M`` / ``L`` / ``XL`` which map to sensible day defaults. ``-`` or an
empty cell means "no estimate yet".
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum

# One working day = 8h; one week = 5 working days. Used to normalise estimates.
HOURS_PER_DAY = 8.0
HOURS_PER_WEEK = HOURS_PER_DAY * 5

# T-shirt sizes → hours, for teams that estimate in sizes rather than durations.
SIZE_HOURS = {
    "S": 0.5 * HOURS_PER_DAY,
    "M": 2 * HOURS_PER_DAY,
    "L": 1 * HOURS_PER_WEEK,
    "XL": 2 * HOURS_PER_WEEK,
}

_DURATION_RE = re.compile(r"^\s*(\d+(?:\.\d+)?)\s*([hdw])\s*$", re.IGNORECASE)
_UNIT_HOURS = {"h": 1.0, "d": HOURS_PER_DAY, "w": HOURS_PER_WEEK}

# Cells that mean "empty" in a Markdown table.
EMPTY_TOKENS = {"", "-", "—", "–", "n/a", "na", "tbd", "?"}


class Status(str, Enum):
    """Lifecycle of a work item. Kept small and generic so any team can map
    its own vocabulary onto it."""

    TODO = "todo"
    DOING = "doing"
    BLOCKED = "blocked"
    DONE = "done"

    @property
    def completed(self) -> bool:
        return self is Status.DONE

    @property
    def started(self) -> bool:
        """True once work has been committed to the item (doing or done)."""
        return self in (Status.DOING, Status.DONE)


# Aliases let a plan use its own words (including Portuguese) and still parse.
_STATUS_ALIASES = {
    "todo": Status.TODO,
    "to-do": Status.TODO,
    "open": Status.TODO,
    "aberto": Status.TODO,
    "backlog": Status.TODO,
    "doing": Status.DOING,
    "wip": Status.DOING,
    "in-progress": Status.DOING,
    "in progress": Status.DOING,
    "em curso": Status.DOING,
    "blocked": Status.BLOCKED,
    "bloqueado": Status.BLOCKED,
    "waiting": Status.BLOCKED,
    "done": Status.DONE,
    "closed": Status.DONE,
    "fechado": Status.DONE,
    "shipped": Status.DONE,
}


def parse_status(raw: str) -> Status:
    key = raw.strip().lower()
    if key not in _STATUS_ALIASES:
        valid = ", ".join(sorted({s.value for s in Status}))
        raise ValueError(f"unknown status {raw!r} (expected one of: {valid}, or a known alias)")
    return _STATUS_ALIASES[key]


def parse_estimate(raw: str) -> float | None:
    """Return the estimate in hours, or None when the cell is empty.

    Raises ValueError on a non-empty cell that is neither a size nor a duration.
    """
    token = raw.strip()
    if token.lower() in EMPTY_TOKENS:
        return None
    upper = token.upper()
    if upper in SIZE_HOURS:
        return SIZE_HOURS[upper]
    m = _DURATION_RE.match(token)
    if m:
        return float(m.group(1)) * _UNIT_HOURS[m.group(2).lower()]
    raise ValueError(f"bad estimate {raw!r} (use a size S/M/L/XL or a duration like 2h, 3d, 1w, or '-' for none)")


def _split_deps(raw: str) -> list[str]:
    token = raw.strip()
    if token.lower() in EMPTY_TOKENS:
        return []
    # Accept comma-, space- or semicolon-separated ids; keep order, drop dups.
    parts = re.split(r"[,;\s]+", token)
    seen: list[str] = []
    for p in parts:
        p = p.strip()
        if p and p not in seen:
            seen.append(p)
    return seen


@dataclass
class Item:
    """One unit of work. ``line`` is the 1-based source line, for error messages."""

    id: str
    title: str
    status: Status
    owner: str = ""
    estimate_hours: float | None = None
    depends: list[str] = field(default_factory=list)
    track: str = ""
    line: int = 0

    @property
    def has_estimate(self) -> bool:
        return self.estimate_hours is not None


@dataclass
class Plan:
    """An ordered collection of items, indexed by id."""

    items: list[Item] = field(default_factory=list)

    def __post_init__(self) -> None:
        self._by_id: dict[str, Item] = {}
        for it in self.items:
            self._by_id.setdefault(it.id, it)

    def get(self, item_id: str) -> Item | None:
        return self._by_id.get(item_id)

    def has(self, item_id: str) -> bool:
        return item_id in self._by_id

    def __iter__(self):
        return iter(self.items)

    def __len__(self) -> int:
        return len(self.items)
