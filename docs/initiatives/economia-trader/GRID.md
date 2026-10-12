# economia-trader: grid spot limitado (cripto)

> Decisões do maestro (2026-10-12, perguntas sim/não):
> - **P-75 = A:** grid spot limitado para cripto, primeiro no backtest contra comprar e manter e contra o
>   `sma_cross`, depois em paper.
> - **P-76 = B:** sem grid em ações/ETFs por agora.
> - **P-77 = B:** sem os grids nativos da Bybit.
>
> PENDENCIAS §10.

## Porquê

O lado cripto não tinha estratégia autónoma: o loop `run` só gera ideias de ações (fluxo de opções, insiders SEC). O
grid dá-lhe uma, para mercados laterais, sem sair do nosso controlo: cada ordem passa pelo motor de risco, pelo gate,
pelo kill switch e pelo diário. Um robô de grid na própria exchange não passaria por nada disso.

## Como funciona

- **Faixa:** `[lower, upper]`, dada em absoluto ou em `range_pct` à volta do primeiro preço visto. A âncora fica fixa
  e é guardada no estado; não persegue o preço.
- **Níveis:** `levels` degraus, geométricos por omissão.
- **Compra:** o lote `i` compra-se quando o preço desce ao nível `L_i`, e só o nível **imediatamente acima** do
  preço. Nunca se compra um nível longe do preço nem abaixo da faixa.
- **Venda:** cada lote vende-se no nível seguinte, `L_{i+1}`.
- **Uma acção por tick, vendas primeiro.** Ordens rejeitadas pelo risco desfazem-se na reconciliação seguinte.
- **Teto:** no máximo `max_lots` lotes de `order_notional` cada.
- **Stop único** abaixo da faixa (`lower × (1 − stop_pct)`): o stop do trader vende tudo de uma vez.
- **Auto-kill** num drawdown de `max_drawdown_pct` a partir do pico (paper).

## Fail-closed contra os limites

Antes do primeiro tick, `GridConfig.problems(limits)` recusa o grid se, no pior caso:
- um lote perder mais do que `max_loss_per_trade` até ao stop;
- um stop-out completo (todos os lotes no mesmo dia) passar o `max_daily_loss`;
- o inventário completo passar o teto de exposição;
- um degrau não pagar as comissões de ida e volta;
- o par não estiver em `allowed_symbols`.

Um grid recusado não negoceia (`grid_refused` no diário).

O exemplo (`examples/grid.example.json`) cabe em `examples/limits.example.json`: BTCUSDT, faixa de ±6 % (7 níveis
a ~2 %), stop 3 % abaixo da faixa, até 4 lotes de 8 USDT. O pior caso fica abaixo de 5 USDT.

## Ordem de uso (P-75)

1. **Backtest com três colunas:**

   ```bash
   economia-trader backtest --exchange bybit --symbol BTCUSDT --interval 1h --limit 1000 \
     --limits examples/limits.example.json --strategy grid --grid-config examples/grid.example.json --cash 100
   ```

   Sai `grid`, `sma_cross` e `buy_and_hold`, com `comparacao` (retorno, drawdown, trades). Um grid relativo
   ancora na primeira vela (sem look-ahead), decide no fecho e executa na abertura seguinte.

2. **Paper**, só se o grid ganhar no backtest em retorno ajustado ao drawdown, em mais de um período:

   ```bash
   economia-trader grid --exchange bybit --config grid.json --limits limits.json --once   # cron, p. ex. de hora a hora
   ```

   O estado fica em `.economia-trader/grid/` e o painel (`dashboard --state-dir .economia-trader/grid`) mostra os
   níveis e os lotes em carteira.

3. **Testnet e real** seguem a escada de sempre (`ALLOW_TESTNET`, `check-key`, mandato P-57, aprovação por ordem).

## O que esperar

O grid ganha o spread entre níveis enquanto o preço oscila dentro da faixa. Perde numa queda forte: o stop limita
essa perda ao valor validado acima. Numa subida forte vende tudo cedo e fica de fora, e perde para comprar e manter.
O backtest mostra estes três cenários lado a lado.

## Limites desta versão

- Os stops vivem no cliente (como no resto do v0.1). Em testnet e em real, as posições ficam registadas localmente
  pela ordem aceite e não pelo fill da exchange: é a mesma lacuna de reconciliação antes do real.
- Um par por processo (corre um processo por par).
