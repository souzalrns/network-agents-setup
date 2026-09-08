---
name: critic_item13
action: critic_item13
version: 1
vertical: marketing
priority: P0
item_13: true
---

# Skill — critic_item13

## Quando usar

- Step `action: critic_item13` (ou `critic` em peças discoverable) após copy/brief.

## Não usar

- Para reescrever a peça inteira (devolver gaps; replan/copy corrige).
- Para aprovar publish (humano no HITL).

## Inputs

- Seo brief + copy (paths em `inputs`)
- Playbook Item 13 e knowledge ai-findability
- Rubrica: `docs/knowledge/marketing/creative-review-rubric.md` (dimensão Item 13 + resto se útil)

## Tools

Tipicamente só `read_repo_file`.

## Processo

1. Verificar alinhamento copy ↔ brief (intent, outline, unique promise).
2. Checklist Item 13 (PASS/FAIL por item; adaptar ao playbook do repo):
   - resposta citável cedo
   - entidades claras
   - FAQ ou equivalente estruturado
   - headings úteis a extracção
   - claims rastreáveis
   - risco thin/canibalização se aplicável
3. Blockers vs suggestions (blocker = impede `publish_ready`).
4. Scores 1–5 se usares rubrica multi-dimensão.
5. `publish_ready`: true **só** se blockers vazio e (se scores) média ≥ 4.

## Saída (`CriticReport` / JSON)

```json
{
  "publish_ready": false,
  "scores": {},
  "item_13": {
    "pass": [],
    "fail": []
  },
  "blockers": [],
  "suggestions": [],
  "summary": ""
}
```

## done_when

- [ ] `publish_ready` boolean explícito
- [ ] Pelo menos uma secção item_13 ou equivalenте fail/pass
- [ ] Blockers acionáveis (o que mudar)

## Anti-padrões

- "Está bom" sem critérios
- publish_ready true com fail Item 13 P0
- Reescrever o artigo dentro do critic
