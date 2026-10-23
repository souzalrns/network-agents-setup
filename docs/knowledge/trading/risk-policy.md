# Trading — política de risco e escada de execução (F6)

Fonte: `oss/economia-trader` (README §"The ladder", §"Risk limits are explicit"; `src/economia_trader/risk.py`). Este pack descreve o que a ferramenta **já impõe**; os agentes de trading analisam e preparam, nunca executam.

## Escada de execução

| Degrau | O que acontece | O que o desbloqueia |
|---|---|---|
| **paper** | Execuções simuladas contra preços públicos reais, com taxas e slippage conservadores | Omissão |
| **testnet** | Ordens na testnet da Bybit (fundos de teste) ou na conta paper da Alpaca | `ECONOMIA_TRADER_ALLOW_TESTNET=1` + chaves de testnet |
| **live** | Ordens reais | `ECONOMIA_TRADER_LIVE=I_ACCEPT_REAL_LOSSES` **e** `check-key` a passar (trade sim, levantamento **não**) **e** um humano aprova *aquela* ordem |

Cada degrau exige o anterior. O kill switch (`economia-trader kill` ou `ECONOMIA_TRADER_KILL=1`) e qualquer regra de risco que falhe param todos os degraus.

**Regra do setup:** dinheiro real está bloqueado. Nenhum agente deste domínio propõe passar para `live`; isso é decisão do maestro, fora do runner.

## Limites de risco explícitos

Não há valores por omissão para dinheiro: um ficheiro de limites sem `max_order_notional`, `max_loss_per_trade`, `max_daily_loss` ou `allowed_symbols` é recusado.

- **`max_order_notional`** — valor máximo de uma ordem, na moeda de cotação (ex.: USDT).
- **`max_loss_per_trade`** — perda máxima no stop de um trade, **incluindo as taxas dos 2 lados**. Não pode ser maior do que o `max_daily_loss`.
- **`max_daily_loss`** — depois de atingido, só passam saídas.
- **`max_open_positions`** — por omissão 1.
- **`max_total_exposure`** — por omissão `max_order_notional × max_open_positions`.
- **`allowed_symbols`** — lista fechada; `["*"]` só como opção explícita.
- **`fee_rate`** — por lado, por omissão 0,1%; entra no cálculo da perda no stop.
- **`max_price_deviation`** — um preço limite pode estar no máximo 2% do preço de referência.

Uma compra sem stop-loss é recusada. A perda no stop tem de caber no `max_loss_per_trade` **e** no que resta do `max_daily_loss` do dia.

## Âmbito da v0.1

Só spot, só posições longas, sem alavancagem. Fora: futuros, margem, short, opções. Na MEXC spot o stop fica do lado do cliente (o venue não tem stop no exchange) e o journal regista-o (`stop_client_side`).

## Como um agente usa isto

- Uma análise de mercado que sugira uma entrada tem de dizer o stop e a perda estimada no stop em R e em dinheiro, e verificar se cabe nos limites.
- Uma revisão de risco recusa (marca como bloqueio) qualquer proposta sem stop, fora de `allowed_symbols`, ou cuja perda no stop não caiba nos limites.
- Nada disto é aconselhamento financeiro: trading pode perder todo o capital investido.
