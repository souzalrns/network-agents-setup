# Conclusão — Setup Marketing Agents

Documentação de sistema da agência multi-agente (horizontais + verticais + orquestrador + knowledge packs).

## Entregáveis documentais

| Entregável | Path |
|------------|------|
| Portfolio | [PORTFOLIO.md](./PORTFOLIO.md) |
| One-pager | [ONE-PAGER-MARKETING-AGENTS.md](./ONE-PAGER-MARKETING-AGENTS.md) |
| System prompts | [marketing-agency-agents.md](./marketing-agency-agents.md) |
| Playbook Item 13 | [item-13-ai-findability.md](./item-13-ai-findability.md) |
| **T6 Ingest RAG** | [T6-INGEST-PIPELINE.md](./T6-INGEST-PIPELINE.md) |
| Knowledge packs | [knowledge/](./knowledge/) |
| Ficha cliente | [knowledge/vertical-client-context.md](./knowledge/vertical-client-context.md) |

## Padrão de invocação

```text
[SYSTEM]    marketing-agency-agents.md
[KNOWLEDGE] knowledge/<agente>.md (+ item-13 se discoverability)
[CLIENT]    vertical-client-context
[TASK]      pedido
```

## Estado

- Knowledge packs horizontais + verticais + Item 13: **documentados**
- Ownership rede Item 13: tech P0 + marketing P1 + skills (playbook §11)
- **T6 pipeline:** especificado — implementação na rede (CI + Supabase)
- Runtime MCP: repo separado

## Próximos passos

1. Implementar T6 na rede (dry-run → CI)
2. Piloto CLIENT real
3. Piloto Item 13 site live (lab vs canónico)

## Ownership Item 13 (rede)

`produto-tech-transversal` (P0) + `marketing` (P1) + skills searchfit-seo / content / brand-review. Sem agent novo obrigatório.

*LRNSdigital*
