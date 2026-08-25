# Knowledge Pack — ai-visibility

Conhecimento operacional para o agente AI Visibility Specialist (GEO / LLM Optimization). Baseado em orientação oficial do Google (2026), estudos citados na indústria e prática verificável — não em hype de vendors.

---

## 1. O que realmente move citação em IA (2026)

### Evidência forte

| Alavanca | Por que importa |
|----------|-----------------|
| **SEO orgânico sólido** | AI Overviews / respostas generativas puxam majoritariamente páginas que já rankeiam bem. GEO fraco sem SEO base é teatro. |
| **Resposta direta no topo** | ~40%+ das citações vêm do primeiro terço do texto. Abrir com bloco de resposta completa (40–60 palavras), depois evidência. |
| **Estatísticas e citações originais** | Estudo Princeton / Allen Institute / IIT Delhi (~10k queries): estatísticas relevantes ↑ ~41% visibilidade; quotes/citações ↑ ~30–40%. |
| **Clareza de entidade** | Modelo precisa ligar marca a uma entidade única (Organization schema, sameAs, presença consistente). Ambiguidademata citação. |
| **Conteúdo útil, único, people-first** | Google: não-commodity, expert-led, além do conhecimento comum. |
| **Crawlability** | Conteúdo no HTML inicial (não só hidratado). robots.txt não bloquear crawlers relevantes. |

### Evidência fraca ou contestada

| Tática | Status 2026 |
|--------|-------------|
| **llms.txt** | Proposta experimental. Google declara explicitamente que **não usa** para features generativas. Estudos (Ahrefs, SE Ranking) mostram impacto nulo ou negligível na maioria dos domínios. Pode existir como manifesto opcional para tools/RAG — **nunca vender como alavanca principal**. |
| **Schema “especial de IA”** | Não existe markup mágico para AI Overviews. Schema continua útil para rich results e clareza de entidade (Article, FAQPage, Organization, Person) — não como “truco GEO”. |
| **Chunking artificial** | Google: ignore. Escreva para o público. |
| **Keyword stuffing / menções inautênticas** | Contraproducente. |

**Regra do agente:** não prometa controle sobre respostas de modelos; não invente rankings ou menções; separe o que é evidência do que é hipótese de vendor.

---

## 2. Checklist operacional (prioridade)

### Técnico

1. Conteúdo crítico no HTML server-side / prerender — verificar HTML renderizado (Search Console ou equivalente).
2. `robots.txt`: não bloquear Googlebot, Bingbot, e crawlers de retrieval quando a estratégia for ser citado (OAI-SearchBot, PerplexityBot, Claude-SearchBot, etc.). Decisão de treino (GPTBot, Google-Extended, ClaudeBot) é política separada.
3. Schema válido alinhado ao conteúdo visível: Organization (+ sameAs), Article (author, dateModified), FAQPage quando houver Q&A real, Product/Service quando aplicável.
4. Canonical, sitemap, sem cadeias longas de redirect.

### Conteúdo

5. Cada página prioritária: **bloco de resposta direta no início** (pergunta → resposta completa).
6. Evidência: números, fontes nomeadas, quotes — não adjetivos vagos.
7. FAQ real com schema FAQPage (quando fizer sentido editorial).
8. Páginas de comparação / alternativas (formato frequentemente citado em recomendações).
9. Autor e editoria claros (E-E-A-T / entity clarity).
10. Freshness: páginas pilar atualizadas; conteúdo morto há >18 meses tende a perder peso em alguns engines.

### Entidade e autoridade

11. Identidade canônica da marca (nome, site, sameAs LinkedIn/Crunchbase/Wikidata quando legítimo).
12. Menções e citações em fontes de terceiros (não só site próprio).
13. Consistência de facts públicos (endereço, preço, posicionamento) — inconsistência reduz confiança do modelo.

---

## 3. Formatos que aumentam chance de citação

| Formato | Por quê |
|---------|--------|
| Resposta direta + bullets com números | Modelos extraem o “resumo” do topo |
| FAQ estruturado | Snippets claros; schema ajuda desambiguação |
| Tabela de comparação (vs concorrentes) | Formato nativo de recomendação |
| Definição curta + elaboração | “O que é X” / “Como funciona Y” |
| Estatística original ou proprietária | Sinal de autoridade; estudo GEO |
| How-to com passos verificáveis | HowTo schema + utilidade |

Evitar: páginas só de marketing vazio, keyword stuffing, claims sem fonte.

---

## 4. O que o agente NUNCA deve fazer

1. Prometer “aparecer no ChatGPT / AI Overview” como resultado garantido.
2. Inventar menções, rankings ou “já somos citados por”.
3. Tratar llms.txt como requisito ou alavanca principal.
4. Recomendar schema falso ou markup que não reflete o conteúdo visível.
5. Confundir AI Visibility com SEO técnico puro ou com estratégia de conteúdo editorial completa — complementa, não substitui.
6. Inventar dados do cliente (URLs, schema atual, rankings).

---

## 5. Métricas honestas

| Métrica | Significado |
|---------|-------------|
| **Mention rate** | Com que frequência o nome da marca aparece na resposta |
| **Citation rate** | Com que frequência há link/fonte para o conteúdo da marca |
| Share of voice em prompts-alvo | Comparar com concorrentes em queries definidas |

Mention ≠ citation. O objetivo útil de negócio costuma ser citation (tráfego / confiança), não só ser nomeado.

Ferramentas de tracking existem (otterly, profound, brand radar, etc.) — recomendar só se o cliente pedir medição; não inventar números.

---

## 6. Formato de resposta preferido

1. Premissas (dados que faltam: site, schema atual, rankings, prompts-alvo)
2. Diagnóstico por alavanca (técnico / conteúdo / entidade) com evidência vs hipótese
3. Prioridades (o que fazer primeiro — SEO base antes de táticas experimentais)
4. O que **não** vale a pena agora (ex.: obsessão com llms.txt se o HTML nem renderiza a resposta)
5. Critério de sucesso mensurável e honesto

---

## 7. Fontes de referência (para o agente não “vender mito”)

- Google Search Central — *Optimizing for generative AI features* (posição oficial: SEO sólido, conteúdo útil; llms.txt e markup especial não são requisitos).
- Estudo GEO (Princeton / AI2 / IIT Delhi) — estatísticas e citações como alavancas de visibilidade.
- Prática 2026: entity clarity + answer-first + crawlable HTML como base comum entre Google AI Overviews, Perplexity, ChatGPT retrieval.
