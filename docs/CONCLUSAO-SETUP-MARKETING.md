# Conclusão — Setup paralelo Agência de Marketing

**Repo:** `network-agents-setup`  
**Data de fecho documental:** 2026-08-25  
**Scope:** prompts + knowledge packs + mapas — **não** altera `agent-network-mcp` de produção.

---

## 1. O que ficou pronto

| Entrega | Local |
|---------|--------|
| System prompts horizontais + verticais | [docs/marketing-agency-agents.md](./marketing-agency-agents.md) |
| Knowledge packs de **todos** os horizontais de marketing | [docs/knowledge/](./knowledge/) |
| Playbook Item 13 (AI Findability) | [knowledge/item-13-ai-findability.md](./knowledge/item-13-ai-findability.md) |
| Regras Ruflo / Hermes / Orca | [knowledge/imported-from-harnesses.md](./knowledge/imported-from-harnesses.md) |
| Mapa skill → agente | [knowledge/skills-map.md](./knowledge/skills-map.md) |
| Template contexto de cliente (verticais) | [knowledge/vertical-client-context.md](./knowledge/vertical-client-context.md) |
| Índice knowledge | [knowledge/README.md](./knowledge/README.md) |

### Horizontais com prompt + knowledge

ui, ux, diretor-arte, storytelling, geo-agent, ai-visibility, seo-specialist, copywriter, social-media-manager, media-buyer, performance-analyst, editor-video, influencer-strategist, ugc-specialist, trend-hunter, research-marketing, critic-criativo, content-strategist, marketing-orquestrador

### Verticais

Prompts prontos; conhecimento = **ficha de cliente** (template acima), não pack genérico.

---

## 2. Como usar em teste real

```text
[SYSTEM]     prompt em marketing-agency-agents.md
[KNOWLEDGE]  docs/knowledge/<agente>.md  (+ item-13 se discoverability)
[CLIENT]     ficha vertical-client-context.md preenchida
[TASK]       pedido concreto e verificável
```

Critério de qualidade: evidência do pack/cliente, premissas explícitas, zero métricas/provas inventadas.

---

## 3. O que deliberadamente ficou de fora (próxima fase)

| Item | Porquê |
|------|--------|
| Ligação runtime no **agent-network-mcp** | Produção separada; este setup é paralelo |
| Piloto Item 13 num site live | Precisa de URLs/dados reais e implementação |
| Skills executáveis auto-carregadas | Mapa feito; wiring é engenharia de produto |
| Adotar Ruflo/Hermes/Orca como produto | Só regras importadas |

---

## 4. Próximos passos recomendados (ordem)

1. **Piloto Item 13** — 5 URLs de um projeto real (ex. ViannaLegal) contra o playbook  
2. **Preencher 1 ficha de cliente** e testar orquestrador + 2 horizontais  
3. **P0 skills** (design-token, a11y, seo) no ambiente onde forem correr agentes  
4. Só depois: portar agentes escolhidos para `agent-network-mcp` se fizer sentido de produção  

---

## 5. Declaração de conclusão

O **desenho documental** da agência de marketing multi-agente (papéis, limites, conhecimento robusto, item 13, skills map, contexto de cliente) está **concluído** neste repo.

A **operação em produção** e o **piloto com evidência de campo** são fases seguintes, não bloqueadores deste fecho documental.

---

*Setup paralelo LRNSdigital / network-agents-setup.*
