# Conclusão — Setup Marketing Agents

Documentação de sistema da agência multi-agente (horizontais + verticais + orquestrador + knowledge packs).

## Entregáveis documentais

| Entregável | Path |
|------------|------|
| Portfolio | [PORTFOLIO.md](./PORTFOLIO.md) |
| One-pager | [ONE-PAGER-MARKETING-AGENTS.md](./ONE-PAGER-MARKETING-AGENTS.md) |
| System prompts + limites | [marketing-agency-agents.md](./marketing-agency-agents.md) |
| Playbook Item 13 | [item-13-ai-findability.md](./item-13-ai-findability.md) + [knowledge/ai-findability.md](./knowledge/ai-findability.md) |
| Knowledge packs | [knowledge/](./knowledge/) |
| Playbook orquestrador | [knowledge/orquestrador-playbook.md](./knowledge/orquestrador-playbook.md) |
| Ficha cliente (verticais) | [knowledge/vertical-client-context.md](./knowledge/vertical-client-context.md) |

## Padrão de invocação

```text
[SYSTEM]    docs/marketing-agency-agents.md  (papel)
[KNOWLEDGE] docs/knowledge/<agente>.md  (+ item-13 / ai-findability se discoverability)
[CLIENT]    vertical-client-context preenchido
[TASK]      pedido concreto
```

## Estado

- **Knowledge packs:** horizontais + verticais + Item 13 reforçados.
- **System prompts:** links Knowledge por papel em `marketing-agency-agents.md`.
- **Documentação de sistema:** completa para portfolio e testes de prompt.
- **Runtime de produção:** fora deste repo (`agent-network-mcp`).

## Knowledge (pós-reforço)

| Camada | Estado |
|--------|--------|
| Item 13 | Playbook + RAG chunks + ownership |
| Horizontais | Packs operacionais completos |
| Verticais | Packs por papel + template CLIENT |
| Runtime MCP | Repo separado |

## Próximos passos (opcional)

1. Piloto com **ficha CLIENT real** (não mais packs genéricos vazios).
2. Piloto Item 13 em site live (lab vs domínio canónico).
3. Wiring de skills / MCP no runtime sem sobrescrever este setup.

## Item 13 — resumo

`ai-visibility` (lead) ← `seo-specialist` (P0) ← copy/content ← `critic-criativo`; `geo-agent` só se local.
Política de bots default: Allow search/answer; Disallow GPTBot e Google-Extended.

*LRNSdigital*
