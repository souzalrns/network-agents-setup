# Portfolio — Rede Multi-Agente de Marketing

**Projeto:** estrutura de agentes para agência de marketing, publicidade, redes sociais e produção audiovisual  
**Tipo:** desenho de sistema + prompts + knowledge packs (setup documental)  
**Repo:** [network-agents-setup](https://github.com/souzalrns/network-agents-setup)  
**Estado:** documentação completa · runtime de produção separado (`agent-network-mcp`)

---

## Problema

Equipas e ferramentas de IA misturam papéis: o mesmo prompt tenta fazer SEO, copy, UI e mídia paga. Resultado típico:

- sobreposição e contradicção entre “especialistas”
- respostas genéricas sem conhecimento operacional
- claims inventados (métricas, depoimentos, rankings)
- zero preparação para **descoberta por IA** (o futuro das buscas)

## Solução

Uma **agência multi-agente** com:

1. **Horizontais** — especialistas reutilizáveis (UX, UI, SEO, AI Visibility, copy, mídia, etc.)
2. **Verticais** — frente por cliente (Instagram, TikTok, tráfego, calendário…)
3. **Orquestrador** — decompõe objetivos e faz handoffs; não substitui o especialista
4. **Knowledge packs** — factos, checklists e anti-padrões por papel (não só system prompt)
5. **Item 13 — AI Findability** — playbook para estruturar projetos para IA encontrar e recomendar

```text
                    ┌──────────────────┐
                    │  Objetivo de negócio   │
                    └─────────│─────────┘
                             │
                    ┌────────▼────────┐
                    │  marketing-orquestrador │
                    └────────│────────┘
          ┌──────────────┼─────────────┐
          │              │              │
   ┌───▼───┐   ┌───▼───┐   ┌───▼───┐
   │Horizontais│   │ Verticais │   │ Qualidade │
   │ SEO AI UI  │   │ IG TikTok │   │ critic    │
   │ copy media │   │ paid AV   │   │ brand-guard│
   └──────────┘   └──────────┘   └──────────┘
          │              │
          └─── [KNOWLEDGE packs + ficha CLIENTE] ───┘
```

---

## O que entrega (evidência no repo)

| Camada | Conteúdo |
|--------|----------|
| **Papéis** | ~19 horizontais + verticais de cliente, com **limites** anti-sobreposição |
| **Conhecimento** | Pack operacional por especialista (checklists, fronteiras, formato de resposta) |
| **Discoverability** | Playbook Item 13: projetos estruturados para IA encontrar e recomendar |
| **Skills** | Mapa designer-skills / ECC → agente + prioridades P0/P1 |
| **Harnesses** | Regras portáteis de Ruflo, Hermes, Orca (evidência, isolamento, SKILL.md) — sem adotar o runtime inteiro |
| **Cliente** | Template de ficha para verticais (NAP, prova, canais, claims proibidos) |

### Padrão de invocação (teste real)

```text
[SYSTEM]     system prompt do agente
[KNOWLEDGE]  knowledge pack correspondente
[CLIENT]     ficha do cliente
[TASK]       pedido concreto e verificável
```

---

## Diferenciais de desenho

1. **Prompt ≠ conhecimento** — comportamento separado de factos e anti-padrões  
2. **Menor número de agentes útil** — orquestrador justifica fast-path vs full cycle  
3. **Evidência antes de “pronto”** — proibição explícita de inventar métricas/provas  
4. **SEO + AI Visibility + GEO local** — três papéis distintos, um playbook integrado (Item 13)  
5. **UI ≠ Diretor de Arte** — design system / tokens vs campanha / Canva  
6. **Setup paralelo** — documentação isolada da rede de produção (sem misturar maturidade)

---

## Mapa rápido de agentes

| Função | Exemplos |
|--------|----------|
| Estratégia | marketing-orquestrador, estrategista-marca |
| Inteligência | research, trend-hunter, seo, ai-visibility, geo, performance |
| Criação | copy, storytelling, diretor-arte, ui, ux, editor-video, ugc |
| Distribuição | social-media-manager, media-buyer, influencer, content-strategist |
| Qualidade | critic-criativo, brand-guard |
| Operação cliente | Instagram, TikTok, tráfego, AV, TikTok Shop, calendário |

Documento completo: [marketing-agency-agents.md](./marketing-agency-agents.md)

---

## Navegação no repo

| Documento | Uso |
|-----------|-----|
| [ONE-PAGER-MARKETING-AGENTS.md](./ONE-PAGER-MARKETING-AGENTS.md) | Resumo 1 página |
| [marketing-agency-agents.md](./marketing-agency-agents.md) | Prompts + limites |
| [knowledge/](./knowledge/) | Packs por agente |
| [knowledge/item-13-ai-findability.md](./knowledge/item-13-ai-findability.md) | AI Findability |
| [knowledge/skills-map.md](./knowledge/skills-map.md) | Skills → agentes |
| [CONCLUSAO-SETUP-MARKETING.md](./CONCLUSAO-SETUP-MARKETING.md) | Fecho e próximos passos |

---

## Honestidade de maturidade

| Feito | Ainda não (fase seguinte) |
|-------|---------------------------|
| Desenho, prompts, knowledge, playbooks | Piloto live com evidência de campo |
| Mapa de skills | Wiring automático no runtime |
| Regras de harnesses | Adotar Ruflo/Hermes/Orca como produto |
| Setup paralelo documentado | Portar agentes para `agent-network-mcp` de produção |

---

## One-liner

> Arquitetura multi-agente de marketing com papéis limitados, knowledge packs operacionais e playbook para marcas serem encontradas e recomendadas por sistemas de IA — pronta para testes reais, com fronteira clara face à produção.

*LRNSdigital / network-agents-setup · documentação 2026*
