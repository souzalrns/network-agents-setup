"""L4 no worker: recall antes da chamada, remember opt-in depois (D3; MEMORY-L4.md).

Tudo e opt-in pelo plano -- sem bloco `memory:` nao ha L4 nenhuma (nem ligacao
a BD) e o worker faz exactamente o que fazia.

    memory:                      # topo do plano: a cadeia de ambitos deste trabalho
      org: acme                  # opcional
      project: site-a            # opcional (recomendado)
      user: maria                # opcional
      recall: {limit: 8, tags: [], include_candidates: false}   # omissoes
    steps:
      - id: copy
        recall: false            # opcional: desliga o recall neste passo
        remember: true           # opt-in: o agente pode propor factos (candidate)
        # ou remember: {scope: project|user|agent, max: 5, tags: [...]}

- Cadeia de leitura do passo: global:global + org + project + user (os que
  existirem) + agent:<id do AGENT.md>. Nunca le outro projecto/agente.
- Escrita: so project/user/agent DESTA cadeia (memory_l4.AGENT_WRITABLE + allowed);
  status sempre candidate; um pedido HITL de promocao por passo
  (memory_l4.request_promotion) -- o run nao para.
- Injeccao: so memorias `active` por omissao (candidates nao entram no prompt
  sem gate humano, D3).
- Falha da L4 (BD em baixo, sem tabela, ...) nunca parte o passo: fica no meta.
"""
from __future__ import annotations

import json
import os
from collections.abc import Callable
from contextlib import AbstractContextManager
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from . import memory_l4 as l4

MEMORY_MARKER = "=====MEMORIA====="
TRACE_FILE = "memory_l4.jsonl"
MAX_BLOCK_CHARS = 4000
DEFAULT_RECALL_LIMIT = 8
DEFAULT_REMEMBER_MAX = 5


@dataclass
class MemoryStore:
    """Como chegar a BD da L4 + embedder. Injectavel nos testes."""

    connect: Callable[[], AbstractContextManager[Any]]
    embed: l4.Embed | None = None


def store_from_env() -> MemoryStore | None:
    """DATABASE_URL (o mesmo do J3/RAG) => store; sem ele, None (L4 desligada)."""
    if not os.environ.get("DATABASE_URL", "").strip():
        return None
    embed = None
    if os.environ.get("GEMINI_API_KEY"):
        from .embedder import embed_text

        embed = embed_text
    return MemoryStore(connect=l4.connect, embed=embed)


@dataclass
class StepMemory:
    chain: list[l4.Scope]
    recall: dict[str, Any] | None
    remember: dict[str, Any] | None
    agent_id: str


def step_memory(plan_raw: dict[str, Any], step_raw: dict[str, Any], agent_id: str | None) -> StepMemory | None:
    mem = plan_raw.get("memory")
    if not isinstance(mem, dict):
        return None
    agent = agent_id or str(step_raw.get("action") or "unknown")
    chain = [l4.Scope("global", "global")]
    for kind in ("org", "project", "user"):
        if mem.get(kind):
            chain.append(l4.Scope(kind, str(mem[kind])))
    chain.append(l4.Scope("agent", agent))

    rec = step_raw.get("recall", True)
    recall = None
    if rec is not False:
        base = {"limit": DEFAULT_RECALL_LIMIT, "tags": None, "include_candidates": False}
        base.update(mem.get("recall") or {})
        if isinstance(rec, dict):
            base.update(rec)
        recall = base

    rem = step_raw.get("remember", False)
    remember = None
    if rem:
        cfg = rem if isinstance(rem, dict) else {}
        kind = cfg.get("scope") or ("project" if mem.get("project") else "agent")
        target = next((s for s in chain if s.kind == kind), None)
        if target is None or kind not in l4.AGENT_WRITABLE:
            raise l4.ScopeError(f"remember.scope={kind!r} nao existe na cadeia do passo ou nao e escrevivel por agente")
        remember = {"scope": target, "max": int(cfg.get("max") or DEFAULT_REMEMBER_MAX), "tags": list(cfg.get("tags") or [])}
    return StepMemory(chain=chain, recall=recall, remember=remember, agent_id=agent)


def _trace(out_root: Path, entry: dict[str, Any]) -> None:
    try:
        with (out_root / TRACE_FILE).open("a", encoding="utf-8") as f:
            f.write(json.dumps({"at": datetime.now(UTC).isoformat(), **entry}, ensure_ascii=False, default=str) + "\n")
    except OSError:
        pass


