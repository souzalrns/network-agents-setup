# Item 13 — AI Findability (playbook operacional)

**Repo:** `network-agents-setup` · **Knowledge RAG:** [knowledge/item-13-ai-findability.md](./knowledge/item-13-ai-findability.md)  
**Lead:** `ai-visibility` · **Base técnica:** `seo-specialist` · **Conteúdo:** `copywriter` / `content-strategist` · **Local (opcional):** `geo-agent` · **Validação:** `critic-criativo` · **Disparo:** `marketing-orquestrador`

**Objectivo:** estruturar sites e páginas para motores de busca e sistemas de IA **encontrarem, compreenderem, citarem e recomendarem** a marca — sem prometer controlo sobre o modelo.

---

## 1. Definição e 8 pilares

**Item 13 — AI Findability:** conjunto de regras técnicas, de conteúdo e de entidade para maximizar a probabilidade de a marca ser recuperada e citada por Google, AI Overviews, Perplexity, ChatGPT Search e equivalentes.

| # | Pilar |
|---|--------|
| 1 | HTML real no 1.º response (SSG/SSR; evitar SPA opaca) |
| 2 | Uma URL canónica por intenção (anti-canibalização / anti-thin) |
| 3 | Answer-first + factos extraíveis (tabelas, listas, FAQ visível) |
| 4 | Entidade / E-E-A-T (Organization, Person, sameAs, autoria, datas) |
| 5 | Schema JSON-LD alinhado ao conteúdo visível |
| 6 | Descoberta deliberada: sitemap, robots, llms.txt sem contradições |
| 7 | Medição (GSC, inspeção de URL, lab vs domínio canónico) |
| 8 | Handoffs multi-agente com PASS/FAIL explícito |

---

## 2. P0 técnico (bloqueantes) — checklist PASS/FAIL

| # | Item | PASS | FAIL | Como verificar |
|---|------|------|------|----------------|
| P0.1 | HTML com texto no 1.º response | Corpo legível sem JS; size tipicamente ≫ 10 KB em páginas de conteúdo | `#root` vazio, shell ~5–8 KB, texto só após hidratação | `curl -sL URL | head` / View Source |
| P0.2 | Title único por URL | `<title>` distinto e descritivo | Ausente, genérico ou igual em todas as rotas | curl + grep title |
| P0.3 | Meta description por URL | Description própria | Ausente ou herdada da home em todas as rotas | curl |
| P0.4 | Canonical autorreferente | `rel=canonical` = URL canónica dessa página | Tudo aponta para a home; canonical ausente | curl |
| P0.5 | 1 H1 | Exactamente um H1 com texto principal | 0 H1, H1 vazio, ou vários H1 competindo | curl / DOM estático |
| P0.6 | 404 real | URL inventada → HTTP 404 | Soft-404: 200 + `index.html` SPA | `curl -sI URL_FALSA` |
| P0.7 | Schema coerente | JSON-LD no HTML; `@type` reflecte o visível; FAQPage só com FAQ visível | Schema sem conteúdo; FAQ fantasma; zero LD em páginas de serviço | grep `ld+json` + Rich Results Test |

**Regra:** qualquer FAIL em P0.1–P0.6 → Item 13 **não passa** nessa URL, independentemente do copy.

---

## 3. P1 descoberta

### 3.1 Sitemap
- Só URLs **canónicas** que se quer indexar
- Sem previews, sem parâmetros de tracking, sem duplicados
- `lastmod` honesto quando possível
- **PASS:** cada `<loc>` devolve 200 e é a canónica da página  
- **FAIL:** sitemap com 100 URLs e HTML idêntico / soft-404

### 3.2 robots.txt — política de bots (default do playbook)

| Classe | User-agents (exemplos) | Default |
|--------|------------------------|---------|
| Pesquisa clássica | Googlebot, Bingbot | **Allow** |
| Answer / search IA | OAI-SearchBot, PerplexityBot, ClaudeBot, ChatGPT-User (consulta) | **Allow** |
| Treino de modelos | GPTBot, Google-Extended | **Disallow** por defeito |
| Scrapers agressivos | Bytespider e afins (conforme política do cliente) | **Disallow** recomendado |

**Regras não negociáveis sem decisão registada do cliente:**
1. **PROIBIDO** Allow e Disallow contraditórios para o **mesmo** user-agent no mesmo ficheiro (ou blocos Cloudflare vs repo em conflito sem nota).
2. Cliente pode optar por **Allow** em GPTBot / Google-Extended; essa opção fica **documentada** (issue, PR ou `CLIENT` brief).
3. **`llms.txt` alinhado** à mesma política (nunca incentivar treino se robots bloqueia treino, e vice-versa, sem nota explícita).
4. **Cloudflare / WAF / Managed Rules:** não podem bloquear na edge o que o `robots.txt` do repo permite **sem decisão explícita**. Divergência edge vs repo = **FAIL** de descoberta.

#### robots.txt de referência (default)

```txt
# Item 13 default — search/answer Allow; train Disallow
User-agent: *
Allow: /

User-agent: GPTBot
Disallow: /

User-agent: Google-Extended
Disallow: /

User-agent: Bytespider
Disallow: /

# Answer/search — explícito (opcional mas claro)
User-agent: OAI-SearchBot
Allow: /

User-agent: PerplexityBot
Allow: /

User-agent: ClaudeBot
Allow: /

Sitemap: https://www.example.com/sitemap.xml
```

#### llms.txt de referência (esqueleto)

```txt
# Marca — one-liner do posicionamento
> Frase factual: quem, o quê, para quem, onde.

## Sobre
Factos verificáveis (entidade, credenciais, geografia).

## URLs prioritárias
- https://www.example.com/servico-principal
- https://www.example.com/sobre

## Política
Conteúdo para consulta e citação. Treino de modelos: ver robots.txt (default: não autorizado via GPTBot/Google-Extended).
```

