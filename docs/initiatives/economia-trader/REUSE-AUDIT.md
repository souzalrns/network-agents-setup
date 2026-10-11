# economia-trader: auditoria de reutilização (decisão A, 2026-10-11)

> **Pergunta do maestro:** "Você construiu ou incorporou? Tem muito repo maduro nessa área."
> **Resposta:** eu tinha construído demais. A decisão A diz: manter só o que é nosso e incorporar
> os repos maduros para tudo o que não é diferencial.

## 1. O que fica nosso (o diferencial) e o que passa a vir de fora

| Peça | Antes | Agora |
|---|---|---|
| Risco determinístico, travas, kill switch, aprovação por ordem, `check-key` | nosso | **nosso** (nenhum repo maduro o tem de forma determinística) |
| Diário com cadeia SHA-256, triagem versionada, relatório por versão | nosso | **nosso** |
| Adapters cripto (assinatura HTTP, símbolos, testnet, precisão) | escritos à mão | **ccxt** (PR1, este) |
| Adapter ações | escrito à mão | **alpaca-py**, SDK oficial (PR1, este) |
| Monitorização de notícias e macro | — | **OpenBB** (PR2) |
| Agentes analistas (notícias, fundamentais, sentimento, técnico, debate) | — | **TradingAgents** (PR2) |

## 2. Auditoria dos 4 repos

Cada um foi instalado num venv limpo com Python 3.12 e passado por `pip-audit`. Em cada um
procurei também os caminhos de execução: algum envia ordens ou dados para fora sem passar por nós?

| Repo | Commit / versão | Licença | Pacotes no venv* | `pip-audit` | Caminhos de execução |
|---|---|---|---|---|---|
| **ccxt** | `4004c1a` (2026-10-11) / 4.5.85 | MIT | 46 | 1: `multidict 6.7.1` CVE-2026-104874 (ver §3) | Só o que lhe pedirmos; as ordens passam sempre por `CcxtSpot.place_order` |
| **alpaca-py** | `2a30779` (2026-10-10) / 0.44.0 | Apache-2.0 | 41 | limpo | Idem, via `AlpacaPy.place_order` |
| **OpenBB** | `ae02687` (2026-10-02) / 5.0.0 | Apache-2.0 | **238** | 1: `diskcache 5.6.3` PYSEC-2026-2447, **sem versão corrigida** | Só lê dados. Pesado: no PR2 instalar só `openbb-core` e as extensões precisas (ex.: `openbb-fred`, notícias), não o meta-pacote |
| **TradingAgents** | `1394a3f` (2026-10-03) / 0.6.0 | Apache-2.0 | 102 | limpo (o próprio pacote não está no PyPI: instala-se do git, com o commit fixado) | **Não executa ordens**: `propagate()` devolve `(estado, rating)`, com o rating em Buy/Overweight/Hold/Underweight/Sell/REVIEW. **Envio externo opcional:** `agents/post_screen.py` envia posts sociais para `api.typesafe.ai`, mas **só** com `TYPESAFE_API_KEY` definida. Por omissão não corre, e assim deve ficar |

\* Inclui as cerca de 20 dependências do próprio `pip-audit`.

## 3. O CVE do multidict (aceite, com fundamento)

- O ccxt 4.5.85 **fixa** `multidict==6.7.1`, por isso não podemos subir para a 6.9.1 sem o ccxt
  o fazer primeiro. Tentei, e o pip devolve `ResolutionImpossible`.
- O CVE é uma fuga de memória quando um **servidor** avalia `operand | d.items()` ou
  `d.items() - operand` sobre cabeçalhos controlados por um atacante. Só afecta a disponibilidade.
- **Não é alcançável aqui:** usamos o ccxt **síncrono** (sobre `requests`). O `multidict` só é
  usado pelo `aiohttp`/`yarl` do ccxt assíncrono, e mesmo esse é cliente, não servidor.
- Mitigação, se algum dia se usar o ccxt assíncrono: `MULTIDICT_NO_EXTENSIONS=1`.
- Reavaliar quando o ccxt subir o pin (o `pip-audit` volta a acusá-lo a cada auditoria).

## 4. O que o ccxt resolveu que o código à mão não resolvia

- **Precisão e lote por instrumento:** `amount_to_precision` / `price_to_precision`. A
  quantidade é arredondada para baixo ao passo do mercado e o preço ao tick mais próximo.
  Abaixo do mínimo do mercado, recusa *antes* de enviar.
- **Bybit, compra spot a mercado:** a quantidade é em quote por omissão. O ccxt resolve isso
  (`marketUnit`, contas UTA vs clássicas) em `bybit.py:4250-4290`.
- **Testnet:** `set_sandbox_mode(True)` usa os URLs oficiais. A MEXC não tem sandbox, por isso
  usa `params={"test": True}` (`/api/v3/order/test`).
- **Símbolos:** aceita `BTCUSDT` (o nosso formato) ou `BTC/USDT` (o do ccxt).

## 5. Testes

Os testes usam o **ccxt real**, com mercados carregados offline (`set_markets`): precisão,
URLs de sandbox, construção do pedido e verificação das chaves são o código verdadeiro, e só as
chamadas de rede são substituídas por gravadores. O alpaca-py é testado com os **objectos de
pedido reais** do SDK (`MarketOrderRequest`, `StockBarsRequest`). Nada contacta uma exchange.
