# Item 13 — AI Findability (playbook operacional)

**Repo:** `network-agents-setup` · **Knowledge RAG:** [knowledge/item-13-ai-findability.md](./knowledge/item-13-ai-findability.md)  
**Lead (setup):** `ai-visibility` · **Base técnica:** `seo-specialist` · **Conteúdo:** `copywriter` / `content-strategist` · **Local (opcional):** `geo-agent` · **Validação:** `critic-criativo` · **Disparo:** `marketing-orquestrador`

**Objectivo:** estruturar sites e páginas para motores de busca e sistemas de IA **encontrarem, compreenderem, citarem e recomendarem** a marca — sem prometer controlo sobre o modelo.

---

## 1. Definição e 8 pilares

**Item 13 — AI Findability:** regras técnicas, de conteúdo e de entidade para maximizar a probabilidade de a marca ser recuperada e citada por Google, AI Overviews, Perplexity, ChatGPT Search e equivalentes.

| # | Pilar |
|---|--------|
| 1 | HTML real no 1.º response (SSG/SSR; evitar SPA opaca) |
| 2 | Uma URL canónica por intenção (anti-canibalização / anti-thin) |
| 3 | Answer-first + factos extraíveis |
| 4 | Entidade / E-E-A-T |
| 5 | Schema JSON-LD alinhado ao visível |
| 6 | Sitemap, robots, llms.txt sem contradições |
| 7 | Medição (GSC; lab vs canónico) |
| 8 | Handoffs multi-agente com PASS/FAIL |

---

## 2. P0 técnico (bloqueantes) — PASS/FAIL

| # | Item | PASS | FAIL |
|---|------|------|------|
| P0.1 | HTML texto no 1.º response | Corpo legível sem JS | Shell SPA vazio |
| P0.2 | Title único | Title distinto | Genérico ou repetido |
| P0.3 | Meta description | Própria | Ausente ou da home |
| P0.4 | Canonical | Autorreferente | Tudo → home |
| P0.5 | 1 H1 | Um H1 com texto principal | 0 ou vários competindo |
| P0.6 | 404 real | URL falsa → 404 | Soft-404 200 |
| P0.7 | Schema coerente | LD alinhado ao visível | FAQ fantasma |

**Regra:** FAIL em P0.1–P0.6 → Item 13 **não passa** nessa URL.

---

## 3. P1 descoberta

### 3.1 Sitemap
Só canónicas a indexar; 200; sem preview/duplicados.

### 3.2 robots.txt — default

| Classe | Exemplos | Default |
|--------|----------|--------|
| Pesquisa | Googlebot, Bingbot | **Allow** |
| Answer/search IA | OAI-SearchBot, PerplexityBot, ClaudeBot | **Allow** |
| Treino | GPTBot, Google-Extended | **Disallow** |

**PROIBIDO** Allow e Disallow contraditórios no mesmo UA. Cloudflare não pode bloquear o que o repo permite sem decisão. `llms.txt` alinhado.

```txt
User-agent: *
Allow: /

User-agent: GPTBot
Disallow: /

User-agent: Google-Extended
Disallow: /

User-agent: OAI-SearchBot
Allow: /

User-agent: PerplexityBot
Allow: /

User-agent: ClaudeBot
Allow: /

Sitemap: https://www.example.com/sitemap.xml
```

---

## 4. P1 conteúdo

Answer-first · factos extraíveis · unique_promise · 1 URL/intent · fundir thin · clusters com links.

---

## 5. P1 entidade / E-E-A-T

Organization/Person · sameAs reais · autoria/datas YMYL · sem claims inventados.

---

## 6. P2 medição

GSC páginas/queries · inspeção de URL · **PASS lab ≠ PASS domínio canónico**.

---

## 7. Anti-padrões

SPA opaca · canonical→home · thin em massa · schema fantasma · preview como marca · claims inventados · robots contraditório · soft-404.

---

## 8. Handoff (setup documental)

| Ordem | Agent | Papel |
|-------|--------|------|
| 1 | marketing-orquestrador | Dispara, URLs prioritárias |
| 2 | seo-specialist | P0 técnico |
| 3 | ai-visibility | Lead citabilidade / gaps |
| 4 | geo-agent | Só intent local |
| 5 | copy / content-strategist | Answer-first, unique_promise |
| 6 | critic-criativo | PASS/FAIL final |

---

## 9. Template auditoria (por URL)

```text
URL:
P0.1 HTML texto: PASS/FAIL
P0.2 Title: PASS/FAIL
P0.3 Description: PASS/FAIL
P0.4 Canonical: PASS/FAIL
P0.5 H1: PASS/FAIL
P0.6 404: PASS/FAIL
P0.7 Schema: PASS/FAIL/NA
P1 answer-first: PASS/FAIL
P1 unique_promise: PASS/FAIL
Notas:
```

---

## 10. Decisões do cliente

| Tema | Default | Override |
|------|---------|----------|
| GPTBot / Google-Extended | Disallow | Cliente pode Allow (registar) |
| Bots answer | OAI-SearchBot, PerplexityBot, ClaudeBot | Expandir/reduzir |
| Cloudflare vs robots | Coincidir | Divergência = FAIL até alinhar |
| Canónico vs preview | Só domínio oficial | — |

---

## 11. Rede de produção vs setup documental

O setup define papéis de **desenho** (`ai-visibility`, `seo-specialist`, `geo-agent`, …).

Na **rede de produção** esses IDs podem **não existir**. Levantamento real: sem agent `ai-visibility` / `geo-agent` nomeados.

| Papel no setup | Dono na rede (default) |
|----------------|------------------------|
| Lead Item 13 / P1 conteúdo | `marketing` |
| P0 técnico | `produto-tech-transversal` |
| Ferramentas novas | `radar-ferramentas` |
| Orquestração | orquestrador da rede (P0 FAIL bloqueia P1) |

**Não criar** agent `ai-findability` só para espelhar o setup, salvo volume que justifique. Preferir **tech (P0) + marketing (conteúdo) + skills**.

### 11.1 Mapa pilar → skill

| Pilar | Skill |
|-------|--------|
| P0 técnico | `searchfit-seo:technical-seo`, `seo-audit`, `seo-check` |
| Schema | `searchfit-seo:schema-markup`, `generate-schema` |
| GEO/AEO | `searchfit-seo:ai-visibility` |
| Anti-canibalização | `searchfit-seo:keyword-clustering` |
| Answer-first / on-page | `on-page-seo`, `content-brief`, `create-content` |
| Links / soft-404 | `internal-linking`, `broken-links` |
| Multilingue | `content-translation` |
| Anti-claims | `marketing:brand-review` |

Playbook = PASS/FAIL e ordem. Skills = execução. Agent = interpretação sem inventar métricas.

### 11.2 Ingestão (pipeline, não one-shot)

1. Hash por ficheiro  
2. Re-ingest só do que mudou  
3. Purga de chunks órfãos  
4. Disparo no merge (CI)  
5. `ingest_knowledge` + estado Supabase  

Sem pipeline → chunks stale (já observado na rede).

### 11.3 Regra de ouro

- **Setup** = o *quê* (critérios).  
- **Rede** = *quem* + *skill*.  
- Nomes diferentes **não** invalidam o playbook.

---

*LRNSdigital · network-agents-setup · Item 13 · ownership rede §11*