def recall_block(store: MemoryStore, sm: StepMemory, query: str) -> tuple[str | None, dict[str, Any]]:
    """(seccao markdown | None, meta). Nunca lanca."""
    cfg = sm.recall or {}
    meta: dict[str, Any] = {"scopes": [str(s) for s in sm.chain]}
    try:
        with store.connect() as conn:
            rows = l4.recall(conn, scopes=sm.chain, query=query, limit=int(cfg.get("limit", DEFAULT_RECALL_LIMIT)),
                             tags=cfg.get("tags") or None, include_candidates=bool(cfg.get("include_candidates")),
                             embed=store.embed)
    except Exception as e:  # noqa: BLE001 -- a L4 nunca parte o passo
        meta["error"] = f"{type(e).__name__}: {str(e)[:200]}"
        return None, meta
    meta["recalled"] = [str(r["id"]) for r in rows]
    if not rows:
        return None, meta
    lines, used = [], 0
    for r in rows:
        tag = "" if r["status"] == "active" else " (candidato, NAO confirmado por humano)"
        conf = f"; confianca {r['confidence']:.2f}" if r.get("confidence") is not None else ""
        line = f"- [{r['scope_kind']}:{r['scope_id']}] {r['statement']}{tag} (memoria L4 {r['id']}{conf})"
        if used + len(line) > MAX_BLOCK_CHARS:
            break
        lines.append(line)
        used += len(line)
    body = ("Factos guardados entre runs. Usa-os como contexto; se o pedido os contradisser, "
            "segue o pedido e assinala a contradicao.\n\n" + "\n".join(lines))
    return body, meta


def remember_instruction(sm: StepMemory, wants_json: bool) -> str:
    n = sm.remember["max"]
    item = '{"statement": "<facto curto>", "subject": "<tema>", "confidence": <0-1>}'
    rule = (f"Memoria (opcional): se este passo estabelecer factos ESTAVEIS que valha a pena lembrar noutros runs "
            f"(preferencias, decisoes, correccoes do operador), propoe ate {n}, so suportados pelo contexto e com a fonte "
            "no statement; nada de hipoteses. Ficam como candidatos ate um humano os aprovar.")
    if wants_json:
        return (rule + f" Devolve entao o objecto de topo com a chave `artifact` (o artefacto) e a chave `memoria` "
                f"(lista de {item}); sem factos, `memoria` vazia.")
    return rule + f" Escreve-os no fim, depois de uma linha so com `{MEMORY_MARKER}`, um por linha, como {item}."


def extract_memories(content: Any, wants_json: bool) -> tuple[Any, list[dict[str, Any]], list[str]]:
    """(conteudo sem o bloco de memoria, itens, erros de parse)."""
    errors: list[str] = []
    if wants_json:
        if isinstance(content, dict) and "memoria" in content:
            content = dict(content)
            raw = content.pop("memoria")
            if set(content) == {"artifact"}:
                content = content["artifact"]
            items = raw if isinstance(raw, list) else []
        else:
            return content, [], []
    else:
        text = str(content)
        if f"\n{MEMORY_MARKER}" not in "\n" + text:
            return content, [], []
        body, _, block = ("\n" + text).partition(f"\n{MEMORY_MARKER}")
        content = body.lstrip("\n")
        items = []
        for line in block.strip().splitlines():
            line = line.strip().lstrip("-").strip()
            if not line:
                continue
            try:
                items.append(json.loads(line))
            except json.JSONDecodeError:
                errors.append(f"linha de memoria nao e JSON: {line[:80]}")
    good = [i for i in items if isinstance(i, dict) and str(i.get("statement") or "").strip()]
    return content, good, errors


def write_memories(
    store: MemoryStore,
    sm: StepMemory,
    items: list[dict[str, Any]],
    *,
    out_root: Path,
    run_id: str | None,
    plan_id: str | None,
    step_id: str,
) -> dict[str, Any]:
    """Grava as propostas como candidate e abre o pedido HITL. Nunca lanca."""
    meta: dict[str, Any] = {"proposed": len(items), "written": [], "rejected": []}
    if not items:
        return meta
    allowed = [s for s in sm.chain if s.kind in l4.AGENT_WRITABLE]
    rows = []
    try:
        with store.connect() as conn:
            for item in items[: sm.remember["max"]]:
                conf = item.get("confidence")
                try:
                    row = l4.remember(
                        conn, scope=sm.remember["scope"], statement=str(item["statement"]),
                        actor=f"agent:{sm.agent_id}", subject=item.get("subject"),
                        confidence=float(conf) if isinstance(conf, (int, float)) and not isinstance(conf, bool) else None,
                        source_run_id=run_id, tags=sm.remember["tags"] + [f"step:{step_id}"],
                        metadata={"plan_id": plan_id, "step_id": step_id}, allowed=allowed, embed=store.embed)
                    rows.append(row)
                    meta["written"].append(str(row["id"]))
                    _trace(out_root, {"op": "remember", "step_id": step_id, "id": row["id"], "status": row["status"],
                                      "scope": str(sm.remember["scope"]), "statement": row["statement"]})
                except l4.L4Error as e:
                    conn.rollback()
                    meta["rejected"].append(str(e))
                    _trace(out_root, {"op": "remember_rejected", "step_id": step_id, "error": str(e)})
            if len(items) > sm.remember["max"]:
                meta["rejected"].append(f"{len(items) - sm.remember['max']} acima do max {sm.remember['max']}")
    except Exception as e:  # noqa: BLE001 -- a L4 nunca parte o passo
        meta["error"] = f"{type(e).__name__}: {str(e)[:200]}"
        _trace(out_root, {"op": "remember_error", "step_id": step_id, "error": meta["error"]})
    req = l4.request_promotion(out_root, rows, run_id=run_id, plan_id=plan_id, step_id=step_id, agent_id=sm.agent_id)
    if req:
        meta["hitl_request"] = req["id"]
    return meta
