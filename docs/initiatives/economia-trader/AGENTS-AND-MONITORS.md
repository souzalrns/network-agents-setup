# economia-trader: monitorização (notícias + macro) e agentes LLM, reutilizados

> **Data:** 2026-10-11. **Decisão A** (`REUSE-AUDIT.md`): incorporar repos maduros, com o nosso código só no diferencial.
> **Código:** `src/economia_trader/monitors.py` (OpenBB) e `src/economia_trader/analysts.py` (TradingAgents).

## 1. Como as peças encaixam

```
OpenBB news.company / bls.calendar ──► EconomicEvent (4 relógios) ──► events.jsonl
                                                                          │
flow.json ──► whale screen (determinístico) ──► 0-3 candidatos            │
                                                    │                     ▼
                                    TradingAgents (LLM): confirma?   bloqueio macro:
                                     Buy/Overweight = sim             CPI/NFP/FOMC a ≤ 24 h
                                     resto = veto                     → nenhuma entrada nova
                                                    │
                                     risco → travas → ordem → diário
```

- **Monitores (OpenBB, Apache-2.0):** notícias por empresa (`news.company`, fornecedor nasdaq,
  sem chave) e o calendário do BLS: CPI, Employment Situation, PPI, JOLTS, etc. As datas que o
  OpenBB não lista (decisões do FOMC) vêm de um ficheiro mantido à mão
  (`examples/fomc.example.json`). Tudo vira `EconomicEvent`, com deduplicação, em `events.jsonl`.
- **Regra macro (nossa, determinística):** com um release de alto impacto a ≤
  `macro_block_hours` (24 h por defeito), o tick **não abre posições**. As saídas continuam a
  correr. Só conta o que já se sabia naquele momento (`available_at`).
- **Agentes (TradingAgents, Apache-2.0):** usamos o grafo inteiro dele (analistas de mercado,
  sentimento, notícias e fundamentais, debate bull/bear, trader e discussão de risco). A regra
  nossa: **o analista só confirma ou veta, nunca ordena.** Buy/Overweight deixa a entrada seguir
  para o motor de risco. Hold/Underweight/Sell/REVIEW vetam.
- **Custo controlado:**
  - o LLM só corre sobre 0–3 nomes por dia (os que passaram a triagem);
  - há um tecto diário (`max_runs_per_day`, 3 por defeito); acima dele, veta **sem chamar** o LLM;
  - os tokens por modelo ficam no diário (callback LangChain `TokenUsage`).
- **Evidência:** os relatórios dos agentes são guardados em `<state>/evidence/<data>_<ticker>.json`
  e referenciados nos `evidence_ids` da proposta.
- **Versões:** `macro_block_hours` e `confirm_with` entram no hash da versão. "Com LLM" e "sem
  LLM" são versões diferentes, comparáveis no `report`.

## 2. Segurança do que incorporámos

- O **TradingAgents não executa ordens** (`propagate()` devolve um rating). O envio de posts
  sociais para a TypeSafe (`post_screen.py`) só acontece com `TYPESAFE_API_KEY`: **não a
  definir**.
- O **OpenBB** fica só com `openbb-core` + `openbb-news` + `openbb-bls`: cerca de 71 pacotes e
  `pip-audit` limpo. Fica de fora `openbb-federal-reserve`, que traz o `diskcache` com
  PYSEC-2026-2447.
- **Nenhum teste** usa a rede nem um LLM. O encaixe real foi verificado com o TradingAgents
  instalado (assinatura de `TradingAgentsGraph(config, callbacks)` e `propagate(ticker, date)`,
  e o callback de tokens com objectos LangChain reais).

## 3. Decisão D6: que modelos para os agentes (o maestro decide)

A camada "quick" serve os analistas, investigadores, debatedores e o trader (muitas chamadas). A
camada "deep" serve os gestores e a decisão final (poucas chamadas).

| | Quick | Deep | Nota |
|---|---|---|---|
| **A (RECOMENDADA)** | **Gemini 3.5 Flash Lite** | **Claude Sonnet 5** | Segue a regra de custo do `CLAUDE.md` (Flash Lite e tier gratuito onde der). A decisão final fica num modelo forte. Duas chaves: `GOOGLE_API_KEY` + `ANTHROPIC_API_KEY`. Pronto em `examples/tradingagents.example.json` |
| B | Claude Haiku 4.5 | Claude Sonnet 5 | Uma só chave (Anthropic); custa mais na camada quick |
| C | Claude Opus 5.5 | Claude Opus 5.5 | A melhor qualidade, mas o custo por dia multiplica-se sem evidência de que valha |

**Porquê A:** a maior parte das chamadas é leitura e resumo, onde o Flash Lite chega. A
qualidade importa na síntese final, e é aí que fica o Sonnet. O diário mede os tokens por modelo,
por isso a escolha revê-se com números ao fim de 2 semanas.

## 4. Como correr (na máquina do maestro)

```bash
pip install -e 'oss/economia-trader[stocks,data]'
pip install 'git+https://github.com/TauricResearch/TradingAgents@1394a3f'
economia-trader monitor --news AAPL,MSFT --macro --calendar-file oss/economia-trader/examples/fomc.example.json
# run.json com "confirm_with": "tradingagents"
economia-trader run --exchange alpaca --mode paper --flow-file flow.json \
  --limits oss/economia-trader/examples/limits.stocks.example.json --config run.json \
  --ta-config oss/economia-trader/examples/tradingagents.example.json --once
economia-trader report
```
