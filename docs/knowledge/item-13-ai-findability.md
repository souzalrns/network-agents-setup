> **Playbook canónico (P0/P1/P2, robots, handoffs, template):** [../item-13-ai-findability.md](../item-13-ai-findability.md)  
> Em conflito de regras operacionais, **prevalece o playbook canónico**. Este ficheiro é contexto RAG para agents.

# Knowledge — Item 13 AI Findability

**Lead agent:** `ai-visibility`  
**Base técnica:** `seo-specialist`  
**Conteúdo:** `copywriter`, `content-strategist`  
**Local (opcional):** `geo-agent`  
**Validação:** `critic-criativo`  
**Disparo:** `marketing-orquestrador`

## Quando usar

- “Ser encontrado / citado / recomendado por IA”
- Auditoria de discoverability
- Site SPA ou HTML fraco
- Preparar cutover SSG/SSR
- Revisar llms.txt, schema, answer-first, entidade

## Saída esperada (ai-visibility)

1. Lista de URLs prioritárias (máx. 5–15 no piloto)
2. Tabela PASS/FAIL por URL (template do playbook §9)
3. Gaps P0 vs P1 vs P2
4. Política de bots aplicada (default ou override do cliente)
5. Lab vs domínio canónico explicitado
6. Próximas 3 acções ordenadas

## Regras operacionais (resumo)

| Camada | Regra |
|--------|--------|
| P0 | HTML texto no 1.º response; title/desc/canonical por URL; 1 H1; 404 real; schema coerente |
| P1 descoberta | Sitemap só canónicas; robots sem contradição; llms.txt alinhado |
| Bots default | Allow search/answer; Disallow GPTBot + Google-Extended (override só com decisão registada) |
| Edge | Cloudflare/WAF não pode contradizer robots do repo sem nota → FAIL |
| P1 conteúdo | Answer-first; factos extraíveis; unique_promise; 1 URL/intent; fundir thin |
| P1 entidade | Organization + Person; sameAs reais; datas; YMYL disclaimer se aplicável |
| P2 | GSC páginas/queries; inspeção URL; PASS lab ≠ PASS canónico |

## Anti-padrões (memória curta)

SPA `#root` vazio · canonical → home · posts thin em massa · FAQPage sem FAQ · preview `.vercel.app` como marca · claims inventados · robots Allow+Disallow no mesmo UA · soft-404

## Exemplo de referência (só doc)

- Lab Next SSG (ex. ViannaLegal ht7m) ≈ P0 alinhado  
- Produção SPA (ex. viannalegal.com.br shell) ≈ FAIL P0 até HTML real no domínio canónico  

## O que não fazer

- Prometer “vais aparecer no ChatGPT”
- Inventar métricas, menções ou rankings
- Substituir o `seo-specialist` em arquitectura técnica profunda
- Criar 20 páginas cidade-clone (geo)
- Declarar PASS no domínio canónico só porque o lab passou

## Handoff mínimo

```text
orquestrador → seo-specialist (P0)
             → ai-visibility (lead Item 13)
             → geo-agent? (só local)
             → copywriter / content-strategist
             → critic-criativo (PASS/FAIL)
```
