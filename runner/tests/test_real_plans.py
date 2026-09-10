"""Testes de integracao com os planos reais do repo.

Valida que o plan_runner suporta os 6 planos genericos em
docs/orchestration/marketing/templates/ (e examples/):

- ship-parallel       (wave paralela + HITL)
- internal-brief      (linear + HITL)
- seo-article         (linear + HITL)
- social-pack         (linear + HITL)
- approval-rounds     (3 HITLs em cadeia)
- seo-article-demo    (linear + HITL)

Nao mexe no conftest.py. Define fixtures locais para evitar
quebrar os 51 testes existentes.
"""
from __future__ import annotations

import json

import pytest

from tests.conftest import RUNNER_DIR, _load_status_safe, _run_cli

REPO_ROOT = RUNNER_DIR.parent
TPL = REPO_ROOT / "docs" / "orchestration" / "marketing" / "templates"


# (nome, path, expected_hitl_step)
REAL_PLANS = [
    ("ship-parallel",    TPL / "examples" / "ship-parallel.plan.yaml",     "hitl"),
    ("internal-brief",   TPL / "internal-brief.plan.yaml",                 "hitl"),
    ("seo-article",      TPL / "seo-article.plan.yaml",                    "hitl_publish_decision"),
    ("social-pack",      TPL / "social-pack.plan.yaml",                    "hitl"),
    ("approval-rounds",  TPL / "approval-rounds.plan.yaml",                "hitl_r1"),
    ("seo-article-demo", TPL / "examples" / "seo-article-demo.plan.yaml",  "hitl_publish_decision"),
]


@pytest.mark.parametrize("name,path,expected_hitl", REAL_PLANS, ids=[p[0] for p in REAL_PLANS])
def test_real_plan_compile_graph(name, path, expected_hitl):
    """compile-graph valida o plano e devolve waves."""
    assert path.exists(), f"Plano nao encontrado: {path}"
    proc = _run_cli(["compile-graph", str(path)], cwd=RUNNER_DIR)
    assert proc.returncode == 0, f"compile-graph falhou: {proc.stderr}"

    data = json.loads(proc.stdout)
    assert "waves" in data and isinstance(data["waves"], list)
    assert len(data["waves"]) > 0
    assert data["node_count"] > 0
    # o HITL tem de estar em interrupt_before
    assert expected_hitl in data["interrupt_before"], (
        f"HITL esperado '{expected_hitl}' nao esta em interrupt_before: "
        f"{data['interrupt_before']}"
    )


@pytest.mark.parametrize("name,path,expected_hitl", REAL_PLANS, ids=[p[0] for p in REAL_PLANS])
def test_real_plan_runs_and_pauses_at_hitl(name, path, expected_hitl, tmp_path):
    """run --mode stub pausa no HITL correto."""
    out = tmp_path / "run"
    proc = _run_cli(
        ["run", str(path), "--engine", "langgraph", "--mode", "stub", "--out", str(out)],
        cwd=RUNNER_DIR,
    )
    assert proc.returncode == 0, f"run falhou: {proc.stderr}"

    status = _load_status_safe(out)
    assert status.get("state") == "paused_human_gate"
    assert status.get("paused_at_step") == expected_hitl, (
        f"Esperado pause em '{expected_hitl}', obtido '{status.get('paused_at_step')}'"
    )


@pytest.mark.parametrize("name,path,expected_hitl", REAL_PLANS, ids=[p[0] for p in REAL_PLANS])
def test_real_plan_completed_matches_waves(name, path, expected_hitl, tmp_path):
    """completed deve ser consistente com as waves antes do HITL."""
    out = tmp_path / "run"

    # 1. Obter as waves
    proc = _run_cli(["compile-graph", str(path)], cwd=RUNNER_DIR)
    assert proc.returncode == 0
    waves = json.loads(proc.stdout)["waves"]

    # 2. Correr
    proc = _run_cli(
        ["run", str(path), "--engine", "langgraph", "--mode", "stub", "--out", str(out)],
        cwd=RUNNER_DIR,
    )
    assert proc.returncode == 0

    status = _load_status_safe(out)
    completed = set(status.get("completed") or [])

    # 3. O HITL nao deve estar em completed (esta a espera)
    assert expected_hitl not in completed, (
        f"HITL '{expected_hitl}' nao devia estar em completed: {completed}"
    )

    # 4. Cada step em completed tem de estar em alguma wave
    all_steps_in_waves = {s for wave in waves for s in wave}
    assert completed.issubset(all_steps_in_waves), (
        f"Steps em completed que nao existem em waves: "
        f"{completed - all_steps_in_waves}"
    )

    # 5. O HITL tem de estar nas waves
    assert expected_hitl in all_steps_in_waves


