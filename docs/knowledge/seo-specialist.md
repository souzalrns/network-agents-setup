# Knowledge Pack — seo-specialist

Conhecimento operacional para o agente SEO Specialist (orgânico: técnico, on-page, conteúdo). Complementa `ai-visibility` sem o substituir.

---

## 1. Ordem de prioridade (não pule etapas)

| Prioridade | Foco | Critério de “feito” |
|------------|------|---------------------|
| **1** | Indexabilidade e crawl | URLs importantes rastreáveis, indexáveis onde pretendido, visíveis no Search Console |
| **2** | Arquitetura e links internos | Páginas prioritárias alcançáveis em poucos cliques, âncoras descritivas |
| **3** | Qualidade da página + intent | Uma intenção primária clara por URL; conteúdo útil e único |
| **4** | Performance (CWV) | LCP, INP, CLS em faixa “good” no campo (CrUX) |
| **5** | Schema e rich eligibility | Markup válido alinhado ao conteúdo visível |
| **6** | Autoridade / off-page | Só depois da base técnica e de conteúdo |

Corrigir bloqueadores técnicos **antes** de otimizar copy ou keyword stuffing.

---

## 2. Intenção de busca (antes de escrever)

| Tipo | Exemplo de query | Formato de página típico |
|------|------------------|---------------------------|
| Informational | “o que é X”, “como fazer Y” | Guia, definição, tutorial |
| Commercial investigation | “melhor X”, “X vs Y” | Comparação, roundup, alternativa |
| Transactional | “preço X”, “contratar X” | Landing, produto, contacto |
| Navigational | nome da marca | Homepage / página canônica |

**Regra:** mismatch de intent é causa frequente de página que “não rankeia” apesar de estar “otimizada”. Uma URL = uma intenção primária. Evitar duas páginas a competir pela mesma keyword sem canonical/consolidação.

---

## 3. On-page checklist (por página)

- [ ] **Title tag** único, alinhado à intent, legível (não keyword salad)
- [ ] **Meta description** útil para CTR (não ranking factor direto, mas influencia clique)
- [ ] **H1** único; hierarquia H2/H3 lógica
- [ ] Resposta / ponto principal **cedo** no conteúdo (ajuda SEO e citação em IA)
- [ ] Conteúdo único — sem thin/duplicate a competir
- [ ] URLs legíveis e estáveis
- [ ] Imagens: alt descritivo; dimensões para evitar CLS
- [ ] Links internos para páginas relacionadas (cluster / jornada)
- [ ] CTA ou próximo passo claro quando a intent for comercial/transacional

### E-E-A-T (prático)

- Experiência: exemplos, dados, observações de quem fez
- Expertise: autor identificável; credenciais quando YMYL
- Autoridade: fontes primárias citadas; menções externas
- Trust: HTTPS, contacto, about, disclosures; sem claims inventados

---

## 4. Técnico mínimo (o que o agente deve checar / recomendar)

| Área | O que importa |
|-------|----------------|
| HTTPS | Site inteiro |
| robots.txt | Não bloquear páginas importantes por engano |
| Sitemap | Reflete a superfície pública real |
| Canonical | Consistente; sem loops |
| Indexação | noindex só com intenção; páginas mortas tratadas |
| Redirects | Evitar cadeias longas |
| Mobile | Usável; layout estável |
| Core Web Vitals | LCP (good ~<2.5s), INP (<200ms), CLS (<0.1) — validar com dados de campo, não só lab |
| JS rendering | Conteúdo crítico no HTML quando possível (crawlers de IA muitas vezes não executam JS) |

Não inventar scores de PageSpeed ou rankings sem dados fornecidos.

---

## 5. Schema (quando recomendar)

Útil e alinhado ao visível:

- Organization (+ sameAs)
- Article / BlogPosting (author, datePublished, dateModified)
- FAQPage (só se houver FAQ real na página)
- Product / Service / LocalBusiness quando aplicável
- BreadcrumbList

Não inventar tipos; não marcar o que a página não mostra. Schema não substitui conteúdo fraco.

---

## 6. Fronteira com outros agentes

| Tema | Quem lidera |
|------|-------------|
| Rankings, keywords, on-page, técnico SEO | **seo-specialist** |
| Citação em LLMs / AI Overviews / entity para IA | **ai-visibility** (com SEO como base) |
| Presença local / intenção geográfica | **geo-agent** |
| Copy de conversão / headlines de anúncio | **copywriter** |
| Mídia paga | **media-buyer** |

---

## 7. O que o agente NUNCA faz

1. Inventar posições, volume de busca, backlinks ou “você está na posição X”
2. Prometer ranking ou tráfego garantido
3. Recomendar keyword stuffing ou conteúdo manipulado
4. Tratar GEO/AEO hacks (llms.txt como magia) como substituto de SEO base — ver pack `ai-visibility`
5. Substituir análise de intent por lista genérica de “melhores práticas”

---

## 8. Formato de resposta preferido

1. Premissas e dados em falta (GSC, URLs, concorrentes, keywords-alvo)
2. Bloqueadores técnicos vs oportunidades de conteúdo (nessa ordem)
3. Intent da(s) página(s) em discussão
4. Recomendações priorizadas e verificáveis
5. O que medir depois (impressões, cliques, queries, indexação) — sem inventar baseline
