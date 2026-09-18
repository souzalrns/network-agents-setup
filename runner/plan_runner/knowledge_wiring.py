"""S9 -- liga o L5 (retrieve_knowledge/McpKnowledge) a execucao real de planos.

Design: docs/architecture/memory/FASE4-SINTESE.md secao "Fase 0 -- agora".
Achado que motivou isto: docs/architecture/memory/FASE1-MEMORIA.md confirmou,
por leitura directa do codigo, que retrieve_knowledge/McpKnowledge nunca eram
chamados por engine.py/langgraph_engine.py/cli.py/executor.py -- o RAG (L5)
existia mas estava desligado da execucao.

Este modulo e ADITIVO:
    - NAO toca em executor.py (execute_stub/execute_external_request
      continuam com o mesmo contrato, a mesma StepResult, o mesmo request.json).
    - NAO toca em models.py (le step.raw, que ja guarda o dict original do
      YAML, sem precisar de um campo novo em Step).
    - Escreve um ficheiro NOVO, `pending_steps/<step_id>/knowledge_context.md`,
      ao lado do que execute_external_request ja escreve nesse mesmo
      directorio -- nunca dentro de request.json, nunca substitui nada.
    - Opt-in por step: so corre se o step tiver um bloco `knowledge:` no
      plan.yaml. Planos existentes sem esse bloco ficam 100% inalterados.

Formato do bloco opcional no plan.yaml:

    steps:
      - id: research
        action: research
        knowledge:
          kb: marketing
          query: "..."       # obrigatorio
          top_k: 8            # opcional, default do proprio retrieve_knowledge
          require_citations: false   # opcional, default do proprio retrieve_knowledge

Falha de retrieval (rede, quota Gemini excedida, MCP_API_KEY em falta, etc.)
nunca aborta o step nem o plano -- fica registada no events.jsonl e um
ficheiro de contexto com o motivo da falha e escrito, para nao deixar o
worker externo (humano ou agente) sem saber que o contexto nao chegou.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

from .events import EventLog
from .knowledge import grounding_block, retrieve_knowledge
from .mcp_knowledge import McpKnowledge, McpKnowledgeError
from .models import Step

CONTEXT_FILENAME = "knowledge_context.md"


def _context_path(out_root: Path, step: Step) -> Path:
    return out_root / "pending_steps" / step.id / CONTEXT_FILENAME


def inject_knowledge_context(
    out_root: Path,
    step: Step,
    log: EventLog,
    run_id: str,
) -> None:
    """Se o step pedir conhecimento (bloco `knowledge:` no plan.yaml), busca-o
    no L5 e escreve-o ao lado dos outros ficheiros do step. No-op silencioso
    se o step nao pedir nada -- e o caso de todos os planos existentes hoje.
    """
    spec = step.raw.get("knowledge") if isinstance(step.raw, dict) else None
    if not spec or not isinstance(spec, dict):
        return

    kb = spec.get("kb")
    query = spec.get("query")
    if not kb or not query:
        log.append(
            "knowledge_context_skipped",
            run_id,
            {"step_id": step.id, "reason": "knowledge block missing kb or query"},
        )
        return

    top_k = spec.get("top_k")
    require_citations = spec.get("require_citations")
    filters = spec.get("filters")

    kwargs: dict[str, Any] = {"backend": McpKnowledge()}
    if top_k is not None:
        kwargs["top_k"] = int(top_k)
    if require_citations is not None:
        kwargs["require_citations"] = bool(require_citations)
    if filters is not None:
        kwargs["filters"] = filters

    path = _context_path(out_root, step)
    path.parent.mkdir(parents=True, exist_ok=True)

    try:
        hits = retrieve_knowledge(kb, query, **kwargs)
    except McpKnowledgeError as e:
        # Falha conhecida (429 Gemini, rede, MCP_API_KEY em falta, etc.) --
        # nao aborta o step. Ver RATE-LIMITS.md para o achado da quota.
        path.write_text(
            "[L5 CONTEXT: FALHA]\n"
            f"Nao foi possivel obter contexto de '{kb}' -- {e}\n"
            "Prossegue sem este contexto; nao inventar dados que substituam "
            "o que faltou.\n"
            "[/L5 CONTEXT]\n",
            encoding="utf-8",
        )
        log.append(
            "knowledge_context_failed",
            run_id,
            {"step_id": step.id, "kb": kb, "error": str(e)[:300]},
        )
        return
    except Exception as e:  # noqa: BLE001 -- enriquecimento opcional, nunca derruba o step
        path.write_text(
            "[L5 CONTEXT: FALHA]\n"
            f"Erro inesperado ao obter contexto de '{kb}': {e}\n"
            "[/L5 CONTEXT]\n",
            encoding="utf-8",
        )
        log.append(
            "knowledge_context_failed",
            run_id,
            {"step_id": step.id, "kb": kb, "error": f"{type(e).__name__}: {e}"[:300]},
        )
        return

    path.write_text(grounding_block(hits), encoding="utf-8")
    log.append(
        "knowledge_context_injected",
        run_id,
        {"step_id": step.id, "kb": kb, "hit_count": len(hits)},
    )
