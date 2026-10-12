# economia-trader: ai-hedge-fund como 2.ª opinião (P-59)

> **P-59 = A** (maestro, 2026-10-11): FinBERT + ai-hedge-fund, sempre só a propor e medidos por versão. O FinBERT
> entrou no #191. Este documento fecha a parte do ai-hedge-fund. **P-70 = B** (maestro, 2026-10-12): não se assina nada; o código fica pronto e desligado.

## O que é

[virattt/ai-hedge-fund](https://github.com/virattt/ai-hedge-fund) (**MIT**; auditado na v2.5.0, commit `78b779c`;
no PyPI como `aihf==2.5.0`) junta personas de investidores (Buffett, Munger, Graham, Lynch, Druckenmiller). Cada
persona é um prompt de sistema que raciocina sobre um **snapshot de fundamentais point-in-time**: só entram
relatórios com `filing_date <= data` (confirmado no pedido real: `filing_date_lte=2026-10-09`). Devolve uma
convicção em [-1, +1] e, quando não consegue formar opinião, **abstém-se** (não inventa um neutro).

É uma visão **fundamental e lenta**, diferente das outras: o TradingAgents debate notícias e mercado, o Kronos lê
velas, o fluxo e os insiders dão a ideia. Por isso entra como 2.ª opinião e não como fonte de ideias.

## Porque corre num ambiente à parte

O `aihf` fixa `langchain-anthropic==0.3.5` (portanto `langchain-core` 0.3.x), e o TradingAgents exige
`langchain-core>=1.6.5`. **Não cabem no mesmo venv.** Além disso, o `pip-audit` do `aihf==2.5.0` mostra:

| Pacote (fixado pelo aihf) | Aviso | Alcançável aqui? |
|---|---|---|
| langchain-anthropic 0.3.5 | PYSEC-2026-2556 (path traversal no middleware de pesquisa de ficheiros) | Não: não usamos esse middleware nem Anthropic neste caminho |
| langchain-core 0.3.86 | PYSEC-2026-2193 (`prompts.loading` lê caminhos de configs) | Não: os prompts são construídos em código |
| langchain-core 0.3.86 / langchain-openai 0.3.35 | PYSEC-2026-2562, PYSEC-2026-76 (SSRF na contagem de tokens de imagens) | Não: sem imagens, sem OpenAI |
| python-dotenv 1.0.0 | PYSEC-2026-2270 (`set_key` segue symlinks) | Não: só a TUI do aihf escreve `.env`; a ponte não a importa |

Decisão de desenho: o economia-trader **não depende** do `aihf`. Corre-o com o Python do venv dele
(`pipx install aihf==2.5.0`) num processo filho (`python -I aihf_bridge.py`). O pedido vai por stdin e a resposta
volta em JSON por stdout. O processo filho recebe **só** as chaves de dados e de LLM (lista fechada em
`analysts._AIHF_ENV`): **nunca** as chaves das bolsas ou do Alpaca, e nunca `TYPESAFE_API_KEY`. Os modelos
TypeSafe (`jev-*`) são recusados.

## Como decide

```
ideia ─► sentimento ─► Kronos ─► TradingAgents ─► ai-hedge-fund ─► risco ─► gate
                                  (cada analista tem de confirmar; o 1.º que vetar pára a cadeia)
```

- Confirma se, entre as personas que formaram opinião, a **convicção média ≥ `min_conviction`** (0,2) **e** pelo
  menos **`min_bullish_share`** (50 %) estão em alta.
- Veta em `NO_VIEW` (todas abstiveram-se), em `ERROR (...)` (processo, dados ou chave) e em `BUDGET`
  (`max_runs_per_day`).
- Cada opinião vai para `evidence/<data>_<ticker>_aihf.json` (sinais e raciocínio de cada persona) e para o diário
  (`opinion`, `by: ai-hedge-fund`). O painel mostra o analista, o rating e as chamadas ao LLM e à cache.
- O aihf guarda em cache cada prompt pelo hash do snapshot. Enquanto não sai um relatório novo, a mesma pergunta
  não paga outra chamada.

## Ligar

```bash
pipx install aihf==2.5.0                         # venv próprio; o Python fica em ~/.local/pipx/venvs/aihf/bin/python
export FINANCIAL_DATASETS_API_KEY=...            # dados (ver P-70)
export GOOGLE_API_KEY=...                        # gemini-3.8-flash (o mais barato da lista do aihf)
```

`run.json`: `"confirm_with": "ai-hedge-fund"` (ou `"tradingagents+ai-hedge-fund"`). Depois:

```bash
economia-trader run --exchange alpaca --mode paper --flow-file flow.json --limits limits.json --config run.json \
  --aihf-python ~/.local/pipx/venvs/aihf/bin/python --aihf-config oss/economia-trader/examples/aihf.example.json --once
```

`confirm_with` entra no hash da versão, por isso o `report` separa os resultados com e sem esta opinião.

## Custos

- **LLM:** por defeito `gemini-3.8-flash` com 3 personas, ou seja até 3 chamadas por candidato, no máximo 5
  candidatos por dia, com cache por relatório. O default do aihf é `claude-opus-5-5` (caro); não o usamos.
- **Dados:** a [Financial Datasets](https://financialdatasets.ai) é paga, fora alguns tickers grátis. É a única fonte
  que o aihf suporta. **P-70.**

## Evidência

- Código: `oss/economia-trader/src/economia_trader/analysts.py` (`AiHedgeFundAnalyst`, `subprocess_bridge`),
  `aihf_bridge.py`, `runner.py` (`_second_opinions`), `cli.py` (`--aihf-python`, `--aihf-config`).
- Testes: `tests/test_aihf.py`. Cobrem a regra de decisão, os vetos, a lista fechada de variáveis de ambiente
  (com um interpretador falso), a cadeia de dois analistas e o painel.
- Verificação manual contra o `aihf==2.5.0` real, num venv à parte:
  - sem chave, falha com `GOOGLE_API_KEY not found` (fica veto `ERROR`);
  - com chaves falsas, chega ao pedido point-in-time à Financial Datasets, que o proxy deste ambiente bloqueia.
