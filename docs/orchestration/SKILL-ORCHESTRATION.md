# Invocacao de skills — orquestrador

## Problema

Invocacao **manual** ("usa a skill X") nao escala.  
Invocacao **so** por magia de description no IDE nao cobre pipelines auditaveis.

## Solucao neste repo (hibrida)

```text
                    pedido do user
                          │
          ┌───────────────┴───────────────┐
          ▼                               ▼
   deliverable conhecido            tarefa livre / IDE
   (seo_article, social_pack, …)    ("cria endpoint…")
          │                               │
          ▼                               ▼
   plan.yaml template              using-agent-skills
   (orchestrator marketing)        (meta mapa de skills)
          │                               │
          ▼                               ▼
   steps[].action ──────────────► SKILL.md + agent
          │
          ▼
   plan_runner external / worker
```

| Componente | Ficheiro |
|------------|----------|
| Meta-skill | `skills/meta/using-agent-skills/SKILL.md` |
| Meta-agent | `agents/meta/using_agent_skills.agent.md` |
| Regras IDE/repo | `AGENTS.md` |
| Marketing orchestrator | `docs/orchestration/marketing/ORCHESTRATOR.md` |
| Wiring runner | `docs/orchestration/marketing/AGENT-SKILL-WIRING.md` |

## Addy Osmani `using-agent-skills`

No ecossistema `npx skills add addyosmani/agent-skills`, a meta-skill dele governa as **25 skills de engenharia** no IDE.

Aqui temos **equivalente de repo**: `skills/meta/using-agent-skills` para skills **deste** monorepo + ponte para templates de plan.

Nao substituir um pelo outro: **coding IDE** (Addy) ∥ **lab marketing/Item 13** (este setup).

## Garantir invocacao

1. Agentes que leem `AGENTS.md` na raiz passam a ter a regra de orquestracao.
2. Claude Code / Cursor: manter `AGENTS.md` ou espelhar o bloco em `CLAUDE.md` local se preciso.
3. Pipelines: nao depender de description matching — usar **plan**.

## Teste rapido (descoberta)

Pedido: *"preciso de um artigo sobre AI Findability"*  
Esperado do meta: `suggested_plan_template` → `seo-article` ou demo; primary `research` / fluxo P0.

Pedido: *"pack social LinkedIn"*  
Esperado: `social-pack.plan.yaml` + skills P1.
