# economia-trader: mais evidência (insiders/OSINT, FinBERT, Adanos)

> **Data:** 2026-10-12. **Decisões:** P-59 (FinBERT), P-62 (edgartools / insiders), P-63 (Adanos
> opcional), P-64 (OSINT de infraestrutura: não por agora), P-65 (busca de pessoas: de fora).
> **Código:** `src/economia_trader/signals.py`, o runner (ideias de várias fontes) e o painel.

## 1. O que entra

| Sinal | Fonte (reutilizada) | Como entra | Relógio que conta |
|---|---|---|---|
| **Compras de insiders em grupo** | SEC Form 4 via **edgartools** (MIT, `b82e098`, 63 pacotes, `pip-audit` limpo) | `insider_clusters`: ≥ 2 insiders distintos compram ≥ $100k em 10 dias → uma **ideia** (como a triagem de fluxo) | `available_at` = quando o filing chegou ao EDGAR, nunca a data do negócio (o Form 4 pode atrasar 2 dias úteis) |
| **Sentimento das notícias** | **FinBERT** (ProsusAI/finbert, Apache-2.0), local, sem custo | Cada notícia guardada recebe positive/negative/neutral → evento `news_sentiment` | só depois de pontuada |
| **Sentimento social** | **Adanos** (SDK MIT; plano grátis com 30 dias de histórico; opcional, só com `ADANOS_API_KEY`) | buzz e % bullish por ativo (Reddit, X, notícias, Polymarket) → `social_sentiment` | a hora da recolha |

## 2. Como são usados (regras nossas, determinísticas, versionadas)

- **Ideias de várias fontes:** o runner junta o fluxo de opções (`use_flow`) e os insiders
  (`insider_signal`). Quando as duas concordam no mesmo ativo, a ideia junta as evidências
  (`flow+insiders`) e passa à frente.
- **Veto por sentimento** (`sentiment_veto`): sem entrada se, nas últimas 48 h, ≥ 60% das
  manchetes sobre o ativo forem negativas, ou se a média de bullish social for < 30%. Só conta o
  que já se sabia naquele momento.
- **Atribuição:** cada ida-e-volta é creditada à fonte e à versão que a abriram
  (`whale-screen@v`, `insiders@v`, ...). O `report` diz qual fonte ganha dinheiro.
- O analista LLM (`confirm_with`) continua a ser o último filtro antes do risco, e as travas
  ficam iguais.

## 3. OSINT que **não** entra

- **Infraestrutura** (theHarvester GPL-2, recon-ng GPL-3, SpiderFoot MIT parado desde 2023):
  não têm a ver com o trader. Ficam como candidatos da área security, em lab e só contra domínios
  próprios (P-64 = não por agora).
- **Busca de pessoas** (Sherlock e Maigret, ambos MIT): ficam **de fora**. Recolhem dados de
  indivíduos, colidem com a política de privacidade (GOV-IMPACT) e não têm uso no trading (P-65).

## 4. Correr (na máquina do maestro)

```bash
pip install -e 'oss/economia-trader[sec,nlp,sentiment,data]'
economia-trader monitor --news ACME,BETA --insiders --sec-identity "Nome email@exemplo" --finbert
ADANOS_API_KEY=... economia-trader monitor --adanos ACME,BETA
# run.json: {"insider_signal": true, "sentiment_veto": true, ...}
economia-trader run --exchange alpaca --mode paper --flow-file flow.json \
  --limits oss/economia-trader/examples/limits.stocks.example.json --config run.json --once
economia-trader dashboard
```

**Por verificar com rede real:** os fetchers do edgartools e da Adanos foram escritos contra o
código instalado (nomes de colunas e de métodos confirmados), mas esta sessão não chega ao EDGAR
nem à Adanos. A primeira corrida na tua máquina valida-os.