---

## 4. P1 conteúdo

| Regra | PASS | FAIL |
|-------|------|------|
| Answer-first | Resposta útil nos primeiros ~2 parágrafos / bloco inicial | Hero só slogan sem factos |
| Factos extraíveis | Tabelas, listas, FAQ visível | Muro de prosa sem estrutura |
| unique_promise | Cada URL tem ângulo/promessa distinta | 10 páginas com o mesmo outline |
| 1 URL / intenção | Uma canónica por intent head | 5 “guias netos 2025/2026” a competir |
| Thin / locais | Fundir ou não publicar | 8 posts “cidadania em [cidade]” quase iguais |
| Clusters | Pilar + spokes com links internos | Posts isolados sem hub |

---

## 5. P1 entidade / E-E-A-T

- **Organization** (e/ou LocalBusiness): `name`, `url`, `sameAs` reais
- **Person** (autor / profissional): nome, credenciais, ligação à org
- Autoria visível em YMYL; data de publicação / revisão
- Disclaimers quando o tema for jurídico, saúde, financeiro (SST / legal)
- **FAIL:** claims de volume/sucesso sem base; sameAs inventados; autor genérico “Admin”

---

## 6. P2 medição

| Sinal | Onde | Nota |
|-------|------|------|
| Indexação | GSC → Páginas | Indexadas vs excluídas (canónica, soft-404, noindex) |
| Queries / impressões | GSC → Desempenho | Por URL e por query |
| Canónica escolhida | Inspeção de URL | Google deve ver a canónica que declaraste |
| Lab vs canónico | Preview vs domínio oficial | **“Passou Item 13 no lab” ≠ passou no domínio público** |

**Definição operacional:**
- **PASS lab:** P0+P1 cumpridos no ambiente de preview (ex. `*.vercel.app` com SSG).
- **PASS domínio canónico:** mesmos critérios em `https://cliente.com` **e** GSC sem falhas graves de canónica/soft-404 na superfície prioritária.

---

## 7. Anti-padrões (sintoma observável)

| Anti-padrão | Sintoma |
|-------------|---------| 
| SPA opaca | `#root` vazio; curl sem H1/texto |
| Canonical tudo → home | Todas as rotas com `canonical` da homepage |
| Dezenas de posts thin | Sitemap inchado; GSC com poucas indexadas |
| Schema fantasma | FAQPage sem FAQ no HTML |
| Preview como marca | `.vercel.app` indexado e promovido como site oficial |
| Claims inventados | “98% sucesso” sem fonte |
| robots contraditório | Allow e Disallow ao mesmo UA; CF bloqueia o que o repo permite |
| Soft-404 | URL falsa → 200 |

**Exemplo de referência (não implementar neste repo):**  
- Lab ViannaLegal (`viannalegal-site-ht7m.vercel.app`, Next SSG) ≈ P0 técnico alinhado ao Item 13.  
- Produção `viannalegal.com.br` (SPA shell) ≈ anti-padrão P0 até cutover para HTML real.

---

## 8. Handoff multi-agente

**Trigger (orquestrador):** “Item 13”, “AI Findability”, “aparecer em IA”, “site ilegível para bots”, auditoria de discoverability.

| Ordem | Agent | Papel | Entrega |
|-------|--------|------|---------|
| 1 | `marketing-orquestrador` | Dispara, define URLs prioritárias, não substitui especialistas | Plano + ordem de handoff |
| 2 | `seo-specialist` | P0 técnico + sitemap/canonical/404 | Checklist P0 PASS/FAIL por URL |
| 3 | `ai-visibility` | Lead Item 13: entidade, llms.txt, citabilidade, gaps | Relatório findability + prioridades |
| 4 | `geo-agent` | **Só** se intent local real | Pacote local ou “fora de scope” |
| 5 | `copywriter` / `content-strategist` | Answer-first, FAQ, unique_promise | Textos com prova; sem claims inventados |
| 6 | `critic-criativo` | Valida coerência e anti-padrões | PASS/FAIL final + bloqueios |

**Critérios para o orquestrador fechar o fluxo:**
- Todas as URLs prioritárias com P0 PASS **ou** lista explícita de FAIL com dono
- Política de bots registada (default ou override do cliente)
- Diferença lab vs domínio canónico explicitada

**Limites:** nenhum agent inventa credenciais, avaliações ou números; `geo-agent` não cria 20 páginas cidade-clone; preview não se promove como canónico.

---

## 9. Template rápido de auditoria (por URL)

```text
URL:
P0.1 HTML texto: PASS/FAIL
P0.2 Title único: PASS/FAIL
P0.3 Description: PASS/FAIL
P0.4 Canonical: PASS/FAIL
P0.5 H1: PASS/FAIL
P0.6 404 site: PASS/FAIL (uma vez por propriedade)
P0.7 Schema: PASS/FAIL/NA
P1 answer-first: PASS/FAIL
P1 unique_promise: PASS/FAIL
Notas:
```

---

## 10. Dependências de decisão do cliente

| Tema | Default playbook | Override |
|------|------------------|----------|
| GPTBot / Google-Extended | Disallow | Cliente pode Allow (registar) |
| Lista exacta de bots answer | OAI-SearchBot, PerplexityBot, ClaudeBot + equivalentes | Expandir/reduzir |
| Cloudflare vs robots | Devem coincidir | Se CF bloquear, documentar e tratar como FAIL até alinhar |
| Domínio canónico vs preview | Só domínio oficial é “PASS canónico” | — |

---

*LRNSdigital · network-agents-setup · Item 13*
