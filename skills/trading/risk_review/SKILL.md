---
name: risk_review
description: "Verifica uma proposta de trade ou um ficheiro de limites contra a política de risco do economia-trader (stop obrigatório, perda no stop dentro dos limites, símbolos permitidos, sem alavancagem) e lista os bloqueios. Não aprova ordens: prepara a decisão humana."
action: risk_review
version: 1
vertical: trading
priority: P1
---

# Skill — risk_review

## Quando usar

- Passo `action: risk_review` antes de uma decisão humana sobre uma proposta ou sobre limites de risco.

## Não usar

- Executar, aprovar ou enviar ordens.
- Mudar os limites: só aponta o que está fora deles.

## Grounding

- A política está em `docs/knowledge/trading/risk-policy.md` (em `repo_files`). Não usar limites de memória.
- A proposta e os limites vêm dos `inputs` ou de `repo_files` do passo; se faltarem, é lacuna.

## Processo

1. Ler a política de risco e a proposta (ou o ficheiro de limites).
2. Verificar, um a um: stop presente; perda no stop (com taxas dos 2 lados) ≤ `max_loss_per_trade` e ≤ o que resta do `max_daily_loss`; símbolo em `allowed_symbols`; notional ≤ `max_order_notional`; spot, longo, sem alavancagem; modo ≠ `live`.
3. Classificar cada ponto: `ok`, `bloqueio` ou `lacuna` (dado em falta).

## Saída

Markdown em `output_artifact`:

```markdown
# Revisão de risco

## Proposta (como recebida)
## Verificações
| Regra | Resultado (ok/bloqueio/lacuna) | Evidência |
## Bloqueios
## Lacunas
## Para a decisão humana
```

## done_when

- [ ] Todas as regras da política verificadas, cada uma com evidência
- [ ] Nenhuma aprovação implícita: a decisão é do humano no gate
- [ ] Modo `live` assinalado como bloqueio

## Anti-padrões

- "Aprovado" sem gate humano
- Arredondar a perda no stop para caber no limite
