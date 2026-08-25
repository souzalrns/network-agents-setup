# Item 13 — Playbook: AI Findability

**Objetivo:** estruturar projetos (sites, páginas, entidades de marca) para sistemas de IA **encontrarem, compreenderem e citarem/recomendarem** com mais probabilidade — sem prometer controlo sobre o modelo.

**Agentes envolvidos:** `ai-visibility` (lead) + `seo-specialist` (base) + `geo-agent` (quando intent local) + `copywriter` / `content-strategist` (conteúdo answer-first).

**Knowledge de apoio:** `ai-visibility.md`, `seo-specialist.md`, `geo-agent.md`.

---

## 1. Princípios não negociáveis

1. **SEO sólido é a entrada** — AI Overviews e retrieval puxam sobretudo páginas já rastreáveis e relevantes.
2. **Resposta no topo** — bloco direto (40–60 palavras) antes do storytelling longo.
3. **Entidade clara** — uma identidade canónica de marca (nome, URL, sameAs, factos consistentes).
4. **Evidência** — estatísticas, fontes, experiência real; não adjetivos vazios.
5. **HTML legível** — conteúdo crítico no HTML inicial quando possível (muitos crawlers de IA não correm JS).
6. **Honestidade** — não prometer “vais aparecer no ChatGPT”; medir o que for mensurável.
7. **llms.txt é opcional** — não é alavanca principal (Google não o usa para generative features).

---

## 2. Checklist por projeto (ordem de execução)

### Fase A — Fundação técnica (seo-specialist + dev)

- [ ] HTTPS em todo o site
- [ ] robots.txt: páginas importantes não bloqueadas; decisão explícita sobre bots de treino vs retrieval
- [ ] Sitemap atualizado com a superfície pública real
- [ ] Canonicals corretos; sem cadeias longas de redirect
- [ ] Conteúdo prioritário presente no HTML renderizado (verificar, não assumir)
- [ ] Core Web Vitals em faixa aceitável no campo (não só lab)

### Fase B — Entidade de marca (ai-visibility)

- [ ] Nome canónico da marca / produto (uma grafia principal)
- [ ] Organization (ou LocalBusiness) schema com `url`, `name`, `sameAs` (LinkedIn, etc. quando reais)
- [ ] Página About / contacto com factos verificáveis
- [ ] Factos públicos consistentes (morada, preços de referência, posicionamento) — sem contradições entre páginas
- [ ] Autor identificável em conteúdo YMYL ou editorial forte

### Fase C — Páginas prioritárias AI-ready (conteúdo)

Para cada URL prioritária (máx. 5–10 no piloto):

- [ ] **Intent única** clara (informational / commercial / transactional / local)
- [ ] **Answer block** no início (pergunta implícita → resposta completa)
- [ ] Evidência: números, fontes nomeadas, ou experiência first-hand
- [ ] Hierarquia H1/H2 legível; listas/tabelas quando compararem opções
- [ ] FAQ real + FAQPage schema **só se** o FAQ estiver visível na página
- [ ] Article/Service/Product schema alinhado ao tipo de página
- [ ] `dateModified` atualizado quando houver mudança substantiva

### Fase D — Formatos que IAs citam com mais frequência

- [ ] Página de definição / “o que é” do serviço principal
- [ ] Comparação ou alternativas (quando o mercado permitir e for honesto)
- [ ] FAQ das dúvidas reais do cliente (não keyword stuffing)
- [ ] How-to com passos verificáveis (se for o caso de uso)
- [ ] Dados proprietários ou estatísticas próprias quando existirem

### Fase E — Local (se aplicável — geo-agent)

- [ ] NAP (nome, morada, telefone) consistente em site e perfis
- [ ] LocalBusiness / área de serviço explícita
- [ ] Conteúdo com intenção local real (cidade/região), não spam de keywords de cidade
- [ ] Perfis Google Business / equivalentes alinhados aos factos do site

### Fase F — Opcional / experimental

- [ ] `llms.txt` como **mapa** das melhores URLs (não como substituto de HTML/SEO)
- [ ] Tracking de mention/citation em prompts-alvo (ferramenta à escolha do cliente) — baseline antes de “melhorar”

---

## 3. Template mínimo de página AI-ready

```text
[H1] Título alinhado à intent

[Answer block — 40–60 palavras]
Resposta direta à pergunta principal da página.

[Evidência]
- Facto ou número + fonte/contexto
- Facto ou número + fonte/contexto

[Desenvolvimento]
Secções H2 com uma ideia cada. Tabelas se for comparação.

[FAQ] (opcional)
Perguntas reais + respostas curtas. Schema FAQPage só se visível.

[Entidade / CTA]
Quem é a organização + próximo passo claro se intent comercial.
```

---

## 4. Fluxo de agentes (item 13)

```text
Objetivo: "estruturar [projeto] para IA encontrar e recomendar"

1. marketing-orquestrador / planejador
   → critério de pronto + lista de URLs prioritárias

2. seo-specialist
   → Fase A + intent por URL + bloqueadores técnicos

3. ai-visibility
   → Fase B + C + D (diagnóstico + prioridades; sem inventar rankings)

4. geo-agent (se local)
   → Fase E

5. copywriter / content-strategist
   → reescrever answer blocks e FAQs com prova disponível

6. Verificação
   → HTML, schema validator, lista do que mudou, o que medir a seguir
```

Não spawnar todos se o site for pequeno: seo + ai-visibility bastam no piloto.

---

## 5. Critério de “item 13 fechado” num projeto

| Critério | Evidência |
|----------|----------|
| Fundação técnica sem bloqueador óbvio | Checklist A com itens verificados |
| Entidade documentada | Schema Organization/LocalBusiness + factos consistentes |
| ≥ 3 URLs prioritárias com answer-first + prova | Diff ou lista de páginas |
| Schema só onde o conteúdo existe | Rich Results / validator sem erro grave |
| Decisões experimentais rotuladas | llms.txt / tracking como opcional, não como “magia” |
| Métricas honestas definidas | Ex.: queries-alvo, indexação, mention rate se houver tool — **sem baseline inventada** |

---

## 6. Anti-padrões (falhar o item 13)

- Tratar llms.txt como trabalho principal
- Schema sem conteúdo correspondente
- Keyword stuffing de cidades / “melhor X 2026” vazio
- Prometer citação em ChatGPT / Perplexity / AI Overview
- Inventar FAQ, estatísticas ou sameAs
- Otimizar copy antes de corrigir noindex / JS-only content / canonical errado

---

## 7. Piloto sugerido (quando for a fase 3)

**Candidato forte:** ViannaLegal (já tem FAQ schema, sitemap, trabalho de SEO/AEO documentado no agente de produção).

Passos do piloto:
1. Inventário de 5 URLs prioritárias
2. Correr Fases A–D (e E se local)
3. Registar gaps vs checklist
4. Implementar só o top 5 de impacto
5. Definir medição em 30 dias (GSC + opcional citation tool)

---

*Item 13 — playbook de fecho. Setup paralelo / knowledge.*
