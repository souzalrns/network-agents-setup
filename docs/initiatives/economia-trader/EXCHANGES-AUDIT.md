# economia-trader — auditoria Bybit e MEXC + o que ficou construído

> **Data:** 2026-10-11. **Pedido do maestro:** "Ele vai estar apto a operar na Bybit? Integrar o
> `bybit-exchange/trading-mcp` (ou a Skill oficial). E na MEXC?"
> **Código:** `oss/economia-trader/` (incubado aqui, coerente com a §0 = A do
> `EXEC-PLAN-AUDIT-PHASE.md`. A §0 **continua aberta**: se o maestro escolher B, a pasta move-se
> tal como está).

## 1. Resposta directa

| Exchange | Hoje (v0.1) | Com 1 passo do maestro | Real |
|---|---|---|---|
| **Bybit** | **Sim, em paper**: preços reais públicos (V5) e fills simulados com taxa + slippage | **Testnet**: chave testnet + `ECONOMIA_TRADER_ALLOW_TESTNET=1` → ordens reais na testnet | Atrás de **3 travas** + kill switch: `ECONOMIA_TRADER_LIVE=I_ACCEPT_REAL_LOSSES`, `check-key` sem permissão de levantamento, aprovação humana **por ordem** (hitlwright) |
| **MEXC** | **Sim, em paper** (Spot V3, dados públicos) | **Sem testnet** (a MEXC não tem). O degrau equivalente é `/api/v3/order/test`: valida a assinatura e os parâmetros, mas não executa | Spot, com as mesmas 3 travas. **Futuros: não** (ver §3) |

Real fica **desligado por defeito**, como manda o PROMPT-MESTRE §3.7. Ligar exige acções explícitas
do maestro, e cada ordem pede aprovação.

## 2. Bybit: o que é oficial e o que fazemos com isso

### 2.1 `bybit-exchange/trading-mcp` (MCP oficial)

Auditado no commit `50418ff` (2026-10-06), clone só de leitura:

- **Oficial e MIT**: org `bybit-exchange`, `LICENSE` MIT; npm `bybit-official-trading-server@2.1.23` (`package.json`).
- **392 tools** em `src/tools/**`, das quais **116 escrevem** (`"readOnlyHint":false`) e têm `requiresApproval: true`.
  Isto inclui ordens, mas também conversões, empréstimos, earn, RFQ e copy-trading.
- **Aprovação por chamada**: `src/utils/approval.ts:29-62` exige ao cliente MCP *form elicitation*
  com o fingerprint SHA-256 dos parâmetros. Se o cliente não suportar elicitation, a chamada falha
  (isto é bom). Para um loop autónomo, porém, é um humano a clicar em cada chamada.
- **Testnet**: `BYBIT_TESTNET=true` (`README.md:155`). Os 23 tools de mercado funcionam sem chave (`README.md:35`).
- **Recomendações do próprio README** (`README.md:528`): IP allowlist, permissões mínimas, levantamentos desligados.
- **Não tem** motor de risco, limites de perda, kill switch nem diário. Expõe a API, não decide.

### 2.2 `bybit-exchange/skills` (Skill oficial)

Auditada no commit `a08a773` (2026-10-02), MIT:

- `SKILL.md:89`: "Permissions: enable **Read + Trade only** (NEVER enable Withdraw for AI use)", o que coincide com o nosso `check-key`.
- `SKILL.md:102-104`: `BYBIT_API_KEY` / `BYBIT_API_SECRET` / `BYBIT_ENV=testnet|mainnet`, os mesmos nomes de env que usamos.
- **Risco de supply chain**: `SKILL.md:30-40` manda o agente descarregar em runtime um manifest
  (`https://api.bybit.com/skill/manifest`) e ficheiros de `raw.githubusercontent.com/.../main/`. Ou seja,
  **auto-actualiza-se a partir do `main`, sem pin**. Uma skill que muda sozinha não passa a regra
  do `skill-scout`/F2-ALLOW-1 (hash aprovado). Para uso nosso: pin a um commit e auto-update desligado.

### 2.3 Decisão D1: como integrar a Bybit

