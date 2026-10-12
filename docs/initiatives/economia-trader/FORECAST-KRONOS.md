# economia-trader: confirmação por previsão (Kronos)

> Decisões do maestro (2026-10-12, perguntas sim/não): **P-68 = A** (Kronos entra como confirmação
> opcional, provado primeiro no backtest contra a mesma versão sem ele, e só depois usado em paper) e
> **P-69 = B** (não gera ideias sozinho, por agora). PENDENCIAS §10.

## O que é

[shiyu-coder/Kronos](https://github.com/shiyu-coder/Kronos) (commit auditado `67b630e`, código **MIT**) é um
modelo de base para velas (OHLCV), treinado em dados de dezenas de bolsas. Os pesos estão no Hugging Face
(`NeoQuasar/Kronos-small`, `NeoQuasar/Kronos-Tokenizer-base`). Daqui não foi possível abrir o Hugging Face
(proxy), por isso **a licença dos pesos fica por confirmar no model card antes do uso** (ver "O que falta").

## Como entra (e como não entra)

```
ideia (fluxo / insiders) ─► veto de sentimento ─► **Kronos: confirma?** ─► TradingAgents (opcional) ─► risco ─► gate
```

- **Só confirma ou veta.** Nunca cria ideias (P-69) e nunca ordena.
- **Fail-closed.** Histórico curto (`NO_DATA`), previsão vazia (`NO_FORECAST`), tecto diário (`BUDGET`) ou erro
  do modelo (`ERROR`) **vetam a entrada**, mas o tick continua (saídas e outras ideias seguem).
- **Probabilístico, mas reprodutível.** Sorteia `samples` caminhos com sementes fixas (`seed`, `seed+1`, ...).
  Só confirma se, nos próximos `forecast_horizon` candles:
  - o fecho médio previsto ficar pelo menos `forecast_min_expected_return` acima do último fecho (por defeito, +1 %), **e**
  - pelo menos `forecast_min_up_share` dos caminhos acabarem acima do último fecho (por defeito, 60 %).
- **Versionado.** `forecast_confirm`, `forecast_interval`, `forecast_lookback`, `forecast_horizon` e os dois
  limiares entram no hash da versão, para o `report` separar os resultados "com Kronos" dos "sem Kronos".
- **Visível.** O diário regista cada previsão (`forecast`: sinal, retorno esperado, % de caminhos em alta). O
  painel tem a secção "Previsões (Kronos)" e, no Star-Office-UI, o analista mostra `ACME: UP (kronos)`.

## Ordem de uso (P-68): backtest primeiro, paper depois

1. **A/B no backtest**, com a mesma estratégia com e sem a confirmação:

   ```bash
   economia-trader backtest --exchange bybit --symbol BTCUSDT --interval 1d --limit 1000 \
     --limits limits.json --forecast kronos --kronos-repo ~/ext/Kronos [--config run.json]
   ```

   A saída traz `sem_previsao`, `com_previsao` e `comparacao` (trades fechados, acerto, retorno, drawdown,
   comissões, `melhora_retorno`). A estratégia só vê as velas até à decisão e executa na abertura seguinte,
   como no backtest normal; o teste `test_with_forecast_confirm_filters_buys_without_lookahead` prova-o.

2. **Só se a A/B ganhar** (retorno ou drawdown melhores, com um número de trades que não seja ridículo), ligar em
   paper no `run.json`: `"forecast_confirm": true`, e correr com `--kronos-repo`.

3. O `report` mostra os resultados por versão; a versão com Kronos tem hash próprio.

## Instalar

O Kronos não está no PyPI (o código fica numa pasta `model/` de topo). Clona-se o commit auditado e instala-se
o extra:

```bash
git clone https://github.com/shiyu-coder/Kronos ~/ext/Kronos && git -C ~/ext/Kronos checkout 67b630e
pip install -e 'oss/economia-trader[forecast]'   # torch, pandas, einops, huggingface_hub, safetensors, tqdm
```

O primeiro uso descarrega os pesos do Hugging Face (Kronos-small: ~25 M parâmetros; corre em CPU).

O loader (`forecast.load_kronos_package`) importa `model/` do checkout. O Kronos importa-se a si próprio como
`model` (`from model.module import *`), por isso o nome `model` fica ocupado. O checkout só entra no
`sys.path` durante o import, e o loader **recusa** carregar o Kronos se já estiver importado outro pacote
chamado `model`, em vez de o sombrear.

## Custos

Sem API paga. É CPU local: cada confirmação faz `samples` (por defeito 10) previsões de `forecast_horizon`
candles. O tecto `max_runs_per_day` (20) limita o loop. No backtest, o Kronos só é chamado nos sinais de compra.

## O que falta (do lado do maestro)

- Confirmar a licença dos pesos no model card `NeoQuasar/Kronos-small` (o código é MIT; os pesos não foram
  verificados daqui).
- Correr a A/B com dados reais (o sandbox não chega às bolsas nem ao Hugging Face) e decidir se liga em paper.

## Evidência

- Código: `oss/economia-trader/src/economia_trader/forecast.py`, `runner.py` (`_forecast_veto`), `cli.py`
  (`backtest --forecast kronos`, `run --kronos-repo`).
- Testes: `oss/economia-trader/tests/test_forecast.py`. Usam um previsor falso e um checkout falso do Kronos com
  o mesmo padrão de import, sem torch e sem pesos.
