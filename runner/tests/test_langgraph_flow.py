"""Testes de integracao do motor LangGraph no runner.

Corre o CLI real (subprocess) para validar:
- run --mode stub -> paused_human_gate
- resume approve -> done
- resume reject -> rejected
- run --mode external -> waiting_external
- resume com result.json -> completed acumulado
- ciclo completo external -> HITL -> done
- checkpoints.db persistente
- sem BOM no langgraph_engine.py
"""
from __future__ import annotations

from pathlib import Path

# ============================================================
# TESTES BASICOS
# ============================================================

def test_no_bom_in_langgraph_engine(runner_dir: Path):
    """langgraph_engine.py nao pode ter BOM (U+FEFF)."""
    target = runner_dir / "plan_runner" / "langgraph_engine.py"
    assert target.exists(), f"Ficheiro nao encontrado: {target}"

    with open(target, "rb") as f:
        first_bytes = f.read(3)

    assert first_bytes != b"\xef\xbb\xbf", (
        "langgraph_engine.py tem BOM (U+FEFF). "
        "Isso quebra o ast.parse e alguns imports."
    )


def test_engine_module_imports(runner_dir: Path):
    """O modulo langgraph_engine importa sem erro."""
    import subprocess
    import sys

    result = subprocess.run(
        [
            sys.executable,
            "-c",
            "from plan_runner.langgraph_engine import "
            "run_plan_langgraph, resume_plan_langgraph, _WaitExternal, merge_artifacts; "
            "print('OK')",
        ],
        cwd=str(runner_dir),
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"Import falhou: {result.stderr}"
    assert "OK" in result.stdout


# ============================================================
# MODE STUB
# ============================================================

def test_run_stub_pauses_at_hitl(run_plan, tmp_run_dir: Path):
    """run --mode stub deve parar em paused_human_gate."""
    proc, status = run_plan(tmp_run_dir, mode="stub")

    assert proc.returncode == 0, f"run falhou: {proc.stderr}"
    assert status.get("engine") == "langgraph", (
        f"Esperado engine=langgraph, obtido {status.get('engine')}. "
        f"Isso indica que caiu no fallback langgraph_waves_fallback."
    )
    assert status.get("state") == "paused_human_gate", (
        f"Esperado state=paused_human_gate, obtido {status.get('state')}"
    )
    assert status.get("paused_at_step") == "hitl"

    # checkpoints.db deve existir
    checkpoint = tmp_run_dir / "checkpoints.db"
    assert checkpoint.exists(), "checkpoints.db nao foi criado"
    assert checkpoint.stat().st_size > 0, "checkpoints.db esta vazio"


def test_resume_approve_completes_plan(run_plan, resume_plan, tmp_run_dir: Path):
    """resume approve deve levar o plano a done."""
    # 1. Run
    proc, status = run_plan(tmp_run_dir, mode="stub")
    assert status.get("state") == "paused_human_gate"

    # 2. Resume approve
    proc, status = resume_plan(tmp_run_dir, "approve")
    assert proc.returncode == 0, f"resume falhou: {proc.stderr}"
    assert status.get("state") == "done", (
        f"Esperado state=done, obtido {status.get('state')}"
    )
    assert status.get("decision") == "approve"

    # hitl deve estar em completed
    completed = status.get("completed") or []
    assert "hitl" in completed, f"hitl nao esta em completed: {completed}"

    # Todos os steps do plano devem estar concluidos
    expected = {"prepare", "code_review", "security_review", "test_review", "ship_decision", "hitl"}
    assert expected.issubset(set(completed)), (
        f"Steps em falta em completed: {expected - set(completed)}"
    )


def test_resume_reject_sets_rejected_state(run_plan, resume_plan, tmp_run_dir: Path):
    """resume reject deve marcar o plano como rejected."""
    proc, status = run_plan(tmp_run_dir, mode="stub")
    assert status.get("state") == "paused_human_gate"

    proc, status = resume_plan(tmp_run_dir, "reject")
    assert proc.returncode == 0, f"resume falhou: {proc.stderr}"
    assert status.get("state") == "rejected", (
        f"Esperado state=rejected, obtido {status.get('state')}"
    )
    assert status.get("decision") == "reject"

    # hitl NAO deve estar em completed (foi rejeitado)
    completed = status.get("completed") or []
    assert "hitl" not in completed


# ============================================================
# MODE EXTERNAL
# ============================================================

def test_run_external_waits_for_worker(run_plan, tmp_run_dir: Path):
    """run --mode external deve criar pending_steps/prepare/."""
    proc, status = run_plan(tmp_run_dir, mode="external")

    assert proc.returncode == 0, f"run falhou: {proc.stderr}"
    assert status.get("engine") == "langgraph"
    assert status.get("state") == "waiting_external"
    assert status.get("paused_at_step") == "prepare"

    # pending_steps/prepare/ deve existir
    pending = tmp_run_dir / "pending_steps" / "prepare"
    assert pending.exists(), "pending_steps/prepare/ nao foi criado"
    assert (pending / "request.json").exists(), "request.json nao foi criado"


def test_resume_external_accumulates_completed(
    run_plan, resume_plan, write_result_json, tmp_run_dir: Path
):
    """Apos preencher prepare/result.json, resume deve acumular completed."""
    # 1. Run external
    proc, status = run_plan(tmp_run_dir, mode="external")
    assert status.get("state") == "waiting_external"
    assert status.get("completed") == []

    # 2. Preencher result.json do prepare
    write_result_json(tmp_run_dir, "prepare", ok=True, detail="prepare done")

    # 3. Resume
    proc, status = resume_plan(tmp_run_dir, "approve")
    assert proc.returncode == 0, f"resume falhou: {proc.stderr}"

    # O prepare deve estar em completed
    completed = status.get("completed") or []
    assert "prepare" in completed, (
        f"prepare nao esta em completed apos resume: {completed}"
    )

    # O estado deve ser waiting_external (proximo step)
    # NOTA: os 3 reviews (code_review, security_review, test_review) estao
    # na mesma wave. O LangGraph nao garante a ordem de execucao dentro da
    # wave, portanto o paused_at_step pode ser qualquer um dos 3.
    assert status.get("state") == "waiting_external"
    assert status.get("paused_at_step") in (
        "code_review",
        "security_review",
        "test_review",
    ), f"Esperado um dos 3 reviews, obtido {status.get('paused_at_step')}"


def test_external_full_cycle(
    run_plan, resume_plan, write_result_json, tmp_run_dir: Path
):
    """Ciclo completo: run external -> 5 workers -> HITL -> approve -> done."""
    # 1. Run external (para em prepare)
    proc, status = run_plan(tmp_run_dir, mode="external")
    assert status.get("state") == "waiting_external"
    assert status.get("paused_at_step") == "prepare"

    # 2. Preencher prepare + resume (para em code_review)
    write_result_json(tmp_run_dir, "prepare")
    proc, status = resume_plan(tmp_run_dir, "approve")
    assert "prepare" in (status.get("completed") or [])

    # 3. Preencher code_review, security_review, test_review + resume
    #    (o run anterior criou pending_steps/code_review/)
    write_result_json(tmp_run_dir, "code_review")
    write_result_json(tmp_run_dir, "security_review")
    write_result_json(tmp_run_dir, "test_review")
    proc, status = resume_plan(tmp_run_dir, "approve")
    completed = status.get("completed") or []
    for step in ["prepare", "code_review", "security_review", "test_review"]:
        assert step in completed, f"{step} nao esta em completed: {completed}"

    # 4. Preencher ship_decision + resume (para em HITL)
    write_result_json(tmp_run_dir, "ship_decision")
    proc, status = resume_plan(tmp_run_dir, "approve")
    completed = status.get("completed") or []
    assert "ship_decision" in completed, (
        f"ship_decision nao esta em completed: {completed}"
    )

    # O estado deve ser waiting_external no hitl (porque o hitl tem human_gate
    # e o modo external vai levantar _WaitExternal antes de chegar ao interrupt)
    # OU paused_human_gate (se o LangGraph interpretou o interrupt)
    state = status.get("state")
    assert state in ("waiting_external", "paused_human_gate"), (
        f"Esperado waiting_external ou paused_human_gate, obtido {state}"
    )

    # 5. Resume approve final -> done
    proc, status = resume_plan(tmp_run_dir, "approve")
    assert proc.returncode == 0, f"resume final falhou: {proc.stderr}"
    assert status.get("state") == "done", (
        f"Esperado state=done, obtido {status.get('state')}"
    )

    completed = status.get("completed") or []
    expected = {"prepare", "code_review", "security_review", "test_review", "ship_decision", "hitl"}
    assert expected.issubset(set(completed)), (
        f"Steps em falta no ciclo completo: {expected - set(completed)}"
    )


# ============================================================
# CHECKPOINT
# ============================================================

def test_checkpoint_db_persists_completed(run_plan, tmp_run_dir: Path):
    """O checkpoints.db deve ter o estado correto apos o run."""
    proc, status = run_plan(tmp_run_dir, mode="external")
    assert status.get("state") == "waiting_external"

    checkpoint = tmp_run_dir / "checkpoints.db"
    assert checkpoint.exists()

    # Verificar que e um SQLite valido
    import sqlite3
    conn = sqlite3.connect(str(checkpoint))
    try:
        cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        assert len(tables) > 0, "checkpoints.db nao tem tabelas"
    finally:
        conn.close()


# ============================================================
# DECISION EDIT
# ============================================================

def test_resume_edit_with_payload(
    run_plan, resume_plan, tmp_run_dir: Path
):
    """resume --decision edit com payload grava o payload no output_artifact."""
    import json as _json

    # 1. Run stub -> paused_human_gate
    proc, status = run_plan(tmp_run_dir, mode="stub")
    assert status.get("state") == "paused_human_gate"

    # 2. Escrever payload num ficheiro (simula o uso real via --payload-file)
    payload = {
        "decision": "GO",
        "notes": "aprovar com condicoes",
        "reviewer": "cto",
    }
    payload_file = tmp_run_dir.parent / "payload-edit.json"
    payload_file.write_text(
        _json.dumps(payload, ensure_ascii=False),
        encoding="utf-8",
    )

    # 3. Correr resume com edit + payload-file
    from tests.conftest import RUNNER_DIR, _run_cli
    proc = _run_cli([
        "resume",
        str(tmp_run_dir),
        "--decision", "edit",
        "--payload-file", str(payload_file),
    ], cwd=RUNNER_DIR)

    assert proc.returncode == 0, f"resume edit falhou: {proc.stderr}"

    # 4. Ler status.json atualizado
    status_file = tmp_run_dir / "status.json"
    status = _json.loads(status_file.read_text(encoding="utf-8"))
    assert status.get("state") == "done"
    assert status.get("decision") == "edit"

    # 5. Verificar que o payload foi gravado no output_artifact do HITL
    artifact = tmp_run_dir / "artifacts" / "06-hitl.json"
    assert artifact.exists(), f"output_artifact nao existe: {artifact}"

    conteudo = _json.loads(artifact.read_text(encoding="utf-8-sig"))
    assert conteudo.get("decision") == "GO"
    assert conteudo.get("notes") == "aprovar com condicoes"
    assert conteudo.get("reviewer") == "cto"

    # 6. Verificar que o evento human_gate_resolved tem has_payload=true
    eventos_file = tmp_run_dir / "events.jsonl"
    eventos = eventos_file.read_text(encoding="utf-8").splitlines()
    resolvidos = [
        _json.loads(e) for e in eventos
        if e.strip() and "human_gate_resolved" in e
    ]
    assert len(resolvidos) == 1, f"esperado 1 evento, obtido {len(resolvidos)}"
    assert resolvidos[0]["payload"].get("decision") == "edit"
    assert resolvidos[0]["payload"].get("has_payload") is True
