"""OFFICE-A1: o mapa de lugares (config/office.yaml) e a projecção dos eventos reais.

O escritório não pode mentir:
- nenhum agente (dos 79 do runner e dos 21 só do MCP de produção) fica sem lugar, em dois
  lugares, ou aparece sem existir; os departamentos são do escritório, não do router;
- os agentes do MCP não emitem eventos: ficam "sem telemetria", nunca "à espera";
- cada passo de plano é atribuível a um agente pela `action:` do frontmatter;
- o estado vem só de eventos do runner (events.jsonl), com a ordem erro > precisa de ti >
  a trabalhar > a pensar > à espera, e um run real em stub acaba "precisa de ti" no gate.
"""

from __future__ import annotations

import copy
import json
import shutil
import uuid
from pathlib import Path

import pytest
import yaml

from plan_runner import office
from plan_runner.engine import run_plan

REPO_ROOT = Path(__file__).resolve().parents[2]
SEO_DEMO = REPO_ROOT / "docs/orchestration/marketing/templates/examples/seo-article-demo.plan.yaml"


@pytest.fixture
def run_dir():
    """O runner exige o --out dentro de pilots/; pilots/_pytest_*/ está no .gitignore."""
    d = REPO_ROOT / "pilots" / f"_pytest_office_{uuid.uuid4().hex[:8]}"
    try:
        yield d
    finally:
        shutil.rmtree(d, ignore_errors=True)


@pytest.fixture(autouse=True)
def _env(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "chave-de-teste")
    for var in ("SUPABASE_URL", "SUPABASE_SERVICE_ROLE_KEY", "AGENT_MODEL", "DATABASE_URL",
                "PLAN_RUNNER_CONTEXT", "MCP_API_KEY", "MCP_URL", "PLAN_RUNNER_TOOLS"):
        monkeypatch.delenv(var, raising=False)


def _with_office(monkeypatch, mutate) -> list[str]:
    data = copy.deepcopy(office.load_office(REPO_ROOT))
    mutate(data)
    monkeypatch.setattr(office, "load_office", lambda _root: data)
    return office.validate_office(REPO_ROOT)


def _dept(data: dict, did: str) -> dict:
    return next(d for d in data["departments"] if d["id"] == did)


def _evt(type_: str, run_id: str, at: str, **payload) -> dict:
    return {"type": type_, "run_id": run_id, "at": at, "payload": payload}


# --- mapa de lugares ---------------------------------------------------------------------------


def test_office_yaml_real_e_valido() -> None:
    assert office.validate_office(REPO_ROOT) == []


def _n(dept: dict) -> int:
    return sum(len(s["agents"]) for s in dept["seats"])


def _expected_total() -> int:
    runtime = {a for area in office.load_areas(REPO_ROOT) for a in area.get("agents") or []}
    mcp_only = [e for e in office.load_mcp_agents(REPO_ROOT) if e["runtime"] is None]
    return len(runtime) + len(mcp_only)


def test_todos_os_agentes_aparecem_nas_2_alas() -> None:
    data = office.load_office(REPO_ROOT)
    assert sum(_n(d) for d in data["departments"]) == _expected_total() >= 100
    negocios = [d for d in data["departments"] if d["wing"] == "negocios"]
    assert sum(_n(d) for d in negocios) == 19  # os agentes de cada negócio, só no MCP
    mk, com = _dept(data, "marketing"), _dept(data, "comercial")
    assert len(mk["seats"]) == 9 and mk["lead"] == "marketing.marketing"
    area_mk = next(a for a in office.load_areas(REPO_ROOT) if a["id"] == "marketing")
    assert _n(mk) + _n(com) == len(area_mk["agents"])  # a área marketing do router, em 2 departamentos


def test_agente_nos_2_sitios_entra_pelo_id_do_runner_e_so_uma_vez() -> None:
    mcp = {e["id"]: e["runtime"] for e in office.load_mcp_agents(REPO_ROOT)}
    assert len(mcp) == 34 and sum(r is None for r in mcp.values()) == 21
    placed = [a for d in office.load_office(REPO_ROOT)["departments"] for s in d["seats"] for a in s["agents"]]
    for mid, runtime in mcp.items():
        assert (f"mcp:{mid}" in placed) == (runtime is None), mid


