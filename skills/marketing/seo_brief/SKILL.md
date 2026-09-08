---
name: seo_brief
action: seo_brief
version: 1
vertical: marketing
priority: P0
item_13: true
---

# Skill — seo_brief

## Quando usar

- Step `action: seo_brief` (templates `seo_article`, `landing_copy`, `full_content_piece`).

## Não usar

- Escrever o artigo completo (→ `copy_answer_first`).
- Auditoria técnica de URL live (→ `seo_tech_audit`).

## Inputs

- Research artefact se `depends_on` incluir research
- Objective, audience, constraints do plan
- Knowledge Item 13: `docs/item-13-ai-findability.md`, `docs/knowledge/ai-findability.md` se existirem

## Tools

Respeitar `tools_allowed` (ex. `read_repo_file`, `web_search`).

## Processo

1. Definir **primary intent** (informational / commercial / navigational).
2. Primary query + 3–8 secondary queries.
3. Outline H1/H2 alinhado à intent (answer-first).
4. Bloco **Item 13** (obrigatório):
   - entidades nomeadas
   - perguntas FAQ (3–5) que a peça deve responder de forma citável
   - o que um sistema de IA deve conseguir extrair/recomendar
   - riscos de thin/canibalização se conhecidos
5. Unique promise (o que esta URL oferece que genéricos não).
6. Schema sugerido (FAQPage, Article, …) se aplicável.

## Saída

Preferir JSON alinhado a schema `SeoBrief` quando o plan o exigir.

Campos mínimos:

```json
{
  "primary_intent": "",
  "primary_query": "",
  "secondary_queries": [],
  "outline": [],
  "unique_promise": "",
  "item_13": {
    "entities": [],
    "faq": [],
    "ai_extractable_claims": [],
    "structure_notes": "",
    "risks": []
  },
  "suggested_schema": [],
  "sources_to_cite": []
}
```

## done_when

- [ ] primary_query + intent preenchidos
- [ ] outline com H1 implícito/explícito
- [ ] `item_13` com FAQ ≥ 3 ou risks a explicar porque não
- [ ] unique_promise não vazio

## Anti-padrões

- Outline genérico "Introdução / Desenvolvimento / Conclusão" sem intent
- Item 13 omitido
- Keyword stuffing como estratégia
- Brief que já é o artigo completo
