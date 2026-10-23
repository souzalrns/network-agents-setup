---
name: post_trade_review
description: "Lê o JSON do `economia-trader review` e escreve a revisão pós-trade da semana: processo avaliado à parte do resultado, resultado em R e em dinheiro, custos e um achado repetível por trade. Não reinterpreta os números nem recomenda ordens."
action: post_trade_review
version: 1
vertical: trading
priority: P1
---

# Skill — post_trade_review

## Quando usar

- Passo `action: post_trade_review`, com o output do `economia-trader review` em `repo_files` ou nos `inputs`.

## Não usar

- Recalcular métricas de memória: os números vêm do JSON da ferramenta.
- Propor ordens ou mudar limites (isso é `risk_review` + decisão humana).

## Grounding

- O método está em `docs/knowledge/trading/post-trade-review-method.md`.
- Cada número citado vem do JSON, copiado tal como está (texto decimal), com o campo de origem.
- Sem JSON → falha controlada: dizer que não há revisão para ler.

## Processo

1. Ler o JSON: `trades[]`, `weeks{}`, `open[]`, `orphan_sells`.
2. Por trade: grau do processo e quebras (com a etapa), resultado em R e em dinheiro, custos, o achado.
3. Por semana: fechados, taxa de acerto, expectativa em R, maior perda, taxas sobre o bruto, quebra mais frequente.
4. Uma conclusão: o achado repetível mais importante da semana (processo antes de resultado).

## Saída

Markdown em `output_artifact`:

```markdown
# Revisão pós-trade — <semana>

## Resumo da semana
| Métrica | Valor | Campo do JSON |
## Trades
| Símbolo | Processo | Resultado (R / dinheiro) | Custos | Achado |
## Achado da semana
## Abertos e anomalias (open, orphan_sells)
```

## done_when

- [ ] Todos os números com o campo do JSON de origem
- [ ] Processo descrito antes do resultado em cada trade
- [ ] Um achado da semana, repetível
- [ ] Nenhuma recomendação de ordem

## Anti-padrões

- Chamar "bom" a um trade ganhador com `major break`
- Adjectivos no lugar de números
