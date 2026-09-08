---
name: creative_review
action: creative_review
version: 1
vertical: marketing
priority: P0
---

# Skill — creative_review

## Quando usar

- Step `action: creative_review` (ex. template `approval_rounds`).
- Revisão de peça criativa com rubrica, antes ou entre HITLs.

## Não usar

- Substituir `critic_item13` em artigos SEO se o plan pede explicitamente critic_item13 (podes complementar, não omitir Item 13).

## Inputs

- Draft actual (`inputs` / artefactos)
- Brief interno ou seo_brief se existir
- Rubrica: `docs/knowledge/marketing/creative-review-rubric.md`

## Processo

Avaliar 1–5:

1. On-brief  
2. Clareza  
3. Canal-fit  
4. Brand  
5. Risco  
6. Item 13 (se discoverable)

Listar blockers e suggestions.  
`publish_ready` = true só se blockers vazio e média ≥ 4 (ou limiar do project).

## Saída JSON

```json
{
  "scores": {
    "on_brief": 0,
    "clarity": 0,
    "channel_fit": 0,
    "brand": 0,
    "risk": 0,
    "item_13": 0
  },
  "blockers": [],
  "suggestions": [],
  "publish_ready": false,
  "summary": ""
}
```

## done_when

- [ ] Todas as dimensões relevantes com score ou N/A justificado
- [ ] publish_ready explícito
- [ ] Blockers acionáveis

## Anti-padrões

- Gosto pessoal sem rubrica
- Aprovar com blocker de risco legal/ToS
