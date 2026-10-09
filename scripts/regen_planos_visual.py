#!/usr/bin/env python3
"""Regenerate (or check) the visual section of docs/initiatives/PLANOS-AUTONOMOS.md.

The master table in that doc is the source of truth; the embedded Mermaid graph,
Kanban board and action plan are generated from it with planwright. This script
keeps them from drifting:

    python scripts/regen_planos_visual.py           # rewrite the section in place
    python scripts/regen_planos_visual.py --check    # exit 1 if it is out of date

CI runs it with --check, so a change to the plan table that forgets to refresh
the diagrams fails the build. Pure stdlib + the bundled planwright engine.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "oss" / "planwright" / "src"
DOC = ROOT / "docs" / "initiatives" / "PLANOS-AUTONOMOS.md"

if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from planwright.mermaid import render_board, render_deps
from planwright.parse import parse_plan
from planwright.report import render_action

# The generated block lives between this heading and the next "## " heading.
START = "## Vista de gestão (gerada pelo planwright)"
NEXT = "## Vistas por projeto"


def build_section() -> str:
    plan = parse_plan(str(DOC))
    parts = [
        START,
        "",
        "> Gerada por `scripts/regen_planos_visual.py` a partir da tabela mestra.",
        "> **Não editar à mão** — correr o script; o CI falha se divergir da tabela.",
        "> Os diagramas Mermaid renderizam no GitHub.",
        "",
        "### Grafo de dependências (o que prende o quê · cor = estado)",
        "",
        render_deps(plan),
        "",
        "### Board por estado (Kanban)",
        "",
        render_board(plan),
        "",
        "### Plano de ação (`planwright action`)",
        "",
        "```",
        render_action(plan),
        "```",
        "",
    ]
    return "\n".join(parts)


def rewrite(text: str, section: str) -> str:
    pat = re.compile(re.escape(START) + r".*?(?=" + re.escape(NEXT) + ")", re.DOTALL)
    if not pat.search(text):
        raise SystemExit(f"markers not found ({START!r} … {NEXT!r}) in {DOC}")
    return pat.sub(section + "\n", text)


def main(argv: list[str]) -> int:
    check = "--check" in argv
    text = DOC.read_text(encoding="utf-8")
    new_text = rewrite(text, build_section())
    if check:
        if text != new_text:
            print(
                "PLANOS-AUTONOMOS.md visual section is out of date — run:\n"
                "  python scripts/regen_planos_visual.py",
                file=sys.stderr,
            )
            return 1
        print("visual section up to date")
        return 0
    DOC.write_text(new_text, encoding="utf-8")
    print("visual section regenerated")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
