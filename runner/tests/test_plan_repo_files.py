"""`repo_files:` dos planos reais (SEC-1) e o pack de design (F3c-DESIGN-1, opção A).

O worker não executa tools (AU-20): o `tools_allowed: [read_repo_file]` é declarativo. O que
um passo lê do repo entra no prompt por `repo_files`. Estes testes garantem, sem rede nem BD:
- cada `repo_files` de cada plano em docs/orchestration/ existe, não está nas exclusões
  fixas e cabe no limite do passo (nada é cortado em silêncio);
- cada ficheiro de `docs/knowledge/design/` que uma skill de design nomeia chega ao passo
  dessa skill nos 2 planos de design.
"""

from __future__ import annotations

import re
from pathlib import Path, PurePosixPath

import pytest
import yaml

from plan_runner.repo_files import MAX_TOTAL_BYTES, denied

REPO_ROOT = Path(__file__).resolve().parents[2]
PLANS = sorted((REPO_ROOT / "docs/orchestration").rglob("*.plan.yaml"))
DESIGN_PLANS = [
    "docs/orchestration/design/templates/design-flow.plan.yaml",
    "docs/orchestration/design/templates/examples/design-flow-demo.plan.yaml",
]
SKILL_OF_ACTION = {"ux_flow": "ux_flow", "ui_spec": "ui_spec", "ux_writing": "ux_writing"}


def _steps_with_repo_files():
    for plan in PLANS:
        data = yaml.safe_load(plan.read_text(encoding="utf-8")) or {}
        for step in data.get("steps") or []:
            if "repo_files" in step:
                yield plan.relative_to(REPO_ROOT).as_posix(), step


CASES = list(_steps_with_repo_files())


def test_ha_planos_com_repo_files():
    plans = {p for p, _ in CASES}
    assert set(DESIGN_PLANS) <= plans
    assert "docs/orchestration/security/templates/examples/security-audit-demo.plan.yaml" in plans


@pytest.mark.parametrize(("plan", "step"), CASES, ids=[f"{p}:{s['id']}" for p, s in CASES])
def test_repo_files_existem_sao_permitidos_e_cabem(plan, step):
    entries = step["repo_files"]
    assert isinstance(entries, list) and entries, f"{plan}:{step['id']}: lista vazia ou não é lista"
    total = 0
    for rel in entries:
        path = REPO_ROOT / rel
        assert not PurePosixPath(rel).is_absolute() and ".." not in PurePosixPath(rel).parts, rel
        assert path.is_file(), f"{plan}:{step['id']}: {rel} não existe"
        assert denied(PurePosixPath(rel)) is None, f"{plan}:{step['id']}: {rel} está nas exclusões"
        total += path.stat().st_size
    assert total <= MAX_TOTAL_BYTES, f"{plan}:{step['id']}: {total} B > {MAX_TOTAL_BYTES} (seria cortado)"


@pytest.mark.parametrize("plan", DESIGN_PLANS)
def test_passos_de_design_recebem_o_que_a_skill_nomeia(plan):
    data = yaml.safe_load((REPO_ROOT / plan).read_text(encoding="utf-8"))
    by_action = {s["action"]: set(s.get("repo_files") or []) for s in data["steps"]}
    for action, skill in SKILL_OF_ACTION.items():
        text = (REPO_ROOT / f"skills/design/{skill}/SKILL.md").read_text(encoding="utf-8")
        named = set(re.findall(r"`(?:docs/knowledge/design/)?([a-z0-9-]+\.md)`", text))
        named = {f"docs/knowledge/design/{n}" for n in named if (REPO_ROOT / "docs/knowledge/design" / n).is_file()}
        assert named, f"a skill {skill} já não nomeia ficheiros do pack: rever o teste"
        assert named <= by_action[action], f"{plan}: {action} sem {sorted(named - by_action[action])}"
    # o crítico: o próprio pack diz que nielsen-heuristics e a11y-baseline são para o design_critic
    for rel in ("docs/knowledge/design/nielsen-heuristics.md", "docs/knowledge/design/a11y-baseline.md"):
        assert "design_critic" in (REPO_ROOT / rel).read_text(encoding="utf-8")
        assert rel in by_action["design_critic"]