@pytest.mark.parametrize("mutate, expected", [
    (lambda d: _dept(d, "trading")["seats"][0]["agents"].remove("trading.market_analysis"), "sem lugar"),
    (lambda d: _dept(d, "trading")["seats"][1]["agents"].append("trading.market_analysis"), "em dois lugares"),
    (lambda d: _dept(d, "trading")["seats"][0]["agents"].append("trading.agente_inventado"), "não existe"),
    (lambda d: _dept(d, "trading").update(lead="marketing.marketing"), "lead `marketing.marketing`"),
    (lambda d: _dept(d, "jogos")["seats"].append({"id": "jogos-x", "name": "X", "does": "y", "agents": []}), "lugar sem agentes"),
    (lambda d: _dept(d, "negocio-saude")["seats"][0]["agents"].remove("mcp:cardiologia"), "`mcp:cardiologia` sem lugar"),
    (lambda d: _dept(d, "software")["seats"][0]["agents"].append("mcp:revisor-codigo"), "não existe"),
    (lambda d: _dept(d, "trading").update(wing="ala-nova"), "`wing`"),
    (lambda d: d["departments"].append(dict(_dept(d, "jogos"))), "departamento `jogos` repetido"),
    (lambda d: _dept(d, "trading")["seats"][1].update(id="trading-mercado"), "repetido"),
    (lambda d: _dept(d, "trading")["seats"][0].update(does=" "), "`does` vazio"),
])
def test_validacao_apanha_o_que_faria_o_escritorio_mentir(monkeypatch, mutate, expected) -> None:
    errors = _with_office(monkeypatch, mutate)
    assert any(expected in e for e in errors), errors


def test_todos_os_passos_dos_planos_sao_atribuiveis_a_um_agente() -> None:
    actions, errors = office.action_index(REPO_ROOT)
    assert errors == []
    missing = []
    for plan in sorted((REPO_ROOT / "docs/orchestration").glob("**/*.plan.yaml")):
        for step in (yaml.safe_load(plan.read_text(encoding="utf-8")) or {}).get("steps") or []:
            action = step.get("action")
            if step.get("human_gate") or action in office.GATE_ACTIONS:
                continue
            if action not in actions:
                missing.append(f"{plan.relative_to(REPO_ROOT)}: {action}")
    assert missing == []


# --- projecção -----------------------------------------------------------------------------------


def _project(events: list[dict]) -> dict:
    actions, _ = office.action_index(REPO_ROOT)
    return office.project(events, office.load_office(REPO_ROOT), actions)


def _agent(snap: dict, aid: str) -> dict:
    for dept in snap["departments"]:
        for seat in dept["seats"]:
            for a in seat["agents"]:
                if a["id"] == aid:
                    return a
    raise KeyError(aid)


def _seat(snap: dict, sid: str) -> dict:
    return next(s for d in snap["departments"] for s in d["seats"] if s["id"] == sid)


def test_sem_eventos_runner_a_espera_mcp_sem_telemetria_e_vazios_sem_estado() -> None:
    snap = _project([])
    states = {d["id"]: d["state"] for d in snap["departments"]}
    assert states["jogos"] is None and states["documentacao"] is None
    assert states["marketing"] == "idle" and states["negocio-construcao"] == "untracked"
    assert states["financas"] == "idle"  # contabilidade (runner) à espera ganha a investimentos (MCP)
    assert _agent(snap, "mcp:viannalegal")["state"] == "untracked"
    assert snap["agent_count"] == _expected_total()


def test_snapshot_diz_que_o_agente_do_runner_tambem_esta_no_mcp() -> None:
    snap = office.snapshot(REPO_ROOT, [])
    assert _agent(snap, "marketing.marketing")["mcp"] == "marketing"
    assert _agent(snap, "marketing.research")["mcp"] is None


def test_cada_evento_da_o_seu_estado() -> None:
    run = "r1"
    started = [_evt("step_started", run, "2026-10-24T10:00:00", step_id="s1", action="research")]
    assert _agent(_project(started), "marketing.research")["state"] == "working"
    waiting = started + [_evt("step_waiting_external", run, "2026-10-24T10:00:01", step_id="s1")]
    assert _agent(_project(waiting), "marketing.research")["state"] == "thinking"
    failed = waiting + [_evt("step_failed", run, "2026-10-24T10:00:02", step_id="s1", detail="x")]
    assert _agent(_project(failed), "marketing.research")["state"] == "error"
    done = started + [_evt("step_finished", run, "2026-10-24T10:00:01", step_id="s1"),
                      _evt("plan_done", run, "2026-10-24T10:00:02", completed=["s1"])]
    assert _agent(_project(done), "marketing.research")["state"] == "idle"


