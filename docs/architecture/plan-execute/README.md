# Plan-Execute (setup)

Padrão: **Planner** gera plano explícito → **Executor** corre passos com tools limitadas → **Verify** (checklist / critic) → humano nos gates.

| Ficheiro | Uso |
|----------|-----|
| `plan.schema.md` | Contrato documental dos campos |
| `schemas/Plan.schema.json` | Validação formal do plano (`depends_on` obrigatório) |
| `schemas/SeoBrief.schema.json` | Output passo SEO |
| `schemas/CopyAnswerFirst.schema.json` | Output passo copy |
| `schemas/CriticReport.schema.json` | Output passo critic |
| `examples/piloto-netos.plan.yaml` | Exemplo preenchido (hub netos) |
| `../../pilots/piloto-seo-copy-001/` | Artefactos já executados (manual) |

## Quando usar

- Fluxos previsíveis: SEO → Copy → Critic
- Precisam de auditoria antes de agir
- Model tiering (plano forte, execução barata)

## Quando não usar

- Exploração pura (preferir ReAct no passo)
- Um único call sem tools

## Produção

Este diretório é **setup / documentação**. Não liga sozinho ao `agent-network-mcp`.
