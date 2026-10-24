"""Escritório dos Agentes (config/office.yaml): validar o mapa de lugares e projectar eventos reais.

OFFICE-A1 (decisões do maestro 2026-10-24: opção A e D1 = A): o escritório é uma
PROJECÇÃO dos eventos que o runner já escreve (events.jsonl de cada run). Não guarda
estado próprio, não anima trabalho que não existe e não esconde nenhum agente. Os
departamentos são do escritório (ala das funções + ala dos negócios), não as áreas do
router. Contrato completo em docs/ops/OFFICE.md.

Regras de validação (cabeçalho de config/office.yaml):
  - cada agente do runner (areas[].agents[]) está em exactamente um lugar;
  - cada agente só do MCP (config/mcp-agents.yaml, runtime: null) está em exactamente um
    lugar como `mcp:<id>`; os que existem nos dois sítios entram pelo id do runner;
  - lead null ou agente do próprio departamento; ids únicos; wing funcoes|negocios;
  - cada `action:` de agents/**/*.agent.md pertence a um só agente (é por ela que um
    passo de plano é atribuído a um agente).

Projecção: estado por agente = o do evento mais recente que lhe é atribuído; lugar = o
mais grave dos seus agentes; departamento = o mais grave dos seus lugares. Os agentes do
MCP não emitem eventos: ficam `untracked` ("sem telemetria"), nunca `idle`.

CLI:  cd runner && python -m plan_runner.office                      (sai 1 e lista os erros)
      cd runner && python -m plan_runner.office --project RUN_DIR...  (snapshot JSON dos runs)
      cd runner && python -m plan_runner.office --html OUT.html [--label TEXTO] RUN_DIR...
                                                                       (escritório 2D, office_html.py)
"""
from __future__ import annotations

import json
import sys
from collections.abc import Iterable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml

from .areas import agent_ids, load_areas
from .skills import _frontmatter

OFFICE_FILE = Path("config") / "office.yaml"
MCP_FILE = Path("config") / "mcp-agents.yaml"
MCP_PREFIX = "mcp:"
WINGS = ("funcoes", "negocios")

# Do mais grave para o menos grave: é esta ordem que decide o estado de um lugar.
# `untracked` (sem telemetria) só ganha quando nenhum agente do lugar tem eventos possíveis.
STATES = ("error", "needs", "working", "thinking", "idle", "untracked")

# Eventos de um passo: atribuídos ao agente que corre esse passo.
STEP_EVENTS = {
    "step_started": "working",
    "tool_called": "working",
    "budget_resumed": "working",
    "step_waiting_external": "thinking",
    "step_finished": "idle",
    "step_failed": "error",
    "budget_exceeded": "needs",
    "tool_approval_requested": "needs",
    "human_gate_requested": "needs",
    "human_gate_resolved": "idle",
}
# Eventos do run sem passo de agente: vão para o último agente activo do run.
RUN_EVENTS = {
    "plan_aborted": "error",
    "done_when_failed": "error",
}
# Passos que são gates humanos, não trabalho de um agente.
GATE_ACTIONS = frozenset({"plan_approve"})


def _load_yaml(path: Path) -> dict:
    if not path.is_file():
        return {}
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def load_office(repo_root: Path) -> dict:
    return _load_yaml(repo_root / OFFICE_FILE)


def load_mcp_agents(repo_root: Path) -> list[dict]:
    return list(_load_yaml(repo_root / MCP_FILE).get("agents") or [])


def action_index(repo_root: Path) -> tuple[dict[str, str], list[str]]:
    """`action:` do frontmatter de cada agente -> id do agente (e os erros de actions repetidas)."""
    ids, _ = agent_ids(repo_root)
    index: dict[str, str] = {}
    errors: list[str] = []
    for aid, path in sorted(ids.items()):
        raw = _frontmatter(path).get("action")
        for action in raw if isinstance(raw, list) else [raw]:
            if not isinstance(action, str) or not action:
                continue
            if action in index:
                errors.append(f"action `{action}` em dois agentes ({index[action]}, {aid}): um passo não se atribui a ninguém")
            else:
                index[action] = aid
    return index, errors


