"""F5: scripts/f5_evidence.py — resumo de evidência de um run, sem segredos nem conteúdo."""

from __future__ import annotations

import importlib.util
import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SEGREDO = "sk-NAO-PODE-APARECER-0123456789"


def _load():
    spec = importlib.util.spec_from_file_location(
        "f5_evidence", REPO_ROOT / "scripts/f5_evidence.py"
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


ev = _load()


def _run(tmp_path: Path, *, state="paused_human_gate", hits=3, ledger=True, errors=()) -> Path:
    run = tmp_path / "run"
    (run / "artifacts").mkdir(parents=True)
    (run / "pending_steps" / "audit").mkdir(parents=True)
    (run / "status.json").write_text(
        json.dumps(
            {
                "run_id": "run_x",
                "plan_id": "example-security-audit-demo",
                "mode": "external",
                "state": state,
                "completed": ["triage", "audit", "report"],
            }
        ),
        encoding="utf-8",
    )
    events = [{"type": "plan_created", "run_id": "run_x", "payload": {}}]
    if hits is not None:
        events.append(
            {
                "type": "knowledge_context_injected",
                "run_id": "run_x",
                "payload": {"step_id": "audit", "kb": "security", "hit_count": hits},
            }
        )
    events += [{"type": e, "run_id": "run_x", "payload": {"error": SEGREDO}} for e in errors]
    (run / "events.jsonl").write_text("\n".join(json.dumps(e) for e in events), encoding="utf-8")
    if ledger:
        rows = [
            {
                "model_version": "gemini-flash-lite",
                "tokens_in": 800,
                "tokens_out": 150,
                "tokens_total": 950,
            },
            {
                "model_version": "gemini-flash-lite",
                "tokens_in": 1200,
                "tokens_out": 300,
                "tokens_total": 1500,
            },
        ]
        (run / "token_usage.jsonl").write_text(
            "\n".join(json.dumps(r) for r in rows), encoding="utf-8"
        )
    # conteúdo que NUNCA pode sair no resumo
    (run / "artifacts" / "03-security-report.md").write_text(
        f"# Relatório\n{SEGREDO}\n", encoding="utf-8"
    )
    (run / "pending_steps" / "audit" / "knowledge_context.md").write_text(
        f"[Fonte: docs/knowledge/security-agents-stack.md @ l.1-9]\nNunca ataque activo. {SEGREDO}\n",
        encoding="utf-8",
    )
    return run


def test_run_completo_passou(tmp_path: Path) -> None:
    out = ev.collect(_run(tmp_path))
    assert out["verdict"] == "PASSOU"
    assert out["tokens"] == {"calls": 2, "tokens_in": 2000, "tokens_out": 450, "tokens_total": 2450}
    assert out["models"] == {"gemini-flash-lite": 2}
    assert out["sources_cited"] == ["docs/knowledge/security-agents-stack.md"]
    assert out["knowledge"] == [{"step_id": "audit", "kb": "security", "hit_count": 3}]
    assert out["artifacts"][0]["path"] == "artifacts/03-security-report.md"


@pytest.mark.parametrize(
    ("kw", "falha"),
    [
        ({"state": "running"}, "estado_final"),
        ({"hits": 0}, "l5_injectado"),
        ({"hits": None}, "l5_injectado"),
        ({"ledger": False}, "modelo_correu"),
        ({"errors": ("worker_error",)}, "sem_erros"),
        ({"errors": ("knowledge_context_failed",)}, "sem_erros"),
    ],
)
def test_cada_criterio_em_falta_da_incompleto(tmp_path: Path, kw: dict, falha: str) -> None:
    out = ev.collect(_run(tmp_path, **kw))
    assert out["verdict"] == "INCOMPLETO"
    assert out["checks"][falha] is False


def test_resumo_nunca_mostra_conteudo_nem_segredos(tmp_path: Path, capsys) -> None:
    run = _run(tmp_path, errors=("worker_error",))
    for args in ([str(run)], [str(run), "--json"]):
        ev.main(args)
        printed = capsys.readouterr().out
        assert SEGREDO not in printed
        assert "Nunca ataque activo" not in printed  # nem o texto dos excertos


def test_markdown_tem_veredicto_e_criterios(tmp_path: Path) -> None:
    md = ev.to_markdown(ev.collect(_run(tmp_path)))
    assert md.startswith("**Veredicto: PASSOU**")
    assert "| l5_injectado | sim |" in md
    assert "`docs/knowledge/security-agents-stack.md`" in md


def test_directorio_que_nao_e_run(tmp_path: Path, capsys) -> None:
    assert ev.main([str(tmp_path)]) == 2


def test_run_stub_real_e_incompleto_sem_l5_nem_modelo() -> None:
    """Um run stub verdadeiro (sem MCP nem Gemini) nunca pode passar como F5."""
    out_dir = REPO_ROOT / "pilots" / "test-f5-evidence-stub"
    shutil.rmtree(out_dir, ignore_errors=True)
    try:
        subprocess.run(
            [
                sys.executable,
                "-m",
                "plan_runner",
                "run",
                str(
                    REPO_ROOT
                    / "docs/orchestration/security/templates/examples/security-audit-demo.plan.yaml"
                ),
                "--mode",
                "stub",
                "--out",
                str(out_dir),
            ],
            cwd=REPO_ROOT / "runner",
            check=True,
            capture_output=True,
            timeout=120,
            env={**__import__("os").environ, "MCP_URL": "", "MCP_API_KEY": ""},
        )
        out = ev.collect(out_dir)
        assert out["state"] == "paused_human_gate"
        assert out["verdict"] == "INCOMPLETO"
        assert out["checks"]["l5_injectado"] is False
        assert out["checks"]["modelo_correu"] is False
    finally:
        shutil.rmtree(out_dir, ignore_errors=True)