| | Opção | Prós | Contras |
|---|---|---|---|
| **A (RECOMENDADA)** | **economia-trader executa; o MCP oficial é só para pesquisa/inspecção**, com chave read-only ou na testnet (`examples/bybit-trading-mcp.testnet.mcp.json`, versão pinada `2.1.23`) | Toda a ordem que um agente origina passa por risco → gate → diário. O MCP dá ao agente conversacional a API toda para *ver* | Duas peças em vez de uma |
| B | O agente opera directamente pelo `trading-mcp` (createOrder) | Zero código nosso | 116 tools de escrita expostas (empréstimos, convert…); sem limites de perda; a aprovação por chamada bloqueia um loop autónomo |
| C | A Skill oficial | Instala-se por um URL | Auto-update a partir do `main` sem pin (§2.2); as mesmas lacunas de risco da B |

**Porquê A:** é a única em que um LLM **não consegue** perder mais do que o limite declarado: o
motor de risco é determinístico e o gate é de outra camada. As evidências estão em
`oss/economia-trader/src/economia_trader/risk.py` e `safety.py`, e nos testes
`test_live_default_denies_then_human_approves` e `test_withdraw_key_refused`. Reutilizamos o
oficial onde ele é bom (dados, inspecção) e não reinventamos a API.

## 3. MEXC

- **Sem MCP oficial** (pesquisa a 2026-10-11): só projectos de terceiros (um servidor Encore.ts
  de RyanLisse, um de anúncios da kukapay, servidores multi-exchange via CCXT). Nenhum da MEXC.
- **Sem testnet pública**: o adapter usa `POST /api/v3/order/test` como degrau de validação (`dry_run=True` por defeito).
- **Futuros**: SDKs de terceiros documentam que a API de criação de ordens de futuros está
  "em manutenção" para chaves de retalho, e contornam-na com tokens de sessão do browser e
  endpoints de engenharia reversa. **Não verificado directamente**: o proxy desta sessão não
  resolve `mexc.com`. Fica **fora de âmbito**: o contorno viola o espírito dos termos e expõe a conta.

### Decisão D2: MEXC

| | Opção | Nota |
|---|---|---|
| **A (RECOMENDADA)** | **Spot via o nosso adapter (Spot V3, assinatura HMAC), `order/test` até live** | Zero dependências; as mesmas travas da Bybit; os testes provam o formato da assinatura (`test_mexc_dry_run_uses_order_test_and_signs_query`) |
| B | MCP de terceiros | Não oficial; recebe as credenciais |
| C | Futuros via SDK de engenharia reversa | Rejeitada: tokens de browser, risco de conta |

## 3b. Ações: Alpaca vs Interactive Brokers (pedido de seguimento, 2026-10-11)

Uma 2.ª IA sugeriu brokers de ações com MCP. Verifiquei os dois que propôs como escolha:

- **Alpaca**: `alpacahq/alpaca-mcp-server`, auditado no commit `a82ad1c` (2026-09-25), **MIT**.
  - O paper é o default: `ALPACA_PAPER_TRADE` vale `true` (`README.md:245`).
  - Filtra tools com `ALPACA_TOOLSETS` (`README.md:265`).
  - **Não tem** aprovação por chamada (não há `approval`/`elicit` em `src/`): com uma chave live, o agente executa directo.
  - A conta paper é gratuita e é simulação do lado do broker.
- **IBKR**: o comunicado oficial de 2026-07-28 diz que a IA **só redige instruções**. O cliente
  revê cada uma e submete-a numa plataforma IBKR. Logo, o MCP oficial **não executa** e não serve
  um loop autónomo. Para isso seria preciso a Client Portal/TWS API, com um gateway sempre a
  correr: mais pesado e fora da v0.1.
