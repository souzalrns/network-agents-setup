"""Worker do modo `external` (AU-23, PLANO-DE-ACAO #6): executa um passo com o Gemini.

Fecha o buraco que deixava o runner parado em `waiting_external`. Para cada
passo pendente:

1. le `pending_steps/<id>/request.json` (escrito por executor.py);
2. le `AGENT.md` e `SKILL.md` (copiados para o mesmo directorio pelo executor),
   a directiva de grounding (agents/_shared) e o contexto opcional
   (`knowledge_context.md`, `CLIENT_MEMORY.md`, artefactos de input);
3. chama o Gemini (`generateContent`, gemini-flash-lite-latest por omissao);
4. escreve `result.json` no formato que executor.py ja le
   (`{ok, detail, artifact_content}`);
5. regista os tokens no ledger J6 (`token_usage`): sempre em
   `<run>/token_usage.jsonl`; no Supabase so se SUPABASE_URL e
   SUPABASE_SERVICE_ROLE_KEY estiverem definidas (mesmo contrato e mesma
   regra do servidor MCP: gravar nunca faz falhar o passo);
6. respeita o HITL: nunca executa um passo com `human_gate` nem avanca um
   run em `paused_human_gate` -- a decisao e humana (hitl-*.jsonl, resume);
7. respeita o orcamento (PLANO item 4, docs/ops/BUDGET.md): antes de cada
   chamada soma o `tokens_total` do ledger do run; se ja chegou ao tecto
   (`--max-tokens` do run, ou `budget.max_tokens` do plano), nao chama o
   Gemini e lanca BudgetExceeded -- o motor pausa o run em `paused_budget`.

Falha do Gemini (rede, HTTP, resposta vazia, JSON invalido) NAO escreve
`result.json`: deixa `worker_error.json` com o motivo e o passo continua em
`waiting_external`, por isso basta `resume` para tentar outra vez.

Sem dependencias novas: httpx (ja usado por embedder.py), PyYAML.

CLI (para runs ja parados em waiting_external, de qualquer engine):
    python -m plan_runner.external_worker <run_dir> [--resume]
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import uuid
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import httpx
import yaml

from . import context_policy as cp
from . import cost
from . import memory_wiring as mw
from . import model_tiers as mt
from . import repo_files as rf
from .skills import _frontmatter, repo_root_from_out

DEFAULT_MODEL = "gemini-flash-lite-latest"
GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
DEFAULT_MAX_OUTPUT_TOKENS = 4096
INPUT_MAX_CHARS = 20000  # por ficheiro de input/contexto
LEDGER_FILE = "token_usage.jsonl"
ERROR_FILE = "worker_error.json"
TOKEN_TABLE = "token_usage"

# run_id do runner ("run_ab12cd34ef") -> uuid estavel para a coluna uuid do
# token_usage. Mesmo run => mesmo uuid, por isso os passos agrupam por run.
_RUN_NAMESPACE = uuid.uuid5(uuid.NAMESPACE_URL, "network-agents-setup/plan_runner")

# Gemini: (url, headers, body, timeout) -> (status_code, json). Injectavel nos testes.
Transport = Callable[[str, dict[str, str], dict[str, Any], float], tuple[int, dict[str, Any]]]
# Ledger remoto: (row) -> None. Injectavel nos testes; None = desligado.
RemoteSink = Callable[[dict[str, Any]], None]


class WorkerError(RuntimeError):
    """O passo nao foi executado (Gemini falhou ou a resposta nao serve)."""


class HumanGateBlocked(WorkerError):
    """O passo ou o run esperam uma decisao humana; o worker nao avanca."""


class BudgetExceeded(WorkerError):
    """O run ja gastou o tecto de tokens; o passo nao chega a chamar o Gemini."""

    unit = "tokens"

    def __init__(self, spent: int, cap: int):
        super().__init__(f"orcamento de tokens atingido: {spent} gastos >= tecto {cap}")
        self.spent = spent
        self.cap = cap


class CostBudgetExceeded(BudgetExceeded):
    """D6: o run ja gastou o tecto de custo (budget.max_cost_usd / --max-cost-usd)."""

    unit = "usd"

    def __init__(self, spent: float, cap: float):
        WorkerError.__init__(self, f"orcamento de custo atingido: US$ {spent:.6f} gastos >= tecto US$ {cap}")
        self.spent = spent
        self.cap = cap


def _now() -> str:
    return datetime.now(UTC).isoformat()


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def _clip(text: str, limit: int = INPUT_MAX_CHARS) -> str:
    return text if len(text) <= limit else text[:limit] + f"\n\n[... cortado: {len(text) - limit} caracteres]"


def ledger_run_uuid(run_id: str | None) -> str | None:
    return str(uuid.uuid5(_RUN_NAMESPACE, run_id)) if run_id else None


def build_usage_row(
    *, run_id: str | None, agent_id: str | None, model: str, response: dict | None, call_kind: str = "agent"
) -> dict[str, Any]:
    """Linha de token_usage -- espelho de buildUsageRow (agent-network-mcp lib/tokenLedger.js).

    So colunas da tabela (memory/token_usage.sql no agent-network-mcp); o
    PostgREST recusa colunas desconhecidas.
    """
    usage = (response or {}).get("usageMetadata")
    has_usage = isinstance(usage, dict)

    def _int(key: str) -> int | None:
        v = usage.get(key) if has_usage else None
        return v if isinstance(v, int) and not isinstance(v, bool) else None

    return {
        "run_id": ledger_run_uuid(run_id),
        "agent_id": agent_id,
        "call_kind": call_kind,  # agent | router | embed_query (check da tabela)
        "model": model,
        "model_version": (response or {}).get("modelVersion"),
        "tokens_in": _int("promptTokenCount"),
        "tokens_out": _int("candidatesTokenCount"),
        "tokens_total": _int("totalTokenCount"),
        "status": "ok" if has_usage else "missing_usage",
        "raw_usage": usage if has_usage else None,
        "service_tier": usage.get("serviceTier") if has_usage else None,
        "response_id": (response or {}).get("responseId"),
    }


def supabase_sink_from_env(timeout: float = 10.0) -> RemoteSink | None:
    """POST no PostgREST com o service_role, como o MCP. None se faltar config."""
    url = os.environ.get("SUPABASE_URL", "").strip().rstrip("/")
    key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "").strip()
    if not url or not key:
        return None

    def sink(row: dict[str, Any]) -> None:
        r = httpx.post(
            f"{url}/rest/v1/{TOKEN_TABLE}",
            headers={
                "apikey": key,
                "Authorization": f"Bearer {key}",
                "Content-Type": "application/json",
                "Prefer": "return=minimal",
            },
            json=row,
            timeout=timeout,
        )
        if r.status_code >= 300:
            raise RuntimeError(f"HTTP {r.status_code}: {r.text[:200]}")

    return sink


def record_token_usage(
    out_root: Path,
    row: dict[str, Any],
    *,
    step_id: str,
    run_id: str | None,
    remote: RemoteSink | None,
) -> dict[str, Any]:
    """Grava a linha no jsonl local e (se houver) no Supabase. Nunca lanca.

    O jsonl leva tambem o run_id original do runner e o step_id, que a tabela
    nao tem; o `remote` diz o que aconteceu do lado do Supabase.
    """
    entry = {**row, "recorded_at": _now(), "runner_run_id": run_id, "step_id": step_id}
    if remote is None:
        entry["remote"] = "skipped"
    else:
        try:
            remote(row)
            entry["remote"] = "ok"
        except Exception as e:  # noqa: BLE001 -- o ledger nunca parte o passo
            entry["remote"] = f"error: {str(e)[:200]}"
            print(f"[token_usage] falha ao gravar: {str(e)[:200]}", file=sys.stderr)
    try:
        with (out_root / LEDGER_FILE).open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except OSError as e:
        print(f"[token_usage] falha no jsonl local: {e}", file=sys.stderr)
    return entry


def gemini_api_key(explicit: str | None = None) -> str:
    key = (explicit or os.environ.get("GEMINI_API_KEY", "")).strip()
    if not key:
        raise WorkerError("GEMINI_API_KEY em falta no ambiente (chave gratuita: aistudio.google.com/apikey)")
    return key


def gemini_generate(
    system: str,
    user: str,
    *,
    model: str,
    api_key: str | None = None,
    wants_json: bool = False,
    max_output_tokens: int = DEFAULT_MAX_OUTPUT_TOKENS,
    timeout: float = 60.0,
    transport: Transport | None = None,
) -> dict[str, Any]:
    """Uma chamada generateContent. Devolve o JSON da resposta; lanca WorkerError.

    Partilhada pelo worker e pelo router (plan_runner/router.py).
    """
    generation: dict[str, Any] = {"maxOutputTokens": max_output_tokens}
    if wants_json:
        generation["responseMimeType"] = "application/json"
    body = {
        "systemInstruction": {"parts": [{"text": system}]},
        "contents": [{"role": "user", "parts": [{"text": user}]}],
        "generationConfig": generation,
    }
    send = transport or httpx_transport
    try:
        # Chave no header (nao na query): nunca aparece em URLs de erro nem em logs.
        code, response = send(GEMINI_URL.format(model=model), {"x-goog-api-key": gemini_api_key(api_key)}, body, timeout)
    except httpx.HTTPError as e:
        raise WorkerError(f"gemini: erro de rede: {type(e).__name__}") from e
    if code != 200:
        msg = ((response.get("error") or {}).get("message") or "")[:300]
        raise WorkerError(f"gemini HTTP {code}: {msg}")
    return response


def httpx_transport(url: str, headers: dict[str, str], body: dict[str, Any], timeout: float) -> tuple[int, dict[str, Any]]:
    r = httpx.post(url, headers=headers, json=body, timeout=timeout)
    try:
        data = r.json()
    except ValueError:
        data = {"error": {"message": r.text[:300]}}
    return r.status_code, data if isinstance(data, dict) else {"data": data}


def _load_plan_raw(out_root: Path) -> dict[str, Any]:
    p = out_root / "plan.yaml"
    if not p.is_file():
        return {}
    data = yaml.safe_load(p.read_text(encoding="utf-8-sig"))
    return data if isinstance(data, dict) else {}


def _plan_step(plan_raw: dict[str, Any], step_id: str) -> dict[str, Any] | None:
    for s in plan_raw.get("steps") or []:
        if isinstance(s, dict) and str(s.get("id")) == step_id:
            return s
    return None


def ledger_spent(out_root: Path) -> int:
    """Tokens ja gastos pelo run: soma do tokens_total do ledger local (linhas sem tokens contam 0)."""
    path = out_root / LEDGER_FILE
    if not path.is_file():
        return 0
    total = 0
    for line in path.read_text(encoding="utf-8").splitlines():
        try:
            v = json.loads(line).get("tokens_total")
        except (json.JSONDecodeError, AttributeError):
            continue
        if isinstance(v, int) and not isinstance(v, bool):
            total += v
    return total


def token_cap(out_root: Path) -> int | None:
    """Tecto do run: `max_tokens` do status.json (--max-tokens) > `budget.max_tokens` do plano. None = sem tecto."""
    status_path = out_root / "status.json"
    if status_path.is_file():
        try:
            v = _read_json(status_path).get("max_tokens")
        except (json.JSONDecodeError, UnicodeDecodeError):
            v = None
        if isinstance(v, int) and not isinstance(v, bool):
            return v
    v = (_load_plan_raw(out_root).get("budget") or {}).get("max_tokens")
    return v if isinstance(v, int) and not isinstance(v, bool) else None


def cost_cap(out_root: Path) -> float | None:
    """D6: tecto de custo em USD. `max_cost_usd` do status.json (--max-cost-usd) > `budget.max_cost_usd` do plano."""
    status_path = out_root / "status.json"
    if status_path.is_file():
        try:
            v = _read_json(status_path).get("max_cost_usd")
        except (json.JSONDecodeError, UnicodeDecodeError):
            v = None
        if isinstance(v, (int, float)) and not isinstance(v, bool):
            return float(v)
    v = (_load_plan_raw(out_root).get("budget") or {}).get("max_cost_usd")
    return float(v) if isinstance(v, (int, float)) and not isinstance(v, bool) else None


def check_budget(out_root: Path, model: str | None = None) -> None:
    """Lanca BudgetExceeded se o ledger do run ja chegou a um tecto (tokens ou custo).

    D6: com tecto de custo, falha fechada (WorkerError) se o modelo a usar, ou um
    ja usado no run, nao tem preco confirmado em config/model-prices.yaml.
    """
    cap = token_cap(out_root)
    if cap is not None:
        spent = ledger_spent(out_root)
        if spent >= cap:
            raise BudgetExceeded(spent, cap)
    usd_cap = cost_cap(out_root)
    if usd_cap is None:
        return
    prices = cost.load_prices()
    missing = model if model is not None and model not in prices else None
    try:
        spent_usd = cost.ledger_cost_usd(out_root / LEDGER_FILE, prices)
    except cost.CostUnknown as e:
        missing = str(e)
    if missing is not None:
        raise WorkerError(
            f"budget.max_cost_usd definido, mas o modelo {missing!r} nao tem preco confirmado "
            "em config/model-prices.yaml (docs/ops/BUDGET.md, D6)"
        )
    if spent_usd >= usd_cap:
        raise CostBudgetExceeded(spent_usd, usd_cap)


def check_hitl(out_root: Path, step_id: str) -> None:
    """Lanca HumanGateBlocked se o passo tem gate ou o run espera decisao humana."""
    status_path = out_root / "status.json"
    if status_path.is_file():
        try:
            status = _read_json(status_path)
        except (json.JSONDecodeError, UnicodeDecodeError):
            status = {}
        if status.get("state") == "paused_human_gate":
            raise HumanGateBlocked(
                f"run em paused_human_gate no passo {status.get('paused_at_step')!r}: "
                "decide primeiro (hitl-decisions.jsonl ou `plan_runner resume --decision ...`)"
            )
    step = _plan_step(_load_plan_raw(out_root), step_id)
    if step is not None and step.get("human_gate"):
        raise HumanGateBlocked(f"passo {step_id!r} tem human_gate: a decisao e humana, o worker nao o executa")


def _section(title: str, body: str) -> str:
    return f"## {title}\n\n{body.strip()}\n"


def build_prompt(
    out_root: Path, pending: Path, request: dict[str, Any], *, context: str | None = None
) -> tuple[str, str, bool]:
    """(system, user, quer_json). Tudo o que o modelo ve vem de ficheiros do run/repo."""
    built = build_prompt_ctx(out_root, pending, request, context=context)
    return built["system"], built["user"], built["wants_json"]


def build_prompt_ctx(
    out_root: Path, pending: Path, request: dict[str, Any], *, context: str | None = None
) -> dict[str, Any]:
    """Prompt + o que entrou nele. `context`: opt (omissao, B1-bis) | legacy (prompt anterior).

    SEC-1: se o passo declarar `repo_files`, os ficheiros (so leitura, com
    exclusoes e limite: plan_runner/repo_files.py) entram no fim do prompt do
    utilizador, nos dois modos. Sem `repo_files`, nada muda. O mesmo para
    `SKILL_ACTIVATION.md` (SEC-1.3, plan_runner/skill_activation.py).
    """
    mode = cp.context_mode(context)
    if mode == "opt":
        built = _build_prompt_opt(out_root, pending, request)
    else:
        system, user, wants_json = _build_prompt_legacy(out_root, pending, request)
        built = {"system": system, "user": user, "wants_json": wants_json, "wants_summary": False,
                 "meta": {"policy": "legacy"}}
    step_raw = _plan_step(_load_plan_raw(out_root), str(request.get("step_id"))) or {}
    if rf.FIELD in step_raw:
        block, files_meta = rf.read_repo_files(repo_root_from_out(out_root), step_raw.get(rf.FIELD))
        if block:
            built["user"] += "\n" + _section("Ficheiros do repo (so leitura)", block)
        built["meta"]["repo_files"] = files_meta
    # SEC-1.3 / activate_for_task: so existe quando a skill tem scripts ou o
    # passo pediu pesquisa externa (skill_activation.py); sem ele, nada muda.
    activation_md = pending / "SKILL_ACTIVATION.md"
    if activation_md.is_file():
        built["user"] += "\n" + _section("Activacao da skill (SEC-1.3)", _clip(activation_md.read_text(encoding="utf-8")))
        built["meta"]["skill_activation"] = "SKILL_ACTIVATION.md"
    return built


def _build_prompt_opt(out_root: Path, pending: Path, request: dict[str, Any]) -> dict[str, Any]:
    """B1-bis (plan_runner/context_policy.py): sem frontmatter, grounding por area, pin + resumos."""
    repo_root = repo_root_from_out(out_root)
    plan_raw = _load_plan_raw(out_root)
    step_id = str(request.get("step_id"))
    agent_fm: dict[str, Any] = {}
    system_parts: list[str] = []
    dropped: list[str] = []
    for name, title, kind in (("AGENT.md", "Agente", "agent"), ("SKILL.md", "Skill", "skill")):
        p = pending / name
        if p.is_file():
            fm, body = cp.strip_frontmatter(p.read_text(encoding="utf-8"))
            body, gone = cp.drop_doc_sections(body, kind)
            dropped += [f"{name}: {g}" for g in gone]
            if name == "AGENT.md":
                agent_fm = fm
                if fm.get("description"):
                    body = f"Papel: {fm['description']}\n\n{body}"
            system_parts.append(_section(title, body))
    level, grounding = cp.grounding_for(repo_root, agent_fm.get("id"))
    if grounding:
        _, gbody = cp.strip_frontmatter(grounding)
        system_parts.append(_section("Grounding (obrigatorio)", gbody))

    artifact = request.get("output_artifact") or ""
    wants_json = artifact.lower().endswith(".json")
    wants_summary = cp.needs_summary(plan_raw, step_id, artifact)
    schema = request.get("output_schema")
    fmt = (
        "JSON valido (um unico objecto), sem texto antes nem depois"
        + (f", com a estrutura de `{schema}` descrita na skill" if schema else "")
        if wants_json
        else "Markdown"
    )
    saida = (
        f"Devolve SO o conteudo do artefacto `{artifact or '(sem ficheiro)'}`, em {fmt}. "
        "Sem preambulos nem comentarios sobre a tarefa. Nao tens tools neste passo: "
        "usa apenas o contexto desta mensagem e marca o que falta como lacuna."
    )
    if wants_summary:
        saida += "\n\n" + cp.summary_instruction(wants_json)
    system_parts.append(_section("Saida", saida))

    user_parts = [
        _section(
            "Passo",
            # SEC-2d: concatenacao implicita intencional (mensagem partida em 2 linhas), nao e uma virgula em falta.
            # nosemgrep: string-concat-in-list
            f"- plano: {plan_raw.get('id', '?')}\n- passo: {step_id}\n"
            f"- action: {request.get('action')}\n- artefacto: {artifact or '(nenhum)'}",
        )
    ]
    for key, title in (("objective", "Objectivo do plano"), ("audience", "Audiencia")):
        if plan_raw.get(key):
            user_parts.append(_section(title, str(plan_raw[key])))
    task = (_plan_step(plan_raw, step_id) or {}).get("task")
    if task:
        user_parts.append(_section("Tarefa deste passo", str(task)))

    inputs = cp.step_inputs(plan_raw, step_id, list(request.get("inputs") or []) or None)
    modes = cp.input_modes(plan_raw, step_id, inputs)
    used: list[dict[str, Any]] = []
    for rel in inputs:
        p = (out_root / rel).resolve()
        if not (p.is_relative_to(out_root.resolve()) and p.is_file()):
            user_parts.append(_section(f"Input: {rel}", "(ficheiro em falta -- trata como lacuna)"))
            used.append({"path": rel, "mode": "missing", "chars": 0})
            continue
        mode = modes[rel]
        summ = cp.summary_path(out_root, rel)
        if mode == "summary" and summ.is_file():
            body = summ.read_text(encoding="utf-8")
            user_parts.append(_section(f"Input (resumo): {rel}", body + f"\n(artefacto completo em `{rel}`)"))
        else:
            mode = "full" if mode == "full" else "full (sem resumo)"
            raw = p.read_text(encoding="utf-8")
            body = _clip(cp.compact_json(raw) if rel.lower().endswith(".json") else raw)
            user_parts.append(_section(f"Input: {rel}", body))
        used.append({"path": rel, "mode": mode, "chars": len(body)})

    for name, title in (("knowledge_context.md", "Conhecimento recuperado (L5)"), ("CLIENT_MEMORY.md", "Memoria do cliente")):
        p = pending / name
        if p.is_file():
            user_parts.append(_section(title, _clip(p.read_text(encoding="utf-8"))))

    return {
        "system": "\n".join(system_parts),
        "user": "\n".join(user_parts),
        "wants_json": wants_json,
        "wants_summary": wants_summary,
        "meta": {"policy": "opt", "grounding": level, "inputs": used, "summary_requested": wants_summary,
                 "dropped_sections": dropped},
    }


def _build_prompt_legacy(out_root: Path, pending: Path, request: dict[str, Any]) -> tuple[str, str, bool]:
    """Prompt anterior ao B1-bis, byte a byte (PLAN_RUNNER_CONTEXT=legacy)."""
    repo_root = repo_root_from_out(out_root)
    system_parts: list[str] = []
    for name, title in (("AGENT.md", "Agente"), ("SKILL.md", "Skill")):
        p = pending / name
        if p.is_file():
            system_parts.append(_section(title, p.read_text(encoding="utf-8")))
    grounding = repo_root / "agents" / "_shared" / "grounding.directive.md"
    if grounding.is_file():
        system_parts.append(_section("Grounding (obrigatorio)", grounding.read_text(encoding="utf-8")))

    artifact = request.get("output_artifact") or ""
    wants_json = artifact.lower().endswith(".json")
    schema = request.get("output_schema")
    fmt = (
        "JSON valido (um unico objecto), sem texto antes nem depois"
        + (f", com a estrutura de `{schema}` descrita na skill" if schema else "")
        if wants_json
        else "Markdown"
    )
    system_parts.append(
        _section(
            "Saida",
            f"Devolve SO o conteudo do artefacto `{artifact or '(sem ficheiro)'}`, em {fmt}. "
            "Sem preambulos nem comentarios sobre a tarefa. Nao tens tools neste passo: "
            "usa apenas o contexto desta mensagem e marca o que falta como lacuna.",
        )
    )

    plan_raw = _load_plan_raw(out_root)
    user_parts = [
        _section(
            "Passo",
            # SEC-2d: concatenacao implicita intencional (mensagem partida em 2 linhas), nao e uma virgula em falta.
            # nosemgrep: string-concat-in-list
            f"- plano: {plan_raw.get('id', '?')}\n- passo: {request.get('step_id')}\n"
            f"- action: {request.get('action')}\n- artefacto: {artifact or '(nenhum)'}",
        )
    ]
    for key, title in (("objective", "Objectivo do plano"), ("audience", "Audiencia")):
        if plan_raw.get(key):
            user_parts.append(_section(title, str(plan_raw[key])))
    # `task:` opcional no passo (o router escreve-a em cada passo de um plano gerado).
    task = (_plan_step(plan_raw, str(request.get("step_id"))) or {}).get("task")
    if task:
        user_parts.append(_section("Tarefa deste passo", str(task)))

    # Inputs declarados; sem eles, os artefactos dos passos de que este depende.
    inputs = list(request.get("inputs") or [])
    if not inputs:
        step = _plan_step(plan_raw, str(request.get("step_id"))) or {}
        for dep in step.get("depends_on") or []:
            dep_step = _plan_step(plan_raw, str(dep)) or {}
            if dep_step.get("output_artifact"):
                inputs.append(str(dep_step["output_artifact"]))
    for rel in inputs:
        p = (out_root / rel).resolve()
        if p.is_relative_to(out_root.resolve()) and p.is_file():
            user_parts.append(_section(f"Input: {rel}", _clip(p.read_text(encoding="utf-8"))))
        else:
            user_parts.append(_section(f"Input: {rel}", "(ficheiro em falta -- trata como lacuna)"))

    for name, title in (("knowledge_context.md", "Conhecimento recuperado (L5)"), ("CLIENT_MEMORY.md", "Memoria do cliente")):
        p = pending / name
        if p.is_file():
            user_parts.append(_section(title, _clip(p.read_text(encoding="utf-8"))))

    return "\n".join(system_parts), "\n".join(user_parts), wants_json


def _response_text(response: dict[str, Any]) -> tuple[str, str | None]:
    candidates = response.get("candidates") or []
    if not candidates:
        return "", None
    first = candidates[0] if isinstance(candidates[0], dict) else {}
    parts = (first.get("content") or {}).get("parts") or []
    text = "".join(p.get("text", "") for p in parts if isinstance(p, dict))
    return text, first.get("finishReason")


def _parse_json_output(text: str) -> Any:
    t = text.strip()
    if t.startswith("```"):  # alguns modelos embrulham em ```json mesmo com responseMimeType
        t = t.split("\n", 1)[1] if "\n" in t else ""
        t = t.rsplit("```", 1)[0]
    return json.loads(t)


class GeminiWorker:
    """Executa um passo pendente com o Gemini e escreve result.json."""

    name = "gemini"

    def __init__(
        self,
        *,
        model: str | None = None,
        api_key: str | None = None,
        max_output_tokens: int = DEFAULT_MAX_OUTPUT_TOKENS,
        timeout: float = 60.0,
        transport: Transport | None = None,
        remote_ledger: RemoteSink | None | bool = True,
        context: str | None = None,
        memory: mw.MemoryStore | None | bool = True,
    ):
        self.model = model or os.environ.get("AGENT_MODEL") or DEFAULT_MODEL
        # L4 (D3): True = DATABASE_URL do ambiente (se houver); so e usada por planos com `memory:`.
        self.memory = mw.store_from_env() if memory is True else (memory or None)
        self.context = cp.context_mode(context)  # opt (B1-bis) | legacy
        self._api_key = api_key
        self.max_output_tokens = max_output_tokens
        self.timeout = timeout
        self.transport = transport or httpx_transport
        # True = Supabase se o ambiente o tiver; None/False = so jsonl local.
        self.remote_ledger = supabase_sink_from_env() if remote_ledger is True else (remote_ledger or None)

    def process(self, out_root: Path, step_id: str, *, run_id: str | None = None) -> dict[str, Any]:
        """Executa o passo. Devolve o result.json escrito; lanca WorkerError/HumanGateBlocked."""
        pending = out_root / "pending_steps" / step_id
        result_path = pending / "result.json"
        if result_path.exists():
            return _read_json(result_path)  # idempotente: o passo ja tem resultado
        check_hitl(out_root, step_id)
        # D5: `model_tier` do passo -> modelo (config/model-tiers.yaml); sem tier, o modelo do worker.
        try:
            model, tier = mt.resolve_model(_plan_step(_load_plan_raw(out_root), step_id), self.model)
        except mt.ModelTierError as e:
            raise WorkerError(f"model_tier: {e}") from e
        check_budget(out_root, model)  # antes de gastar: uma pausa de orcamento nao e um erro (sem worker_error.json)
        request_path = pending / "request.json"
        if not request_path.is_file():
            raise WorkerError(f"sem request.json em {pending}")
        request = _read_json(request_path)
        if run_id is None:
            status_path = out_root / "status.json"
            run_id = _read_json(status_path).get("run_id") if status_path.is_file() else None

        try:
            return self._run(out_root, pending, request, step_id, run_id, model=model, tier=tier)
        except WorkerError as e:
            (pending / ERROR_FILE).write_text(
                json.dumps({"at": _now(), "model": model, "error": str(e)}, indent=2, ensure_ascii=False) + "\n",
                encoding="utf-8",
            )
            raise

    def _run(
        self, out_root: Path, pending: Path, request: dict, step_id: str, run_id: str | None,
        *, model: str | None = None, tier: str | None = None,
    ) -> dict[str, Any]:
        model = model or self.model
        built = build_prompt_ctx(out_root, pending, request, context=self.context)
        system, user, wants_json = built["system"], built["user"], built["wants_json"]
        agent_id = _frontmatter(pending / "AGENT.md").get("id") or request.get("action")

        # L4 (D3, docs/ops/MEMORY-L4.md): so com bloco `memory:` no plano.
        plan_raw = _load_plan_raw(out_root)
        try:
            sm = mw.step_memory(plan_raw, _plan_step(plan_raw, step_id) or {}, agent_id)
        except mw.l4.L4Error as e:
            raise WorkerError(f"memory: {e}") from e
        mem_meta: dict[str, Any] | None = None
        wants_memory = False
        if sm is not None:
            mem_meta = {"scopes": [str(x) for x in sm.chain]}
            if self.memory is None:
                mem_meta["error"] = "plano com `memory:` mas sem DATABASE_URL: L4 desligada neste run"
            else:
                if sm.recall is not None:
                    task = (_plan_step(plan_raw, step_id) or {}).get("task") or ""
                    query = f"{plan_raw.get('objective', '')} {task} {request.get('action', '')}"[:1000]
                    block, mem_meta["recall"] = mw.recall_block(self.memory, sm, query)
                    if block:
                        user += "\n" + _section("Memoria L4 (factos entre runs)", block)
                if sm.remember is not None:
                    wants_memory = True
                    system += "\n" + _section("Memoria", mw.remember_instruction(sm, wants_json))

        response = gemini_generate(
            system,
            user,
            model=model,
            api_key=self._api_key,
            wants_json=wants_json,
            max_output_tokens=self.max_output_tokens,
            timeout=self.timeout,
            transport=self.transport,
        )

        row = build_usage_row(run_id=run_id, agent_id=agent_id, model=model, response=response)
        ledger = record_token_usage(out_root, row, step_id=step_id, run_id=run_id, remote=self.remote_ledger)

        text, finish = _response_text(response)
        if not text.strip():
            raise WorkerError(f"gemini: resposta vazia (finishReason={finish})")
        content: Any = text
        if wants_json:
            try:
                content = _parse_json_output(text)
            except json.JSONDecodeError as e:
                raise WorkerError(f"gemini: JSON invalido para {request.get('output_artifact')}: {e.msg}") from e
        memories: list[dict[str, Any]] = []
        if wants_memory:
            content, memories, parse_errors = mw.extract_memories(content, wants_json)
            if parse_errors:
                mem_meta["parse_errors"] = parse_errors
            if wants_json and not isinstance(content, (dict, list)):
                raise WorkerError(f"gemini: `artifact` invalido para {request.get('output_artifact')}")
        summary = None
        if built["wants_summary"]:
            content, summary = cp.split_summary(content, wants_json)
            if wants_json and not isinstance(content, (dict, list)):
                raise WorkerError(f"gemini: `artifact` invalido para {request.get('output_artifact')}")
        context_meta = {**built["meta"], "summary": "written" if summary else ("missing" if built["wants_summary"] else "not_needed")}

        result = {
            "ok": True,
            "detail": f"gemini:{row['model_version'] or model}",
            "artifact_content": content,
            "meta": {
                "context": context_meta,
                "worker": self.name,
                "model": model,
                "model_version": row["model_version"],
                "finish_reason": finish,
                "tokens_in": row["tokens_in"],
                "tokens_out": row["tokens_out"],
                "tokens_total": row["tokens_total"],
                "response_id": row["response_id"],
                "ledger_remote": ledger["remote"],
            },
        }
        if tier is not None:
            result["meta"]["model_tier"] = tier
        if summary:
            result["artifact_summary"] = summary  # o executor grava-o em <artefacto>.summary.md
        if wants_memory:
            mem_meta["remember"] = mw.write_memories(
                self.memory, sm, memories, out_root=out_root, run_id=run_id, plan_id=plan_raw.get("id"), step_id=step_id)
        if mem_meta is not None:
            result["meta"]["memory"] = mem_meta
        (pending / "result.json").write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        (pending / ERROR_FILE).unlink(missing_ok=True)
        return result


WORKERS = ("gemini",)


def make_worker(name: str | None) -> GeminiWorker | None:
    if name in (None, "", "none"):
        return None
    if name == "gemini":
        return GeminiWorker()
    raise ValueError(f"worker desconhecido {name!r} (opcoes: none, {', '.join(WORKERS)})")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="plan_runner.external_worker",
        description="Executa com o Gemini o passo em waiting_external de um run (qualquer engine).",
    )
    parser.add_argument("out", type=Path, help="Directorio do run (com status.json)")
    parser.add_argument("--resume", action="store_true", help="Depois do passo, retoma o run com o worker inline (engine native)")
    args = parser.parse_args(argv)

    out = args.out.resolve()
    status_path = out / "status.json"
    if not status_path.is_file():
        print(f"error: sem status.json em {out}", file=sys.stderr)
        return 1
    status = _read_json(status_path)
    worker = GeminiWorker()
    try:
        if status.get("state") == "paused_human_gate":
            check_hitl(out, str(status.get("paused_at_step")))
        if status.get("state") == "paused_budget":
            check_budget(out)  # se o tecto ja foi subido no status, segue como waiting_external
        if status.get("state") not in ("waiting_external", "paused_budget"):
            print(f"error: run em {status.get('state')!r}, nao em waiting_external", file=sys.stderr)
            return 1
        step_id = str(status.get("paused_at_step"))
        result = worker.process(out, step_id, run_id=status.get("run_id"))
    except HumanGateBlocked as e:
        print(f"hitl: {e}", file=sys.stderr)
        return 2
    except BudgetExceeded as e:
        flag = "--max-cost-usd X" if e.unit == "usd" else "--max-tokens N"
        print(f"budget: {e}; sobe o tecto com `python -m plan_runner resume <run> {flag}`", file=sys.stderr)
        return 3
    except WorkerError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1

    summary: dict[str, Any] = {"step_id": step_id, "detail": result.get("detail"), "meta": result.get("meta")}
    if args.resume:
        if str(status.get("engine", "")).startswith("langgraph"):
            summary["resume"] = "engine langgraph: corre `python -m plan_runner resume <run>` para continuar"
        else:
            from .engine import resume_run

            summary["status"] = resume_run(out, decision="approve", worker="gemini")
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
