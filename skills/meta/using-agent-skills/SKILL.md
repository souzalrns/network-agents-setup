---
name: using-agent-skills
action: using_agent_skills
version: 1
priority: P0
role: orchestrator_meta
---

# Skill — using-agent-skills (meta / orquestrador de descoberta)

## Papel

Meta-skill: **descobrir** e **seleccionar** skills do repo para a tarefa actual.  
Nao implementa a tarefa final — devolve um **mapa de invocacao**.

## Dois modos no projecto

| Modo | Quem decide a skill | Quando |
|------|---------------------|--------|
| **A — Plan-execute** | `steps[].action` no `plan.yaml` | Runner lab / pipelines marketing |
| **B — Descoberta por contexto** | Esta meta-skill + descriptions | Sessao livre no IDE (Claude/Cursor/Copilot) |

Em **modo A** o orchestrator de marketing **ja** fixou a action; esta skill so valida se a action existe e aponta o path.  
Em **modo B** (pedido livre do user) esta skill e o **primeiro** passo.

## Processo (modo B)

1. Ler o pedido do utilizador (objectivo, dominio, riscos).
2. Inventariar skills em:
   - `skills/marketing/*/SKILL.md`
   - `skills/meta/*/SKILL.md`
   - (se instalado) `~/.agents/skills/*/SKILL.md` ou caminho do CLI skills
3. Para cada candidata, ler frontmatter `name` + primeiros paragrafos / "Use when" / "Quando usar".
4. Seleccionar 1–N skills **sem** mesh de agentes (lista ordenada).
5. Preferir templates de plan se o pedido for deliverable conhecido (`seo_article`, `social_pack`, …).
6. Emitir o mapa de invocacao (abaixo) e **parar** — o executor/plan aplica as skills.

## Processo (modo A)

1. Ler `steps[].action` actual.
2. Resolver `skills/marketing/<action>/SKILL.md` ou vertical correcta.
3. Se nao existir: reportar gap; nao inventar action.
4. Anexar `agents/.../<action>.agent.md` se existir.

## Saida obrigatoria

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

## done_when

- [ ] Mapa preenchido
- [ ] Pelo menos primary_skill ou suggested_plan_template
- [ ] Nenhuma persona a orquestrar outra persona

## Anti-padroes

- Executar copy/seo dentro desta skill
- Activar 10 skills "por si acaso"
- Ignorar plan.yaml quando o runner ja esta a meio de um plan
- Reduzir tudo a Google quando o tema e Item 13 multi-IA
