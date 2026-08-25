# Knowledge Packs

Conhecimento operacional injetável nos agentes horizontais do setup de marketing.

**Prompt** define comportamento.  
**Knowledge pack** define fatos, checklists e anti-padrões.  
**Client context** (brief, brand, dados) é injetado por pedido.

---

## Packs disponíveis

| Arquivo | Agente / uso | Conteúdo principal |
|---------|--------------|---------------------|
| [ui.md](./ui.md) | `ui` | Tokens (3 camadas), pipeline Figma→código, estados, a11y UI |
| [ux.md](./ux.md) | `ux` | Jornadas, fricção, priorização, a11y de fluxo |
| [ai-visibility.md](./ai-visibility.md) | `ai-visibility` | GEO/AEO baseado em evidência 2026, o que funciona vs mito |
| [seo-specialist.md](./seo-specialist.md) | `seo-specialist` | Intent-first, on-page, técnico mínimo, E-E-A-T |
| [copywriter.md](./copywriter.md) | `copywriter` | Proof, clareza, especificidade, anti-hype, QA por formato |
| [imported-from-harnesses.md](./imported-from-harnesses.md) | orquestração / rede | Regras de Ruflo, Hermes, Orca, evidência, SKILL.md |

---

## Como montar um teste real

```text
[SYSTEM]
{system prompt do agente em docs/marketing-agency-agents.md}

[KNOWLEDGE]
{conteúdo do knowledge pack correspondente}

[CLIENT]
- Marca / produto
- Objetivo do pedido
- Dados disponíveis (site, brand kit, tokens, métricas, screenshots…)
- Restrições

[TASK]
Pedido concreto e verificável
```

### Critério de “pronto para uso”

- Responde com base no knowledge + client, não só em generalidades
- Declara premissas quando falta dado
- Não inventa métricas, tokens, rankings ou resultados
- Respeita os limites do system prompt

---

## Próximos packs sugeridos

1. **Item 13 fecho** — playbook AI-findability + `geo-agent` pack + piloto num site real
2. `diretor-arte` — coerência de campanha, brief visual
3. `marketing-orquestrador` — decomposição com regras R1–R5 importadas
4. `content-strategist` / `social-media-manager`

---

Setup paralelo — não altera o agent-network-mcp de produção.
