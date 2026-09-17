---
name: using-agent-skills
action: using_agent_skills
version: 1
priority: P0
role: orchestrator_meta
description: >-
  Meta-skill de descoberta: inventaria e selecciona as skills certas para uma tarefa (modo B, sessao livre) ou valida a action ja fixada num plan.yaml (modo A). Nao executa a tarefa, so devolve o mapa de invocacao. Activar como primeiro passo sempre que nao ha action ja decidida.
requires: []
---

# Skill — using-agent-skills (meta / orquestrador de descoberta)

## Trigger

Sempre que não há `action` já decidida para o pedido — seja porque é sessão livre (modo B), seja para confirmar/validar uma `action` que já veio fixada num `plan.yaml` (modo A).

## Inputs

- O pedido do utilizador (objectivo, domínio, riscos)
- `skills/marketing/*/SKILL.md`, `skills/meta/*/SKILL.md`, e (se instalado) `~/.agents/skills/*/SKILL.md`
- `plan.yaml` com `steps[].action`, quando aplicável (modo A)

## Passos

Meta-skill: **descobrir** e **seleccionar** skills do repo para a tarefa actual. Não implementa a tarefa final — devolve um **mapa de invocação**.

**Dois modos no projecto:**

| Modo | Quem decide a skill | Quando |
|------|---------------------|--------|
| **A — Plan-execute** | `steps[].action` no `plan.yaml` | Runner lab / pipelines marketing |
| **B — Descoberta por contexto** | Esta meta-skill + descriptions | Sessão livre no IDE (Claude/Cursor/Copilot) |

Em **modo A** o orchestrator de marketing **já** fixou a action; esta skill só valida se a action existe e aponta o path. Em **modo B** (pedido livre do user) esta skill é o **primeiro** passo.

**Processo (modo B):**

1. Ler o pedido do utilizador (objectivo, domínio, riscos).
2. Inventariar skills em `skills/marketing/*/SKILL.md`, `skills/meta/*/SKILL.md`, e (se instalado) `~/.agents/skills/*/SKILL.md`.
3. Para cada candidata, ler frontmatter `name` + `description` (todas as skills deste repo já têm este campo).
4. Seleccionar 1–N skills **sem** mesh de agentes (lista ordenada).
5. Preferir templates de plan se o pedido for deliverable conhecido (`seo_article`, `social_pack`, …).
6. Emitir o mapa de invocação (abaixo) e **parar** — o executor/plan aplica as skills.

**Processo (modo A):**

1. Ler `steps[].action` actual.
2. Resolver `skills/marketing/<action>/SKILL.md` ou vertical correcta.
3. Se não existir: reportar gap; não inventar action.
4. Anexar `agents/.../<action>.agent.md` se existir.

**Saída obrigatória:**

```markdown
## Skill invocation map

- mode: plan | discovery
- primary_skill: path ou name
- supporting_skills: []
- suggested_plan_template: path ou null
- agent_paths: []
- rationale: 1-3 frases
- do_not_invoke: []  # skills tentadoras mas erradas
```

## Enforcement Note

Advisory — esta skill orienta a descoberta, não aplica nada mecanicamente. Nada impede um agente de ignorar o mapa de invocação e activar skills directamente.

## Done When

- [ ] Mapa preenchido
- [ ] Pelo menos `primary_skill` ou `suggested_plan_template`
- [ ] Nenhuma persona a orquestrar outra persona

## Anti-padrões

- Executar copy/seo dentro desta skill
- Activar 10 skills "por si acaso"
- Ignorar `plan.yaml` quando o runner já está a meio de um plan
- Reduzir tudo a Google quando o tema é Item 13 multi-IA

## Knowledge Ref

Sem atribuição externa — desenho de orquestração interno a este repo, não adaptado de nenhuma skill de terceiros.
