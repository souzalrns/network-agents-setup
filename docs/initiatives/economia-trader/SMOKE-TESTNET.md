# Smoke testnet (L3): checklist obrigatório

**Data:** 2026-10-13 · **Issue:** #201 · **Estado:** BLOQUEADO nesta sessão (ver §4); comandos prontos para o maestro correr.

Nenhum L3 operacional prolongado (testnet ou paper da corretora a correr sozinho durante horas/dias)
começa sem este smoke passar e o resultado ficar registado na #201. L4 (live) continua **bloqueado**
até esta evidência existir e ser aprovada (ver `AUTONOMY_LEVELS.md`).

## 1. O que o smoke prova

| # | Prova | Onde se vê |
|---|---|---|
| 1 | A compra só entra no livro quando a exchange diz que encheu (fill real, preço da exchange) | diário: `order` → `fill` com `"source": "exchange"` |
| 2 | Depois do fill fica **um** stop pousado na exchange (Bybit: ordem condicional `triggerPrice`) | diário: `stop_placed`; exchange: 1 ordem condicional aberta |
| 3 | O livro bate com a exchange (`sync_positions` sem divergência) | nenhum `reconcile_mismatch` |
| 4 | Antes de vender por conta própria, o trader cancela o stop da exchange | diário: `stop_cancelled` antes do `order` de venda |
| 5 | Depois da saída, nada fica aberto: sem posição no livro e sem stop | `state.positions` e `exchange_stops` vazios |
| 6 | **Sem venda dupla:** 1 venda de saída e saldo do activo a 0 na exchange | diário: 1 `order` de venda; exchange: saldo base 0 |
| 7 | O diário continua íntegro (cadeia de hashes) | `verify-journal` sem erros |

O script `oss/economia-trader/examples/smoke_testnet.py` faz o ciclo e verifica os 7 pontos. Está
coberto por `tests/test_smoke_script.py`, que o corre contra um cliente ccxt **real** com todas as
chamadas de rede gravadas offline (passa: 7/7) e prova que, sem `ECONOMIA_TRADER_ALLOW_TESTNET=1`,
não sai nenhuma ordem.

## 2. Pré-requisitos (nunca em ficheiros, nunca em commits)

