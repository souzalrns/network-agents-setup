---
name: seo_brief
action: seo_brief
version: 2
vertical: marketing
priority: P0
item_13: true
---

# Skill — seo_brief

## Quando usar

- Step `action: seo_brief` (templates `seo_article`, `landing_copy`, `full_content_piece`).

## Nao usar

- Escrever o artigo completo (→ `copy_answer_first`).
- Auditoria tecnica de URL live (→ `seo_tech_audit`).

## Alvo de descoberta (obrigatorio ler)

O brief **nao** e so "para o Google". Item 13 cobre **multi-IA**, incluindo de forma nao exclusiva:

- Assistentes: **ChatGPT, Claude, Gemini, Copilot**, …
- Resposta com fontes: **Perplexity** e similares
- AI search / overviews (Google e outros)
- Qualquer RAG/agent que recupere a peca

SEO classico (intent, queries, outline) **permanece**; o bloco **item_13** e para **citabilidade e recomendacao por sistemas generativos**, nao so rankings SERP.

Ver: `docs/knowledge/marketing/multi-ai-findability.md`.

## Inputs

- Research artefact se `depends_on` incluir research
- Objective, audience, constraints do plan
- Knowledge Item 13 + multi-ai-findability

## Tools

Respeitar `tools_allowed`.

## Processo

1. **Primary intent** (informational / commercial / navigational).
2. Primary query + 3–8 secondary (linguagem natural como utilizadores perguntam a **assistentes e** a motores).
3. Outline H1/H2 answer-first.
4. Bloco **Item 13** (obrigatorio):
   - entidades nomeadas
   - FAQ 3–5 **citaveis** (pergunta como se fosse feita a um assistente)
   - `ai_extractable_claims`: frases que GPT/Claude/Gemini/etc. possam reutilizar com fidelidade
   - `structure_notes`: o que ajuda extracão multi-modelo (nao so snippet Google)
   - riscos thin/canibalizacao / claims de "garantia de citacao"
5. Unique promise.
6. Schema sugerido (FAQPage, Article, …) se aplicavel.

## Saida (minimo)

```json
{
  "primary_intent": "",
  "primary_query": "",
  "secondary_queries": [],
  "outline": [],
  "unique_promise": "",
  "discovery_targets": ["assistants", "ai_search", "classic_serp"],
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

`discovery_targets` default: incluir assistants + ai_search; `classic_serp` se tambem houver objectivo de ranking tradicional.

## done_when

- [ ] primary_query + intent
- [ ] outline com resposta cedo
- [ ] item_13 com FAQ >= 3 ou risks a explicar
- [ ] unique_promise
- [ ] linguagem do brief **nao** reduz Item 13 a "so Google" (salvo objective explicitamente SERP-only)

## Anti-padroes

- Tratar Item 13 como sinonimo de ranking Google
- "Garantir aparecer no ChatGPT/Claude"
- Outline generico sem intent
- Item 13 omitido
- Keyword stuffing
- Brief = artigo completo
