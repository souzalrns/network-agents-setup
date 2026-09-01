# Conclusão — Setup Marketing Agents

Documentação de sistema da agência multi-agente (horizontais + verticais + orquestrador + knowledge packs).

## Entregáveis documentais

| Entregável | Path |
|------------|------|
| Portfolio | [PORTFOLIO.md](./PORTFOLIO.md) |
| One-pager | [ONE-PAGER-MARKETING-AGENTS.md](./ONE-PAGER-MARKETING-AGENTS.md) |
| System prompts + limites | [marketing-agency-agents.md](./marketing-agency-agents.md) |
| Playbook Item 13 (AI Findability) | [item-13-ai-findability.md](./item-13-ai-findability.md) (canónico) + [knowledge/item-13-ai-findability.md](./knowledge/item-13-ai-findability.md) |
| Knowledge packs | [knowledge/](./knowledge/) |
| Playbook orquestrador | [knowledge/orquestrador-playbook.md](./knowledge/orquestrador-playbook.md) |

## Padrão de invocação

```text
[SYSTEM]   docs/marketing-agency-agents.md  (papel)
[KNOWLEDGE]  docs/knowledge/<agente>.md  (+ item-13 se discoverability)
[CLIENT]   brief / vertical-client-context
[TASK]     pedido concreto
```

## Estado

- Documentação de sistema: **completa** para portfolio e testes de prompt.
- Runtime de produção: **fora** deste repo (`agent-network-mcp`).
- Piloto Item 13 num site live: precisa de URLs/dados reais e implementação no domínio canónico.

## Próximos passos (opcional)

1. **Piloto Item 13** — 5–15 URLs de um projeto real (ex. ViannaLegal lab vs domínio) contra o playbook canónico.
2. Wiring de skills / MCP no runtime sem sobrescrever o setup documental.
3. Vertical por cliente com `vertical-client-context.md` preenchido.

## Item 13 — resumo

Playbook canónico com P0/P1/P2 PASS/FAIL, política de bots (search/answer Allow; train Disallow por defeito), anti-padrões e handoffs:
`ai-visibility` (lead) ← `seo-specialist` ← `copywriter`/`content-strategist` ← `critic-criativo`, com `geo-agent` só se intent local.

*LRNSdigital*
