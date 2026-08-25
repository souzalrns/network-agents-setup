# Knowledge Packs

Conhecimento operacional injetável nos agentes horizontais do setup de marketing.

**Prompt** define comportamento.  
**Knowledge pack** define fatos, checklists e anti-padrões.  
**Client context** (brief, brand, dados) é injetado por pedido.

---

## Packs disponíveis

| Arquivo | Agente / uso | Conteúdo principal |
|---------|--------------|---------------------|
| [ui.md](./ui.md) | `ui` | Tokens, pipeline, estados, a11y UI |
| [ux.md](./ux.md) | `ux` | Jornadas, fricção, a11y de fluxo |
| [ai-visibility.md](./ai-visibility.md) | `ai-visibility` | GEO/AEO evidência 2026 |
| [seo-specialist.md](./seo-specialist.md) | `seo-specialist` | Intent-first, on-page, técnico |
| [copywriter.md](./copywriter.md) | `copywriter` | Proof, clareza, QA por formato |
| [geo-agent.md](./geo-agent.md) | `geo-agent` | NAP, intent local, anti-spam de cidades |
| [item-13-ai-findability.md](./item-13-ai-findability.md) | **Item 13** | Playbook completo AI findability |
| [imported-from-harnesses.md](./imported-from-harnesses.md) | orquestração | Ruflo, Hermes, Orca, evidência |

---

## Item 13 — estado

| Peça | Status |
|------|--------|
| Agente `ai-visibility` + pack | Feito |
| Playbook de implementação | Feito (`item-13-ai-findability.md`) |
| Pack `geo-agent` | Feito |
| Piloto num site real | **Pendente** (fase 3 — ex. ViannaLegal) |

---

## Como montar um teste real

```text
[SYSTEM]
{system prompt do agente em docs/marketing-agency-agents.md}

[KNOWLEDGE]
{pack correspondente e/ou item-13-ai-findability.md}

[CLIENT]
- Marca / produto / URLs
- Dados disponíveis
- Restrições

[TASK]
Pedido concreto e verificável
```

---

Setup paralelo — não altera o agent-network-mcp de produção.
