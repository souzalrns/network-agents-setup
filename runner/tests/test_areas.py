"""E7: config/areas.yaml tem de bater com agents/**/*.agent.md."""
from __future__ import annotations

from pathlib import Path

import pytest

from plan_runner.areas import main, validate_areas

REPO_ROOT = Path(__file__).resolve().parents[2]


def test_repo_real_e_valido():
    assert validate_areas(REPO_ROOT) == []


def _repo(tmp_path: Path, areas_yaml: str, agents: dict[str, str]) -> Path:
    (tmp_path / "config").mkdir()
    (tmp_path / "config" / "areas.yaml").write_text(areas_yaml, encoding="utf-8")
    for rel, aid in agents.items():
        p = tmp_path / "agents" / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(f"---\nid: {aid}\naction: x\n---\n# {aid}\n", encoding="utf-8")
    return tmp_path


AGENTS = {"eng/dev.agent.md": "eng.dev", "meta/plan.agent.md": "meta.plan"}
VALID = """
areas:
  - id: software
    description: Software.
    agents: [eng.dev]
    horizontals: [meta.plan]
  - id: horizontal
    description: Transversais.
    agents: [meta.plan]
    horizontals: []
"""


def test_fixture_valida(tmp_path):
    assert validate_areas(_repo(tmp_path, VALID, AGENTS)) == []


@pytest.mark.parametrize(
    "yaml_text, esperado",
    [
        (VALID.replace("agents: [eng.dev]", "agents: [eng.dev, eng.fantasma]"),
         "agents[] refere `eng.fantasma`, que não existe"),
        (VALID.replace("agents: [eng.dev]", "agents: []"), "agente órfão `eng.dev`"),
        (VALID.replace("agents: [meta.plan]", "agents: [meta.plan, eng.dev]"),
         "`eng.dev` está em agents[] de mais de uma área"),
        (VALID.replace("horizontals: [meta.plan]", "horizontals: [meta.inexistente]"),
         "horizontals[] refere `meta.inexistente`"),
        (VALID.replace("id: horizontal", "id: software"), "id de área repetido"),
        (VALID.replace("    description: Software.\n", ""), "área `software`: falta `description`"),
        (VALID.replace("horizontals: []", "horizontals: meta.plan"), "`horizontals` tem de ser uma lista"),
        ("areas: [\n  - id: x", "não é YAML legível"),
        # Router (D2): keywords, routing, budget, hitl, delegation
        (VALID.replace("    agents: [eng.dev]\n", "    agents: [eng.dev]\n    keywords: [Código]\n"),
         "keyword `Código` tem de estar em minúsculas, sem acentos"),
        (VALID.replace("    agents: [eng.dev]\n", "    agents: [eng.dev]\n    keywords: [plano]\n")
              .replace("    agents: [meta.plan]\n", "    agents: [meta.plan]\n    keywords: [plano]\n"),
         "keyword `plano` está em mais de uma área"),
        (VALID.replace("    agents: [eng.dev]\n", "    agents: [eng.dev]\n    keywords: codigo\n"),
         "`keywords` tem de ser uma lista"),
        ("routing:\n  area_min_confidence: 1.5\n" + VALID, "routing.area_min_confidence tem de ser um número"),
        ("routing:\n  fallback_area: nenhuma\n" + VALID, "routing.fallback_area `nenhuma` não é uma área"),
        (VALID.replace("    agents: [eng.dev]\n", "    agents: [eng.dev]\n    budget: 3\n"),
         "`budget` tem de ser null ou {max_steps"),
        (VALID.replace("    agents: [eng.dev]\n", "    agents: [eng.dev]\n    hitl: sempre\n"),
         "`hitl` tem de ser null ou required"),
        (VALID.replace("    agents: [eng.dev]\n", "    agents: [eng.dev]\n    delegation: talvez\n"),
         "`delegation` tem de ser um de auto, agent, plan"),
        ("version: 1\n", "falta a lista `areas:`"),
    ],
)
def test_divergencias_falham(tmp_path, yaml_text, esperado):
    errors = validate_areas(_repo(tmp_path, yaml_text, AGENTS))
    assert any(esperado in e for e in errors), errors


def test_agente_sem_id_ou_id_repetido(tmp_path):
    agents = {**AGENTS, "eng/copia.agent.md": "eng.dev"}
    root = _repo(tmp_path, VALID, agents)
    (root / "agents" / "eng" / "semid.agent.md").write_text("---\naction: y\n---\n", encoding="utf-8")
    errors = validate_areas(root)
    assert any("id `eng.dev` repetido" in e for e in errors), errors
    assert any("semid.agent.md: frontmatter sem `id:`" in e for e in errors), errors


def test_cli_codigo_de_saida(tmp_path, capsys):
    assert main([str(_repo(tmp_path, VALID, AGENTS))]) == 0
    assert "válido: 2 áreas" in capsys.readouterr().out
    bad = tmp_path / "bad"
    bad.mkdir()
    assert main([str(_repo(bad, VALID.replace("agents: [eng.dev]", "agents: []"), AGENTS))]) == 1
    assert "agente órfão `eng.dev`" in capsys.readouterr().err


def test_campos_do_router_validos(tmp_path):
    yaml_text = "routing:\n  area_min_confidence: 0.7\n  fallback_area: horizontal\n" + VALID.replace(
        "    agents: [eng.dev]\n",
        "    agents: [eng.dev]\n    keywords: [codigo, pull request]\n    budget: {max_steps: 4}\n"
        "    hitl: required\n    delegation: plan\n",
    )
    assert validate_areas(_repo(tmp_path, yaml_text, AGENTS)) == []


def test_normalize():
    from plan_runner.areas import normalize

    assert normalize("Revisão do CÓDIGO e Ecrã") == "revisao do codigo e ecra"
