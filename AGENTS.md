# AGENTS.md — Network Agents Setup

**Núcleo do produto** (motor + governança + horizontais + RAG) — não é lab/método, correcção de 2026-09-18 (ver `docs/architecture/ECOSYSTEM.md`). Marketing + design + Item 13 + plan-execute continuam a viver aqui.  
Producao MCP: repo separado `agent-network-mcp` — traz os **verticais** (agentes proprietários, 20 dos 33). Os **horizontais** (13 dos 33) já foram migrados para cá (G2: 16 skills, G4: 13 agentes, ver `docs/architecture/MCP-MAPPING.md`) — a regra já não é "não misturar sem decisão explícita", é "horizontais migram para cá, verticais ficam lá", decisão já tomada e executada.

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

## Credenciais

Não há secrets manager configurado neste repo. Uma sessão nova precisa de `GITHUB_TOKEN` (ou equivalente) fornecido explicitamente no ambiente para operações de API do GitHub — não assumir que existe um token guardado de sessão anterior, e não ir procurar um em histórico de conversas antigas (risco de token obsoleto/de escopo largo demais). Pedir ao utilizador se precisar.

## Runner

```text
runner/plan_runner  →  pending_steps/<id>/SKILL.md + AGENT.md
```

Ver `docs/orchestration/marketing/AGENT-SKILL-WIRING.md`.