- Conta **testnet** Bybit (https://testnet.bybit.com) com fundos de teste; chave **dedicada** com
  leitura + trading spot, **sem levantamentos**. Se usarem Alpaca: conta **paper**.
- Variáveis só no ambiente da shell (não em `.env` versionado):
  - Bybit: `BYBIT_API_KEY`, `BYBIT_API_SECRET`
  - Alpaca: `ALPACA_API_KEY`, `ALPACA_SECRET_KEY`
  - trava de testnet: `ECONOMIA_TRADER_ALLOW_TESTNET=1`
  - **não** definir `ECONOMIA_TRADER_LIVE` (live continua fechado).
- Rede com acesso a `api-testnet.bybit.com` (e `paper-api.alpaca.markets` para Alpaca).

## 3. Comandos exactos (a partir de `oss/economia-trader/`)

```bash
python -m venv .venv && . .venv/bin/activate && pip install -e '.[test]'
export ECONOMIA_TRADER_ALLOW_TESTNET=1
read -rs BYBIT_API_KEY && export BYBIT_API_KEY        # colar a chave de TESTE (não fica no histórico)
read -rs BYBIT_API_SECRET && export BYBIT_API_SECRET

# 0) regressão paper (tem de continuar verde)
python -m pytest -q

# 1) travas: testnet aberto, live fechado
economia-trader gate --mode testnet      # testnet_enabled: true, live_acknowledged: false
economia-trader gate --mode live         # live_acknowledged: false

# 2) chave segura: pode negociar, NÃO pode levantar
economia-trader check-key --exchange bybit --mode testnet   # safe_for_trading: true, can_withdraw: false

# 3) ciclo compra -> stop na exchange -> reconcile -> saída (BTCUSDT, ~10 USDT de teste)
python examples/smoke_testnet.py bybit BTCUSDT 0.0002 examples/limits.example.json /tmp/et-smoke
#    sai com código 0 e todos os "checks" a true; o diário fica em /tmp/et-smoke/journal.jsonl

# 4) diário íntegro
economia-trader verify-journal /tmp/et-smoke/journal.jsonl     # journal: intact

# 5) alertas: canal configurado e sem fuga de segredos (ver ALERTS.md para os nomes das variáveis)
economia-trader alerts --state-dir /tmp/et-smoke --test
python -c "import os; t=open('/tmp/et-smoke/alerts.jsonl').read(); print(sum(t.count(os.environ[k]) for k in ('BYBIT_API_KEY','BYBIT_API_SECRET')))"   # tem de dar 0
```

Na interface da Bybit testnet, confirmar à mão: 1 compra executada, 1 ordem condicional criada e
depois cancelada, 1 venda executada, saldo BTC de volta a 0.

**Alpaca (paper), mesma prova** (só com mercado aberto; fraccionárias usam stop DAY):

```bash
read -rs ALPACA_API_KEY && export ALPACA_API_KEY
read -rs ALPACA_SECRET_KEY && export ALPACA_SECRET_KEY
economia-trader check-key --exchange alpaca --mode testnet
python examples/smoke_testnet.py alpaca AAPL 1 examples/limits.stocks.example.json /tmp/et-smoke-alpaca
```

O script só foi validado offline com Bybit; o ramo Alpaca usa o mesmo protocolo (`order_status`,
`place_stop`, `cancel_order`, `position_qty`), coberto pelos testes do #199, mas não pelo script.

**Bybit EU (Portugal e resto do EEE):** a Bybit global bloqueia o acesso a partir de Portugal. Usa-se a
venue `bybiteu` (`ccxt.bybiteu`: `bybit.eu`, testnet em `api-testnet.bybit.eu`), com chave criada na
testnet da Bybit EU e os mesmos nomes de variáveis (`BYBIT_API_KEY`/`BYBIT_API_SECRET`). Nos comandos
acima, trocar `bybit` por `bybiteu`:

```bash
economia-trader check-key --exchange bybiteu --mode testnet   # safe_for_trading: true, can_withdraw: false
python examples/smoke_testnet.py bybiteu BTCUSDT 0.0002 examples/limits.example.json /tmp/et-smoke
economia-trader verify-journal /tmp/et-smoke/journal.jsonl
```

O ciclo offline do script corre para `bybit` e `bybiteu` (`tests/test_smoke_script.py`, #201).

**MEXC:** não tem testnet. `/api/v3/order/test` só valida o pedido e nunca enche, por isso não prova
os pontos 1–6. Não conta como smoke L3.

## 4. Estado nesta sessão (2026-10-13)

| Passo | Resultado |
|---|---|
| Regressão paper (suite) | **feito**: 150 passed (py3.11 e py3.10) em `main` + este PR |
| Script do ciclo, offline (ccxt real, rede gravada) | **feito**: 7/7 checks; sem a trava de testnet não sai ordem |
| `alerts --test` sem canais | **feito** depois do fix #202 (antes rebentava numa pasta nova) |
| `alerts --test` com canais falsos | **feito**: canais falham (rede), código 0, segredo 0 vezes na saída e no `alerts.jsonl` |
| Bybit testnet real | **BLOQUEADO**: o proxy da sessão recusa `api-testnet.bybit.com` (`CONNECT tunnel failed, response 403`); sem chaves de teste no ambiente |
| Alpaca paper real | **BLOQUEADO**: idem (`paper-api.alpaca.markets` → 403) |
| Bybit EU testnet real (maestro, 2026-10-19, máquina local) | **Reportado pelo maestro:** chave EU com `check-key` → `can_withdraw: false`; teste na testnet da Bybit EU concluído com sucesso; chaves antigas revogadas, chaves EU só no ambiente local. **Por anexar à #201:** o JSON do `smoke_testnet.py bybiteu` (7 checks) e o `verify-journal` (critério do §5) |

## 5. Critério para passar a L3 prolongado

Os 7 checks a `true` em Bybit testnet (e em Alpaca paper, se for usada), a interface da exchange a
confirmar o mesmo, `alerts --test` a chegar ao canal real, e o resultado (JSON do script + diário
sanitizado, nunca chaves) anexado à #201. Antes de L3 prolongado ficam também por fechar as lacunas
G1 e G2 de `VISUAL_AND_AUTONOMY_PLAN.md` (alerta e bloqueio de entradas em divergência).
