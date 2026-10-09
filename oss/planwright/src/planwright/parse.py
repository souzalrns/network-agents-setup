"""Parse a plan from a Markdown file.

The plan is the first GitHub-flavoured Markdown table whose header contains at
least ``id`` and ``title``. Column names are matched case-insensitively and
accept a few aliases, so the same parser reads an English plan or a Portuguese
one. Everything outside the table (prose, headings, other tables) is ignored,
so a plan can live inside a larger document.
"""

from __future__ import annotations

from .model import Item, Plan, parse_estimate, parse_status

# Header alias → canonical column. Only id and title are required.
_COLUMN_ALIASES = {
    "id": "id",
    "title": "title",
    "task": "title",
    "titulo": "title",
    "título": "title",
    "name": "title",
    "status": "status",
    "state": "status",
    "estado": "status",
    "owner": "owner",
    "dono": "owner",
    "assignee": "owner",
    "est": "estimate",
    "estimate": "estimate",
    "estimativa": "estimate",
    "effort": "estimate",
    "size": "estimate",
    "depends": "depends",
    "depends on": "depends",
    "depends_on": "depends",
    "deps": "depends",
    "depende": "depends",
    "depende de": "depends",
    "blocked by": "depends",
    "track": "track",
    "lane": "track",
    "group": "track",
    "fase": "track",
    "phase": "track",
}


class ParseError(ValueError):
    """Raised when a plan file has no usable table or a malformed row."""


def _split_row(line: str) -> list[str]:
    """Split a Markdown table row on unescaped pipes, trimming the outer pipes."""
    s = line.strip()
    if s.startswith("|"):
        s = s[1:]
    if s.endswith("|"):
        s = s[:-1]
    return [cell.strip() for cell in s.split("|")]


def _is_separator(cells: list[str]) -> bool:
    """A separator row is all cells like ``---`` / ``:--:``."""
    if not cells:
        return False
    for c in cells:
        stripped = c.replace(":", "").replace("-", "").strip()
        if stripped or "-" not in c:
            return False
    return True


def _map_header(cells: list[str]) -> dict[str, int] | None:
    """Return {canonical_column: index} if this looks like a plan header."""
    mapping: dict[str, int] = {}
    for idx, cell in enumerate(cells):
        canon = _COLUMN_ALIASES.get(cell.strip().lower())
        if canon and canon not in mapping:
            mapping[canon] = idx
    if "id" in mapping and "title" in mapping:
        return mapping
    return None


def parse_text(text: str, *, source: str = "<text>") -> Plan:
    """Parse plan text. Finds the first table with id+title and reads its rows."""
    lines = text.splitlines()
    header: dict[str, int] | None = None
    header_width = 0
    header_lineno = 0
    items: list[Item] = []
    seen_separator = False

    for lineno, raw in enumerate(lines, start=1):
        if "|" not in raw:
            if header is not None:
                break  # table ended at the first non-table line
            continue
        cells = _split_row(raw)
        if header is None:
            maybe = _map_header(cells)
            if maybe is not None:
                header = maybe
                header_width = len(cells)
                header_lineno = lineno
            continue
        if not seen_separator:
            # The row right after the header must be the separator.
            if _is_separator(cells):
                seen_separator = True
                continue
            raise ParseError(
                f"{source}:{lineno}: expected a table separator row (|---|---|) "
                f"after the header on line {header_lineno}"
            )
        if _is_separator(cells):
            continue
        items.append(_row_to_item(cells, header, header_width, lineno, source))

    if header is None:
        raise ParseError(
            f"{source}: no plan table found (need a Markdown table with at least 'ID' and 'Title' columns)"
        )
    return Plan(items)


def _cell(cells: list[str], header: dict[str, int], key: str) -> str:
    idx = header.get(key)
    if idx is None or idx >= len(cells):
        return ""
    return cells[idx]


def _row_to_item(cells: list[str], header: dict[str, int], header_width: int, lineno: int, source: str) -> Item:
    if len(cells) != header_width:
        raise ParseError(
            f"{source}:{lineno}: row has {len(cells)} cells but the header has "
            f"{header_width}; every row must have the same columns (no bare '|' inside a cell)"
        )
    item_id = _cell(cells, header, "id")
    if not item_id:
        raise ParseError(f"{source}:{lineno}: row has an empty ID")
    title = _cell(cells, header, "title")

    status_cell = _cell(cells, header, "status") or "todo"
    try:
        status = parse_status(status_cell)
    except ValueError as exc:
        raise ParseError(f"{source}:{lineno}: {exc}") from exc

    try:
        estimate = parse_estimate(_cell(cells, header, "estimate"))
    except ValueError as exc:
        raise ParseError(f"{source}:{lineno}: {exc}") from exc

    from .model import _split_deps  # local import keeps model's helper private-ish

    depends = _split_deps(_cell(cells, header, "depends"))
    return Item(
        id=item_id,
        title=title,
        status=status,
        owner=_cell(cells, header, "owner"),
        estimate_hours=estimate,
        depends=depends,
        track=_cell(cells, header, "track"),
        line=lineno,
    )


def parse_plan(path: str) -> Plan:
    """Parse a plan from a file path."""
    with open(path, encoding="utf-8") as fh:
        return parse_text(fh.read(), source=path)
