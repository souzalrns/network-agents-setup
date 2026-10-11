# economia-trader: triagem de fluxo institucional ("whale screen") e protocolo de afinação

> **Data:** 2026-10-11. **Origem:** dois posts que o maestro trouxe do r/options e do r/Trading.
> O do r/Trading descreve 77 trades em 7 meses, 70% de acerto e $10K → $22K, com o Xynth.
> **Código:** `oss/economia-trader/src/economia_trader/{flow,screen,runner,report}.py`.

## 1. O método, e o que mudámos

O post usa o fluxo de opções como **sinal** e compra a **ação**, não a opção. Os filtros
determinísticos replicam os do post por defeito, em `ScreenConfig`:

| Filtro | Post | Aqui | Porquê |
|---|---|---|---|
| Capitalização | $1B–$10B | igual | uma ordem pesa mais numa mid-cap |
| Prémio por ordem | ≥ $30K | igual | corta ruído de varejo |
| IV rank | ≥ 80 | igual | o mercado está a precificar um movimento |
| Fluxo bullish | ≥ 70% | igual | é a direcção |
| Vol/OI | < 0,5 | `vol_oi_max = 0.5`, **e** `vol_oi_min` para testar a hipótese inversa | "atividade invulgar" costuma ser Vol/OI > 1 (posições novas); o OI só actualiza 1×/dia |
| DTE | 15–60 | igual | aposta de curto prazo |
| Resultados a ≤ 7 dias | só **marca** | **bloqueia** (`block_earnings_days = 7`; `null` = só marca) | um gap de resultados salta o stop e rebenta a `loss_at_stop` |

**O que o post não diz** e que nós definimos explicitamente, em `RunConfig`:
- stop a 8%, take-profit a 16% e saída por tempo aos 15 dias;
- 1 entrada nova por tick;
- auto-kill: drawdown de 15% desde o pico, ou 3 ticks seguidos sem chegar à exchange;
- **nunca reentrar com a mesma evidência** (os `print_ids` já usados): só fluxo novo reabre um ticker.

**O que não está provado no post:** os números são auto-declarados (77 trades, sem ganho médio
nem perda média, sem drawdown, sem benchmark) e o post gira à volta de uma ferramenta paga.
Tratamos tudo como hipótese a medir em paper.

## 2. Protocolo de afinação (para não ajustar os filtros ao passado)

1. **Cada configuração tem versão.** `RunConfig.version` é um hash dos filtros e das regras de
   saída. Vai carimbado em cada proposta (`proposer = whale-screen@<versão>`).
2. **Os resultados são por versão.** `economia-trader report` credita cada ida-e-volta à versão
   que *abriu* a posição: taxa de acerto, P&L, ganho médio, perda médio e expectância.
3. **Uma mudança de cada vez**, registada em `note`. Nunca mudar a meio de uma posição aberta.
4. **Mínimo de 20 trades fechados por versão** antes de comparar. Com menos, é ruído.
5. **Benchmark:** comparar o P&L da versão com o índice de mid-caps no mesmo período. Ganhar a
   um mercado em alta não prova vantagem.
6. **Só em paper** até uma versão bater o benchmark com ≥ 20 trades. O passo seguinte é o
   mandato de dinheiro real, uma decisão própria do maestro.

## 3. Como corre (na máquina do maestro)

```bash
# 1x por dia antes da abertura (cron/systemd), depois de o teu job de dados escrever flow.json
economia-trader run --exchange alpaca --mode paper --flow-file flow.json \
  --limits oss/economia-trader/examples/limits.stocks.example.json \
  --config oss/economia-trader/examples/run.example.json --once
economia-trader report          # resultados por versão
economia-trader screen --flow-file flow.json   # ver candidatos + motivos de exclusão (para afinar)
```

O formato do `flow.json` está em `examples/flow.example.json`: uma lista de ordens, com
`available_at` (quando *nós* podíamos saber). Qualquer fornecedor serve: basta um exportador.

## 4. Decisão D5: de onde vêm os dados de fluxo (o maestro decide)

| | Opção | Nota |
|---|---|---|
| **A (RECOMENDADA)** | **Começar com o que a Alpaca dá** (toolsets `options-data` e `news` do MCP oficial) e medir se chega para o filtro | Custo zero ou baixo e um só fornecedor. **Por verificar:** que tier do feed dá trades de opções com a condição de cada um em tempo útil |
| B | Fornecedor de fluxo pago (Unusual Whales, ou outro com API), exportado para `flow.json` | Dados melhores (sweeps e blocos classificados). Custo mensal; a classificação "bullish" é deles e é opaca |
| C | Xynth, como no post | Opaco, não dá para fazer backtest e prende-nos ao fornecedor. O post pode ser marketing |

**Porquê A:** a triagem é nossa e não depende do fornecedor. Primeiro prova-se o encanamento e a
disciplina de versões a custo zero. Só se o feed gratuito não chegar se paga a B, e aí com
números na mão.