def _validate_mcp(repo_root: Path, runtime_ids: set[str], errors: list[str]) -> tuple[set[str], dict[str, str]]:
    """Ids só do MCP e o mapa runtime -> id no MCP (para o snapshot dizer que o agente também está em produção)."""
    if not (repo_root / MCP_FILE).is_file():
        errors.append(f"{MCP_FILE} não existe")
        return set(), {}
    only: set[str] = set()
    also: dict[str, str] = {}
    seen: set[str] = set()
    for entry in load_mcp_agents(repo_root):
        mid = entry.get("id") if isinstance(entry, dict) else None
        if not isinstance(mid, str) or not mid:
            errors.append(f"{MCP_FILE}: entrada sem `id`: {entry!r}")
            continue
        if mid in seen:
            errors.append(f"{MCP_FILE}: `{mid}` repetido")
        seen.add(mid)
        runtime = entry.get("runtime")
        if runtime is None:
            only.add(mid)
        elif runtime not in runtime_ids:
            errors.append(f"{MCP_FILE}: `{mid}` aponta para o agente `{runtime}`, que não está em config/areas.yaml")
        elif runtime in also:
            errors.append(f"{MCP_FILE}: `{runtime}` é o runtime de dois agentes do MCP ({also[runtime]}, {mid})")
        else:
            also[runtime] = mid
    return only, also


def validate_office(repo_root: Path) -> list[str]:
    office = load_office(repo_root)
    if not office:
        return [f"{OFFICE_FILE} não existe ou está vazio"]
    errors: list[str] = []
    if office.get("version") != 1:
        errors.append("office.yaml: `version: 1` em falta")

    runtime_ids = {aid for a in load_areas(repo_root) for aid in (a.get("agents") or [])}
    mcp_only, _ = _validate_mcp(repo_root, runtime_ids, errors)
    expected = runtime_ids | {MCP_PREFIX + m for m in mcp_only}

    placed: dict[str, str] = {}
    dept_ids: set[str] = set()
    seat_ids: set[str] = set()
    for dept in office.get("departments") or []:
        if not isinstance(dept, dict) or not isinstance(dept.get("id"), str):
            errors.append(f"departamento inválido: {dept!r}")
            continue
        did = dept["id"]
        if did in dept_ids:
            errors.append(f"departamento `{did}` repetido")
        dept_ids.add(did)
        if dept.get("wing") not in WINGS:
            errors.append(f"{did}: `wing` tem de ser {' | '.join(WINGS)}")
        if not isinstance(dept.get("name"), str) or not dept["name"].strip():
            errors.append(f"{did}: `name` vazio")
        members: set[str] = set()
        for seat in dept.get("seats") or []:
            sid = seat.get("id") if isinstance(seat, dict) else None
            if not isinstance(sid, str) or not sid:
                errors.append(f"{did}: lugar sem `id`")
                continue
            if sid in seat_ids:
                errors.append(f"{did}: lugar `{sid}` repetido")
            seat_ids.add(sid)
            for key in ("name", "does"):
                if not isinstance(seat.get(key), str) or not seat[key].strip():
                    errors.append(f"{did}/{sid}: `{key}` vazio")
            agents = seat.get("agents")
            if not isinstance(agents, list) or not agents:
                errors.append(f"{did}/{sid}: lugar sem agentes (lugares vazios não se desenham)")
                continue
            for aid in agents:
                if aid not in expected:
                    errors.append(f"{did}/{sid}: `{aid}` não existe (nem em config/areas.yaml nem só no MCP em {MCP_FILE})")
                elif aid in placed:
                    errors.append(f"`{aid}` em dois lugares ({placed[aid]}, {sid})")
                else:
                    placed[aid] = sid
                    members.add(aid)
        lead = dept.get("lead")
        if lead is not None and lead not in members:
            errors.append(f"{did}: lead `{lead}` não é agente do departamento")

    for aid in sorted(expected - set(placed)):
        errors.append(f"`{aid}` sem lugar (o escritório não pode esconder um agente)")

    _, action_errors = action_index(repo_root)
    return errors + action_errors


def read_events(run_dirs: Iterable[Path]) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    for run_dir in run_dirs:
        path = Path(run_dir) / "events.jsonl"
        if not path.is_file():
            continue
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                events.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return events


def worst(states: Iterable[str]) -> str:
    present = set(states)
    return next((s for s in STATES if s in present), "idle")


