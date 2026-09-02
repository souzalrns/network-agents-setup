> **Playbook canónico:** [../item-13-ai-findability.md](../item-13-ai-findability.md) — prevalece em conflito.

# Knowledge — Item 13 AI Findability

**Lead (setup):** `ai-visibility`  
**P0 setup:** `seo-specialist` · **Rede P0:** `produto-tech-transversal`  
**P1 rede:** `marketing`  
**Validação:** `critic-criativo`

## Quando usar

Ser encontrado/citado por IA · auditoria discoverability · SPA/HTML fraco · cutover SSG · llms.txt/schema/answer-first.

## Saída esperada

1. 5–15 URLs prioritárias  
2. PASS/FAIL por URL (playbook §9)  
3. Gaps P0/P1/P2  
4. Política de bots  
5. Lab vs canónico  
6. Próximas 3 acções  

## Regras (resumo)

P0: HTML real, title/desc/canonical, H1, 404, schema.  
P1: sitemap, robots, answer-first, unique_promise, entidade.  
Bots: Allow search/answer; Disallow GPTBot/Google-Extended (default).  
PASS lab ≠ PASS canónico.

## Anti-padrões

SPA vazia · canonical→home · thin · FAQ fantasma · preview como marca · claims inventados · soft-404.

## Rede de produção

**Não** assumir agent `ai-visibility` na rede. Ownership: **produto-tech-transversal** (P0) + **marketing** (conteúdo) + skills `searchfit-seo:*`, content, brand-review. Detalhe: playbook §11.

## Handoff

```text
orquestrador → produto-tech / seo (P0)
             → marketing / ai-visibility lead (P1)
             → critic (PASS/FAIL)
```