- **Não verificado por mim:** tastytrade, E*TRADE e os outros da lista (ficam como "a auditar se
  vierem a contar"). Também não verifiquei se a Alpaca aceita residentes do teu país: confirma ao
  abrir a conta. Para $100, usa uma **conta cash** e não margin, para não cair na regra de pattern
  day trader dos EUA. A liquidação T+1 limita a recompra com dinheiro ainda não liquidado.

### Decisão D4: broker de ações

| | Opção | Nota |
|---|---|---|
| **A (RECOMENDADA)** | **Alpaca como 3.º adapter**: a conta paper (simulação do broker) é o degrau "testnet"; o MCP oficial só para pesquisa, com `ALPACA_TOOLSETS` restrito | **Já implementado neste PR**: `exchanges/alpaca.py`, testes em `test_alpaca.py`, incluindo o Trader a enviar para `paper-api` |
| B | IBKR | O MCP oficial é óptimo para *analisar* com humano no loop, mas não executa. A execução autónoma exige o gateway TWS/Client Portal |
| C | Ficar só em cripto | Perde o paper do broker (gratuito e fiel) e o mercado regulado |

**Porquê A:** é o único com paper do lado do broker, gratuito, com a mesma API do live e uma
licença MIT auditável. O degrau seguinte da escada passa a ser um broker real a simular, e não a
nossa simulação. Encaixa nos $100: `max_order_notional` de 50, com ações fraccionadas.

## 4. Decisão D3: parâmetros iniciais de perda e de valor máximo (o maestro decide)

O pacote **não tem valores de dinheiro por omissão**: `RiskLimits.from_mapping` recusa uma config
sem eles (`test_limits_must_be_explicit`).

| | max_order_notional | max_loss_per_trade | max_daily_loss | posições | símbolos |
|---|---|---|---|---|---|
| **A (RECOMENDADA)** | **50 USDT** | **2 USDT** | **5 USDT** | **1** | BTCUSDT, ETHUSDT |
| B | 100 | 5 | 10 | 1 | idem |
| C | 20 | 1 | 3 | 1 | BTCUSDT |

**Porquê A:** o objectivo da 1.ª fase real é provar o encanamento (ordem → fill → diário →
reconciliação) e não ganhar dinheiro. Com 5 USDT/dia, o pior mês custa ~150 USDT, e com 2 USDT por
trade e stop obrigatório o sistema ainda faz trades reais com significado. A config está em
`oss/economia-trader/examples/limits.example.json`.

## 5. O que ficou construído (v0.1, `oss/economia-trader/`)

- Contratos v1: `EconomicEvent` com os 4 relógios e a guarda anti look-ahead, `TradeProposal`,
  `RiskAssessment`, `OrderIntent`, `Fill`, `SimulationRun`. Correspondem à T6 do plano.
- Motor de risco determinístico, que falha fechado (`risk.py`).
- Gate em escada paper → testnet → live, com kill switch, `check-key` sem levantamento e
  `HitlApprover` sobre o contrato hitlwright (`safety.py`). Corresponde à T7 do plano.
- Adapters Bybit V5 (mainnet e testnet), MEXC Spot V3 e **Alpaca** (ações/ETFs, conta paper + live), com transporte injectável; o mainnet é
  recusado pelo próprio adapter salvo em LIVE.
- Paper broker, backtest sem look-ahead (decide no fecho, executa na abertura seguinte) e a baseline SMA.
- Diário JSONL com cadeia SHA-256 e `verify-journal`.
- CLI, 61 testes (3.10 e 3.13), CI `economia-trader.yml`, sem workflow de publicação.

**Limites honestos da v0.1:** não reconcilia com os fills da exchange; os stops são do lado do
cliente; não arredonda lot-size; spot long-only.

## 6. Para o maestro ligar (por ordem, cada passo depende do anterior)

1. `pip install -e 'oss/economia-trader[hitl]'` na tua máquina. O proxy desta sessão bloqueia
   `api.bybit.com`/`api.mexc.com` (HTTP 403), por isso os testes reais correm aí.
2. **Paper**: `economia-trader ticker --symbol BTCUSDT`, depois
   `economia-trader backtest --symbol BTCUSDT --limits oss/economia-trader/examples/limits.example.json`.
3. **Testnet Bybit**: cria uma chave em testnet.bybit.com com **Read + Trade, sem Withdraw**,
   exporta `BYBIT_API_KEY`/`BYBIT_API_SECRET`, depois `ECONOMIA_TRADER_ALLOW_TESTNET=1`,
   `economia-trader check-key --mode testnet` e `economia-trader trade --mode testnet ...`.
4. **Paper + testnet durante ≥ 2 semanas**, com `verify-journal` intacto, antes de pensar em live.
5. **Live**: é uma decisão tua, numa fase própria (PROMPT-MESTRE §3.7). Sub-conta com saldo
   limitado, chave sem levantamento e com IP allowlist, `ECONOMIA_TRADER_LIVE=...`, e cada ordem
   aprovada com `hitlwright decide`.

## 7. Próximo trabalho (por valor)

1. Reconciliar com a exchange (Bybit `GET /v5/order/realtime` e `/v5/execution/list`) e pôr os stops do lado da exchange.
2. Arredondar lot-size/precisão (`/v5/market/instruments-info`, MEXC `exchangeInfo`).
3. Ligar o 1.º analista LLM (só propõe) a `EconomicEvent` reais, com custo medido pelo tokenwright.