def project(events: Iterable[dict[str, Any]], office: dict, actions: dict[str, str],
            mcp_also: dict[str, str] | None = None) -> dict[str, Any]:
    """Snapshot do escritório a partir dos eventos (função pura: mesmos eventos, mesmo snapshot)."""
    mcp_also = mcp_also or {}
    agents: dict[str, dict[str, Any]] = {}
    step_agent: dict[tuple[str, str], str] = {}
    last_agent: dict[str, str] = {}
    run_agents: dict[str, set[str]] = {}
    unattributed: list[dict[str, Any]] = []

    def mark(aid: str, state: str, evt: dict[str, Any], step_id: str | None) -> None:
        run_id = evt.get("run_id") or ""
        agents[aid] = {"state": state, "run_id": run_id, "step_id": step_id, "at": evt.get("at"), "event": evt.get("type")}
        last_agent[run_id] = aid
        run_agents.setdefault(run_id, set()).add(aid)

    for evt in sorted(events, key=lambda e: str(e.get("at") or "")):
        etype = evt.get("type")
        run_id = evt.get("run_id") or ""
        payload = evt.get("payload") or {}
        step_id = payload.get("step_id")
        if etype == "step_started":
            action = payload.get("action")
            if action in GATE_ACTIONS:
                continue
            aid = actions.get(action)
            if aid is None:
                unattributed.append({"run_id": run_id, "step_id": step_id, "action": action})
                continue
            step_agent[(run_id, step_id)] = aid
            mark(aid, "working", evt, step_id)
        elif etype in STEP_EVENTS:
            aid = step_agent.get((run_id, step_id)) or last_agent.get(run_id)
            if aid:
                mark(aid, STEP_EVENTS[etype], evt, step_id)
        elif etype in RUN_EVENTS:
            aid = last_agent.get(run_id)
            if aid:
                mark(aid, RUN_EVENTS[etype], evt, step_id)
        elif etype == "plan_done":
            for aid in run_agents.get(run_id, ()):
                if agents[aid]["run_id"] == run_id:
                    agents[aid] = {**agents[aid], "state": "idle", "at": evt.get("at"), "event": etype}

    def member(aid: str) -> dict[str, Any]:
        if aid.startswith(MCP_PREFIX):
            return {"id": aid, "source": "mcp", "mcp": aid[len(MCP_PREFIX):], "state": "untracked",
                    "run_id": None, "step_id": None, "at": None, "event": None}
        base = agents.get(aid, {"state": "idle", "run_id": None, "step_id": None, "at": None, "event": None})
        return {"id": aid, "source": "runtime", "mcp": mcp_also.get(aid), **base}

    departments = []
    for dept in office.get("departments") or []:
        seats = []
        for seat in dept.get("seats") or []:
            members = [member(aid) for aid in seat.get("agents") or []]
            seats.append({"id": seat["id"], "name": seat["name"], "does": seat["does"],
                          "state": worst(m["state"] for m in members), "agents": members})
        departments.append({
            "id": dept["id"], "wing": dept.get("wing"), "name": dept["name"], "lead": dept.get("lead"),
            "agent_count": sum(len(s["agents"]) for s in seats),
            "state": worst(s["state"] for s in seats) if seats else None,
            "seats": seats,
        })
    return {
        "version": 1,
        "generated_at": datetime.now(UTC).isoformat(),
        "states": list(STATES),
        "agent_count": sum(d["agent_count"] for d in departments),
        "departments": departments,
        "unattributed": unattributed,
    }


def snapshot(repo_root: Path, run_dirs: Iterable[Path]) -> dict[str, Any]:
    actions, _ = action_index(repo_root)
    runtime_ids = {aid for a in load_areas(repo_root) for aid in (a.get("agents") or [])}
    _, also = _validate_mcp(repo_root, runtime_ids, [])
    return project(read_events(run_dirs), load_office(repo_root), actions, also)


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    repo_root = Path(__file__).resolve().parents[2]
    errors = validate_office(repo_root)
    if errors:
        print(f"{OFFICE_FILE}: {len(errors)} erro(s)", file=sys.stderr)
        for e in errors:
            print(f"  - {e}", file=sys.stderr)
        return 1
    if args and args[0] == "--project":
        print(json.dumps(snapshot(repo_root, [Path(p) for p in args[1:]]), indent=2, ensure_ascii=False))
        return 0
    if args and args[0] == "--html":
        from .office_html import render

        if len(args) < 2:
            print("uso: --html OUT.html [--label TEXTO] RUN_DIR...", file=sys.stderr)
            return 2
        out, rest, label = Path(args[1]), args[2:], None
        if rest[:1] == ["--label"]:
            if len(rest) < 2:
                print("--label precisa de um texto", file=sys.stderr)
                return 2
            label, rest = rest[1], rest[2:]
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(render(snapshot(repo_root, [Path(p) for p in rest]), label=label), encoding="utf-8")
        print(f"escritório 2D: {out}")
        return 0
    office = load_office(repo_root)
    depts = office.get("departments") or []
    seats = sum(len(d.get("seats") or []) for d in depts)
    agents = sum(len(s.get("agents") or []) for d in depts for s in d.get("seats") or [])
    print(f"{OFFICE_FILE}: OK ({len(depts)} departamentos, {seats} lugares, {agents} agentes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