def test_lugar_mostra_o_estado_mais_grave_dos_seus_agentes() -> None:
    events = [
        _evt("step_started", "r1", "2026-10-24T10:00:00", step_id="a", action="research"),
        _evt("step_started", "r2", "2026-10-24T10:00:01", step_id="b", action="trend_hunter"),
        _evt("step_failed", "r2", "2026-10-24T10:00:02", step_id="b", detail="x"),
    ]
    snap = _project(events)
    assert _seat(snap, "marketing-pesquisa")["state"] == "error"
    assert next(d for d in snap["departments"] if d["id"] == "marketing")["state"] == "error"


def test_gate_e_aborto_vao_para_o_ultimo_agente_activo_do_run() -> None:
    base = [_evt("step_started", "r1", "2026-10-24T10:00:00", step_id="c", action="critic_item13"),
            _evt("step_finished", "r1", "2026-10-24T10:00:01", step_id="c"),
            _evt("step_started", "r1", "2026-10-24T10:00:02", step_id="hitl", action="plan_approve")]
    gate = base + [_evt("human_gate_requested", "r1", "2026-10-24T10:00:03", step_id="hitl")]
    assert _agent(_project(gate), "marketing.critic_item13")["state"] == "needs"
    resolved = gate + [_evt("human_gate_resolved", "r1", "2026-10-24T10:00:04", step_id="hitl")]
    assert _agent(_project(resolved), "marketing.critic_item13")["state"] == "idle"
    aborted = base + [_evt("plan_aborted", "r1", "2026-10-24T10:00:03", reason="max_steps")]
    assert _agent(_project(aborted), "marketing.critic_item13")["state"] == "error"


def test_o_evento_mais_recente_ganha_entre_runs() -> None:
    events = [
        _evt("step_started", "velho", "2026-10-23T09:00:00", step_id="a", action="research"),
        _evt("step_failed", "velho", "2026-10-23T09:00:01", step_id="a", detail="x"),
        _evt("step_started", "novo", "2026-10-24T09:00:00", step_id="a", action="research"),
    ]
    agent = _agent(_project(events), "marketing.research")
    assert agent["state"] == "working" and agent["run_id"] == "novo"


def test_passo_sem_dono_fica_a_vista_em_unattributed() -> None:
    snap = _project([_evt("step_started", "r1", "2026-10-24T10:00:00", step_id="x", action="acao_que_nao_existe")])
    assert snap["unattributed"] == [{"run_id": "r1", "step_id": "x", "action": "acao_que_nao_existe"}]


def test_run_real_em_stub_acaba_precisa_de_ti_no_lugar_da_qualidade(run_dir) -> None:
    status = run_plan(SEO_DEMO, mode="stub", out_dir=run_dir)
    assert status["state"] == "paused_human_gate"
    snap = office.snapshot(REPO_ROOT, [run_dir])
    assert snap["unattributed"] == []
    assert _seat(snap, "marketing-qualidade")["state"] == "needs"
    assert next(d for d in snap["departments"] if d["id"] == "marketing")["state"] == "needs"
    for aid in ("marketing.research", "marketing.seo_brief", "marketing.copy_answer_first"):
        assert _agent(snap, aid)["state"] == "idle"
    assert next(d for d in snap["departments"] if d["id"] == "trading")["state"] == "idle"
    assert next(d for d in snap["departments"] if d["id"] == "negocio-viannalegal")["state"] == "untracked"


def test_cli_valida_e_projecta(run_dir, capsys) -> None:
    assert office.main([]) == 0
    assert "OK" in capsys.readouterr().out
    run_plan(SEO_DEMO, mode="stub", out_dir=run_dir)
    assert office.main(["--project", str(run_dir)]) == 0
    snap = json.loads(capsys.readouterr().out)
    assert snap["states"] == ["error", "needs", "working", "thinking", "idle", "untracked"]
