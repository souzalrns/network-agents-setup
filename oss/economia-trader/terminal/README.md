# Terminal de mercado do economia-trader (OpenTerminal)

Um terminal de mercado para a tua máquina, ao estilo "Bloomberg", com dados públicos e sem chaves pagas. Mostra o
mapa de calor do mercado americano, gráficos com 8 horizontes e indicadores (SMA, EMA, VWAP, Bollinger, RSI, MACD),
cotações com fundamentais, screener, opções, cripto, macro (curva de juros, VIX), calendário económico e de
resultados, notícias e insiders. Junta-lhe o widget **AGENT**, que mostra o que o economia-trader está a fazer.

Base: [ErTasselli/OpenTerminal](https://github.com/ErTasselli/OpenTerminal) (MIT). As alterações estão em
`PROVENANCE.md` e o README original em `UPSTREAM-README.md`.

## Correr

Precisa de Node.js 22 ou mais recente.

```bash
cd oss/economia-trader/terminal
npm ci
# o terminal lê o estado do agente desta pasta (a mesma --state-dir do `economia-trader run` / `grid`)
ECONOMIA_TRADER_STATE_DIR=~/et/paper npm run dev
# abre http://localhost:3000   (o servidor de dados fica em 127.0.0.1:4000, só local)
```

Do lado do economia-trader, o painel estático liga cada ticker ao terminal:

```bash
economia-trader dashboard --state-dir ~/et/paper --openterminal-url http://localhost:3000 --refresh 60
```

## Regras

- **O terminal nunca envia ordens.** O widget AGENT só lê o `state.json`, o `journal.jsonl` e o `alerts.jsonl` da
  pasta do agente. As decisões do economia-trader continuam a usar os preços da própria exchange, nunca os dados
  deste terminal.
- **Os dados de mercado são públicos mas não oficiais** (Nasdaq, Yahoo, TradingView, CoinGecko, Binance, FRED,
  Forex Factory). Servem para ver e estudar, não para executar, e um fornecedor pode falhar sem aviso. Uso pessoal;
  uso comercial exige rever os termos de cada fonte.
- **O servidor escuta só em `127.0.0.1`.** Não definas `API_HOST=0.0.0.0` sem `API_KEY` e `WEB_ORIGIN`
  (ver `UPSTREAM-README.md`).
- **O assistente de IA é opcional** e usa a API da Anthropic, que é paga. Sem `ANTHROPIC_API_KEY` fica desligado e o
  resto funciona.
- `ECONOMIA_TRADER_STALE_AFTER_S` (por defeito 900) define quando o widget marca o agente como `STALE`.
