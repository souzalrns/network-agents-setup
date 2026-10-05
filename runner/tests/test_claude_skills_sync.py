""".claude/skills/ e uma copia gerada de skills/meta/ + skills/claude/ (scripts/sync_claude_skills.py).

Garante que as skills de tecnica do setup estao mesmo carregaveis nas sessoes Claude
Code deste repo, e que a copia nao diverge da fonte.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]


def _sync_module():
    spec = importlib.util.spec_from_file_location("sync_claude_skills", REPO / "scripts" / "sync_claude_skills.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_claude_skills_em_dia_com_a_fonte():
    mod = _sync_module()
    assert mod.drift() == [], "correr: python scripts/sync_claude_skills.py"


def test_nome_repetido_fica_a_versao_do_setup():
    mod = _sync_module()
    plan = mod.planned()
    assert plan["using-agent-skills"].relative_to(REPO).as_posix() == "skills/meta/using-agent-skills"


def test_skills_de_dominio_ficam_de_fora():
    names = {d.name for d in (REPO / ".claude" / "skills").iterdir() if d.is_dir()}
    dominio = {d.name for v in ("marketing", "design", "security") for d in (REPO / "skills" / v).iterdir() if d.is_dir()}
    assert names and not (names & dominio)
    assert {"meta-workflow", "receiving-code-review", "test-driven-development"} <= names
