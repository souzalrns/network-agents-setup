# AGENTS.md — Network Agents Setup

Repo de **lab/metodo** multi-agente (marketing + design + Item 13 + plan-execute).  
Producao MCP: repo separado `agent-network-mcp` — nao misturar sem decisao explicita.

## Skill orchestration

1. **Pedido livre (IDE):** no inicio de tarefa nao trivial, aplicar  
   `skills/meta/using-agent-skills/SKILL.md` (action `using_agent_skills`)  
   para mapear tarefa → skills / template de plan.
2. **Pipeline formal:** o `plan.yaml` e a fonte de verdade;  
   `steps[].action` resolve `skills/**/<action>/SKILL.md` + `agents/**/<action>.agent.md`  
   via `plan_runner` (mode `external`).
3. **Nao** esperes que o utilizador nomeie skills — descobre ou usa o plan.
4. Personas **nao** invocam outras personas; so o plan / meta-skill / humano orquestra.
5. Publish / spend / credenciais: **HITL** obrigatorio.
6. Item 13 = multi-IA (ChatGPT, Claude, Gemini, Perplexity, …), nao so Google.

## Grounding (obrigatório)

7. **Nunca inventar factos** ausentes do contexto (RAG, artefactos, L4, bancos operacionais).  
   Ver `agents/_shared/grounding.directive.md` e `docs/architecture/memory/GROUNDING.md`.  
   Se não estiver no contexto → dizer que não tens o dado.
8. **Ingest ≠ fonte certa:** L5 (`knowledge_chunks`) não substitui bancos de status operacional.  
   Dual-source e retrieve L5: `docs/architecture/memory/rag-l5.md`.

## Onde estao as skills

| Path | Conteudo |
|------|----------|
| `skills/marketing/` | P0/P1 marketing + Item 13 |
| `skills/design/` | UX / UI / writing |
| `skills/meta/` | Orquestracao de descoberta |
| CLI `npx skills` (addyosmani) | Engenharia no IDE — paralelo, nao substitui este repo |

## Runner

```text
runner/plan_runner  →  pending_steps/<id>/SKILL.md + AGENT.md
```

Ver `docs/orchestration/marketing/AGENT-SKILL-WIRING.md`.
