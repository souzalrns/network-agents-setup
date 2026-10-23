# Trading — método da revisão pós-trade (F6)

Fonte: `oss/economia-trader` (README §"Post-trade review"; `src/economia_trader/review.py`). Método adaptado do Trade Reviewer do HyperGrok (galleonlabs/hypergrok-trading-desk, MIT); o código é do economia-trader.

## O que é um trade

Um trade é **flat → posição → flat** num símbolo. Uma corrida de grid com vários lotes conta como um trade, e o seu 1R é a soma do `loss_at_stop` das entradas.

## Regras do método

1. **Rever a partir do registo do exchange** (as linhas `fill` do journal), nunca do chat nem das intenções.
2. **Avaliar o processo primeiro, à parte do resultado.** Um trade perdedor com processo limpo continua `clean`.
3. **Medir os custos:** slippage de entrada e de saída contra o preço do ticket (bps) e taxas (dinheiro e bps).
4. **Um achado repetível por trade**, não uma lista.

## Classificação do processo

| Grau | Quando |
|---|---|
| `clean` | Nenhuma quebra |
| `minor break` | Stop no exchange mais de 60 s depois do fill; stop só do lado do cliente; stop retirado; erro de execução |
| `major break` | Entrada sem stop; fill sem avaliação de risco aprovada; posição de testnet ou live que nunca teve stop; diferença entre o livro e o exchange |

## Resultado

- **Em R**, com 1R = `loss_at_stop` do motor de risco, e **em dinheiro**, depois de taxas.
- Sem adjectivos: o número diz se foi bom ou mau.

## Fuga de custos (achado de um trade limpo)

- Slippage acima de **20 bps** é o achado de um trade limpo.
- Taxas acima de **metade do bruto** de um trade ganhador são uma fuga.

## Resumo por semana ISO

Número de trades fechados, taxa de acerto, ganho e perda médios em R, **expectativa em R**, maior perda, taxas como fracção do bruto, contagem por grau de processo e a quebra mais frequente (`pattern`).

## Como ler o JSON do `economia-trader review`

- `trades[]`: `process.grade`, `process.breaks[]`, `outcome` (`net`, `gross`, `r`, `risk_1r`), `costs` (`fees`, `fees_bps`, `entry_slippage_bps`, `exit_slippage_bps`) e `finding` (`type`, `stage`, `detail`).
- `weeks{}`: o resumo da semana, por chave ISO (ex.: `2026-W43`).
- `open[]`: posições ainda abertas (não entram na revisão); `orphan_sells`: vendas sem entrada conhecida.
- Valores em texto decimal (ex.: `"-1.13"`): copiar tal como estão, nunca arredondar de memória.
