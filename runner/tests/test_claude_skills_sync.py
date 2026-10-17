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


def test_skills_fixadas_pelo_skill_scout_ficam_e_nao_contam_como_divergencia(tmp_path, monkeypatch):
    mod = _sync_module()
    target = tmp_path / ".claude" / "skills"
    monkeypatch.setattr(mod, "REPO", tmp_path)
    monkeypatch.setattr(mod, "TARGET", target)
    monkeypatch.setattr(mod, "README", target / "README.md")
    monkeypatch.setattr(mod, "LOCK", tmp_path / "skill-scout.lock.json")
    monkeypatch.setattr(mod, "planned", lambda: {})
    (target / "wizard").mkdir(parents=True)
    (target / "wizard" / "SKILL.md").write_text("x", encoding="utf-8")
    (target / "solta").mkdir()
    assert "a mais: wizard" in mod.drift()  # sem lock é uma pasta a mais
    (tmp_path / "skill-scout.lock.json").write_text(
        '{"version": 1, "skills": {".claude/skills/wizard": {"name": "wizard"}}, "waivers": []}', encoding="utf-8"
    )
    assert "a mais: wizard" not in mod.drift() and "a mais: solta" in mod.drift()
    mod.sync()
    assert (target / "wizard" / "SKILL.md").is_file()  # a fixada sobrevive
    assert not (target / "solta").exists()  # a solta é apagada, como antes
