---
name: critic_item13
action: critic_item13
version: 2
vertical: marketing
priority: P0
item_13: true
---

# Skill — critic_item13

## Quando usar

- Apos copy/brief em pecas discoverable.

## Alvo de avaliacao

Avaliar citabilidade para **sistemas de IA em geral** (ChatGPT, Claude, Gemini, Perplexity, Copilot, AI overviews, RAG) — **nao** apenas visibilidade Google.

SEO tecnico SERP e complementar; falhas so de ranking Google **nao** esgotam o Item 13.

## Processo

1. Alinhamento copy ↔ brief.
2. Checklist Item 13 (PASS/FAIL):
   - resposta citavel cedo
   - entidades claras
   - FAQ ou equivalente
   - headings uteis a extracao
   - claims rastreaveis
   - discurso multi-IA (nao reduzido indevidamente a um unico motor)
   - thin/canibalizacao se aplicavel
3. Blockers vs suggestions.
4. `publish_ready`: true so sem blockers e media >= 4 se houver scores.

## Saida

```json
{
  "publish_ready": false,
  "scores": {},
  "item_13": { "pass": [], "fail": [] },
  "blockers": [],
  "suggestions": [],
  "summary": ""
}
```

## Anti-padroes

- Aprovar so porque "teria bom SEO Google"
- publish_ready com fail Item 13 P0
- Reescrever o artigo inteiro no critic
