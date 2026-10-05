"""Gera .claude/skills/ (skills das sessoes Claude Code neste repo) a partir de skills/.

Fonte unica: skills/meta/ (tecnicas do setup) e skills/claude/ (pack de engenharia,
sincronizado do agent-network-mcp). .claude/skills/ e uma copia gerada, como o
docs/generated/: nao editar a mao. Copias em vez de symlinks porque o Git para
Windows nao cria symlinks por omissao (core.symlinks=false).

Num nome repetido ganha a 1.a fonte (skills/meta/, a versao adaptada ao setup).
As skills de dominio (marketing, design, security) nao entram: sao papeis dos
agentes do runner, nao tecnicas para quem trabalha no repo.

Uso (a partir da raiz do repo):
    python scripts/sync_claude_skills.py          # gera
    python scripts/sync_claude_skills.py --check  # sai com 1 se estiver desactualizado
"""
from __future__ import annotations

import filecmp
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SOURCES = ("skills/meta", "skills/claude")
TARGET = REPO / ".claude" / "skills"
README = TARGET / "README.md"
README_TEXT = (
    "# `.claude/skills/` (gerado)\n\n"
    "> **Não editar à mão.** Gerado por `python scripts/sync_claude_skills.py` a partir de "
    + " e ".join(f"`{s}/`" for s in SOURCES)
    + ". Editar a skill na fonte e voltar a correr o script; o teste "
    "`runner/tests/test_claude_skills_sync.py` falha se esta pasta divergir da fonte.\n\n"
    "Num nome repetido ganha a 1.ª fonte (`skills/meta/`). As skills de domínio "
    "(marketing, design, security) ficam de fora: são papéis dos agentes do runner.\n"
)


def planned() -> dict[str, Path]:
    """{nome da skill: pasta de origem}, com a 1.a fonte a ganhar nos nomes repetidos."""
    out: dict[str, Path] = {}
    for src in SOURCES:
        for d in sorted((REPO / src).iterdir()):
            if d.is_dir() and (d / "SKILL.md").is_file() and d.name not in out:
                out[d.name] = d
    return out


def _same_tree(a: Path, b: Path) -> bool:
    if not b.is_dir():
        return False
    cmp = filecmp.dircmp(a, b)
    if cmp.left_only or cmp.right_only or cmp.funny_files:
        return False
    _, mismatch, errors = filecmp.cmpfiles(a, b, cmp.common_files, shallow=False)
    if mismatch or errors:
        return False
    return all(_same_tree(a / sub, b / sub) for sub in cmp.common_dirs)


def drift() -> list[str]:
    """Diferencas entre .claude/skills/ e a fonte (lista vazia = em dia)."""
    plan = planned()
    problems = [f"desactualizada: {n}" for n, src in plan.items() if not _same_tree(src, TARGET / n)]
    if TARGET.is_dir():
        problems += [f"a mais: {d.name}" for d in sorted(TARGET.iterdir()) if d.is_dir() and d.name not in plan]
    if not README.is_file() or README.read_text(encoding="utf-8") != README_TEXT:
        problems.append("README.md em falta ou diferente")
    return problems


def sync() -> int:
    plan = planned()
    TARGET.mkdir(parents=True, exist_ok=True)
    for d in TARGET.iterdir():
        if d.is_dir() and d.name not in plan:
            shutil.rmtree(d)
    for name, src in plan.items():
        dst = TARGET / name
        if dst.exists():
            shutil.rmtree(dst)
        shutil.copytree(src, dst)
    README.write_text(README_TEXT, encoding="utf-8")
    return len(plan)


if __name__ == "__main__":
    if "--check" in sys.argv[1:]:
        found = drift()
        for p in found:
            print(p)
        sys.exit(1 if found else 0)
    print(f"OK: {sync()} skills em {TARGET.relative_to(REPO)}")