# ============================================================
# TESTES ESPECIFICOS
# ============================================================

def test_ship_parallel_has_parallel_wave():
    """O plano ship-parallel deve ter uma wave com 3 reviews em paralelo."""
    path = TPL / "examples" / "ship-parallel.plan.yaml"
    proc = _run_cli(["compile-graph", str(path)], cwd=RUNNER_DIR)
    assert proc.returncode == 0

    data = json.loads(proc.stdout)
    waves = data["waves"]
    parallel_waves = data["parallel_waves"]

    # Ha exatamente 1 wave paralela
    assert sum(parallel_waves) == 1, f"Esperado 1 wave paralela, obtido {sum(parallel_waves)}"

    # Essa wave tem os 3 reviews
    idx = parallel_waves.index(True)
    wave = set(waves[idx])
    assert wave == {"code_review", "security_review", "test_review"}, (
        f"Wave paralela inesperada: {wave}"
    )


def test_approval_rounds_full_cycle_three_hitls(tmp_path):
    """approval-rounds tem 3 HITLs em cadeia. 3 resumes devem levar a done."""
    path = TPL / "approval-rounds.plan.yaml"
    out = tmp_path / "run"

    # 1. Run -> pause em hitl_r1
    proc = _run_cli(
        ["run", str(path), "--engine", "langgraph", "--mode", "stub", "--out", str(out)],
        cwd=RUNNER_DIR,
    )
    assert proc.returncode == 0, f"run falhou: {proc.stderr}"
    s = _load_status_safe(out)
    assert s.get("paused_at_step") == "hitl_r1"

    # 2. Resume 1 -> pause em hitl_r2
    proc = _run_cli(["resume", str(out), "--decision", "approve"], cwd=RUNNER_DIR)
    assert proc.returncode == 0, f"resume 1 falhou: {proc.stderr}"
    s = _load_status_safe(out)
    assert s.get("paused_at_step") == "hitl_r2"

    # 3. Resume 2 -> pause em hitl_final
    proc = _run_cli(["resume", str(out), "--decision", "approve"], cwd=RUNNER_DIR)
    assert proc.returncode == 0, f"resume 2 falhou: {proc.stderr}"
    s = _load_status_safe(out)
    assert s.get("paused_at_step") == "hitl_final"

    # 4. Resume 3 -> done
    proc = _run_cli(["resume", str(out), "--decision", "approve"], cwd=RUNNER_DIR)
    assert proc.returncode == 0, f"resume 3 falhou: {proc.stderr}"
    s = _load_status_safe(out)
    assert s.get("state") == "done"

    # 5. Todos os 7 steps concluidos
    completed = set(s.get("completed") or [])
    expected = {
        "review_r1", "hitl_r1", "revise_r2", "review_r2",
        "hitl_r2", "final_or_r3", "hitl_final",
    }
    assert completed == expected, (
        f"Steps em falta: {expected - completed} | "
        f"Steps a mais: {completed - expected}"
    )


def test_seo_article_demo_writes_artifacts(tmp_path):
    """seo-article-demo deve escrever os artefactos de cada step executado."""
    path = TPL / "examples" / "seo-article-demo.plan.yaml"
    out = tmp_path / "run"

    proc = _run_cli(
        ["run", str(path), "--engine", "langgraph", "--mode", "stub", "--out", str(out)],
        cwd=RUNNER_DIR,
    )
    assert proc.returncode == 0, f"run falhou: {proc.stderr}"

    status = _load_status_safe(out)
    completed = status.get("completed") or []

    # Para cada step completed que tem output_artifact, o ficheiro deve existir
    # Os steps antes do HITL sao: research, seo_brief, copy, critic
    artifacts = out / "artifacts"
    assert artifacts.exists(), f"Diretorio artifacts/ nao criado: {artifacts}"

    # Verificar pelo menos um artefacto esperado
    # (research escreve artifacts/01-research.md)
    expected_artifacts = [
        "01-research.md",
        "02-seo-brief.json",
        "03-copy.md",
        "04-critic.json",
    ]
    for name in expected_artifacts:
        f = artifacts / name
        assert f.exists(), f"Artefacto em falta: {f}"
        assert f.stat().st_size > 0, f"Artefacto vazio: {f}"

    # E os 4 steps executados antes do HITL
    assert set(completed) == {"research", "seo_brief", "copy", "critic"}, (
        f"Steps executados inesperados: {completed}"
    )
