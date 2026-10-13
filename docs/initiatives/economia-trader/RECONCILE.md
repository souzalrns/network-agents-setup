# economia-trader: fills reais, stops na exchange e drawdown real

> Pedido do maestro (2026-10-13, passo 2 de 3): fechar as lacunas antes do dinheiro real. Era o que bloqueava o
> mandato P-57.

## Antes e depois (testnet/real)

| Lacuna | Antes (v0.1) | Agora |
|---|---|---|
| Fills | a ordem aceite ficava registada como executada, ao preço avaliado | regista-se **o que a exchange diz** (`fetch_order` / `get_order_by_id`): quantidade e preço médio reais, incluindo fills parciais |
| Stops | só no cliente (o trader tinha de estar a correr) | **uma ordem de stop na exchange** para a posição inteira. Em Bybit spot é uma ordem condicional; na Alpaca é uma ordem stop, GTC ou DAY para frações, recolocada quando expira |
| Posição | nunca se comparava com a exchange | a cada tick compara-se com a exchange; **só se ajusta para baixo** |
| Drawdown | auto-kill só em paper | auto-kill também em testnet/real, sobre o **equity da própria exchange** |

## Regras de segurança

- **Nunca vender duas vezes.** Antes de uma venda própria (take-profit, saída por tempo), o trader cancela o stop
  que está na exchange. Enquanto houver stop na exchange, o stop do cliente não dispara.
- **Só ajustar para baixo.** Se a exchange tem menos do que o livro (um fill que se perdeu, uma venda manual), o
  livro passa a seguir a exchange. Se tem mais, pode ser moeda tua de fora do trader: nunca é adotada. Os dois
  casos ficam no diário (`reconcile_mismatch`).
- **O stop na exchange é o stop já aprovado.** Executa o `stop_loss` aprovado com a compra (risco, gate, HITL),
  por isso não pede uma segunda aprovação. Em mainnet continua trancado se o adapter não foi criado para real.
- **MEXC spot não tem stop na exchange:** o stop fica no cliente e o diário diz isso uma vez (`stop_client_side`).
  As ordens de validação da MEXC (o "testnet" dela) nunca são executadas, por isso continuam a ser registadas
  localmente.
- **Usa uma conta ou subconta só para o trader.** O equity real inclui depósitos e levantamentos, e o ajuste para
  baixo assume que ninguém mexe na posição à mão.

## O que fica no diário

`fill` (com `source: exchange`, `order_id`, preço real e comissão), `order_unfilled`, `stop_placed`,
`stop_cancelled`, `stop_dropped`, `stop_client_side`, `reconcile_mismatch`, `auto_kill`.

## Limites

- Testado com uma exchange falsa e com o ccxt e o alpaca-py reais sem rede. O proxy desta sessão não chega às
  exchanges. **A primeira corrida em Bybit testnet e na conta paper da Alpaca é o teste que falta.**
- Os stops de frações na Alpaca são DAY: expiram ao fecho e são recolocados no tick seguinte. Entre o fecho e
  esse tick o stop vive só no cliente.
