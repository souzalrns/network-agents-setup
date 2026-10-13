# Treino por walk-forward (`economia-trader tune`)

**Data:** 2026-10-13 · **Decisão:** opção A do maestro ("treinar = backtest walk-forward + paper por
versões"). Nada aqui envia ordens: tudo corre em histórico, pelo mesmo motor de risco e pelo mesmo
broker paper do `backtest`.

## O que "treinar" quer dizer aqui

Os analistas LLM não aprendem com as operações (não há treino de pesos). O que se treina são os
**parâmetros das estratégias determinísticas** (hoje: `grid` e `sma`), em três passos:

1. **`tune`**: procura parâmetros no passado e mantém-nos só se ganharem em dados que nunca viram;
2. **paper**: a config aceite corre no simulador ao lado da actual, cada uma na sua pasta de estado;
3. **`report`**: compara as duas por resultado real em paper. Só depois o maestro decide trocar.

## Como o `tune` decide

As velas são cortadas em `folds + 1` segmentos seguidos. Em cada fold *i*:

- todos os candidatos (`base` + todas as combinações de `search`) jogam no segmento *i* (**treino**);
- o melhor joga no segmento *i + 1* (**teste**), que nunca viu, ao lado da config actual.

A evidência **fora da amostra** é a soma destes testes fold a fold. Mede o procedimento de
re-afinação e nunca reutiliza um segmento que ajudou a escolher, o que evita o viés de seleção.
A config a usar é a escolha do último fold, a janela mais recente; `picked_in_folds` diz quão
estável foi essa escolha.

Pontuação: `retorno % − dd_weight × drawdown máximo %` (por defeito `dd_weight = 0.5`).

A config só é **aceite** se, fora da amostra, cumprir as três condições:

- ganha à config actual por **mais de `min_edge`** pontos (por defeito 0.1), porque uma diferença
  mínima é ruído e não motivo para trocar;
- o pior drawdown fica abaixo do `max_drawdown_pct` da própria config (grid) ou de 15% (sma);
- fecha pelo menos `min_trades` trades (por defeito 3), porque não negociar não é mérito.

Há também duas travas:

- **Travas de risco:** um candidato que não cabe nos limites no pior caso (`GridConfig.problems`)
  nunca é pontuado. O `tune` não pode propor uma config que o loop real recusaria. Se a própria
  config actual não couber, o resultado diz isso nas `notes`.
- **Recusa:** se não for aceite, o `--out` **não é escrito** e a config actual fica.

Cada resultado vai para `--log` (por defeito `.economia-trader/tune.jsonl`), com `bars_hash`
(impressão digital dos dados), intervalo temporal, candidatos, recusas, cada fold e o veredicto. Com
`--save-klines` / `--klines-file`, o mesmo `tune` repete-se exactamente sobre os mesmos dados.

## Comandos (na tua máquina, com rede)

```bash
cd oss/economia-trader && pip install -e .

# 1) treino: ~41 dias de velas de 1h da Bybit (dados públicos, sem chave), guardadas para repetir
economia-trader tune --exchange bybit --symbol BTCUSDT --interval 1h --limit 1000 \
  --save-klines ~/et/btc-1h.json --limits examples/limits.example.json \
  --space examples/tune.grid.example.json --out ~/et/grid.tuned.json --log ~/et/tune.jsonl
#    código 0 = aceite (escreveu grid.tuned.json); código 1 = recusado (diz porquê em "reasons")

# 2) paper lado a lado: a config actual e a afinada, cada uma na sua pasta, 1 tick por minuto
economia-trader grid --exchange bybit --mode paper --cash 1000 --limits examples/limits.example.json \
  --config examples/grid.example.json --state-dir ~/et/actual --every-min 1
economia-trader grid --exchange bybit --mode paper --cash 1000 --limits examples/limits.example.json \
  --config ~/et/grid.tuned.json --state-dir ~/et/afinada --every-min 1

# 3) comparar (e ver no painel)
economia-trader report --journal ~/et/actual/journal.jsonl
economia-trader report --journal ~/et/afinada/journal.jsonl
economia-trader dashboard --state-dir ~/et/afinada --out ~/et/afinada.html --refresh 60
```

O `config_hash` que o `tune` mostra é a impressão digital do ficheiro afinado. Em paper, o grid regista
a versão da config **já ancorada** no primeiro preço (com `lower`/`upper`), que é outro hash. Por isso
a comparação faz-se por pasta de estado, como acima.

## Limites honestos

- **O passado não garante o futuro.** O walk-forward reduz o risco de afinar ao ruído, mas não o
  elimina. Por isso o passo 2 (paper) é obrigatório antes de trocar.
- **O espaço de busca está limitado a 500 combinações.** Mais combinações aumentam a probabilidade de
  encontrar uma que ganhou por sorte.
- **Cada segmento corre sozinho.** O grid relativo ancora no primeiro preço do segmento, como o loop
  real ancora no primeiro preço que vê; a sma precisa de `slow` velas de aquecimento em cada segmento.
- **Não está ligado ao loop.** O `tune` nunca troca a config que está a correr; quem troca é o maestro,
  depois do paper.
- Testado só com séries sintéticas (`tests/test_tune.py`). Nesta sessão a rede bloqueia as exchanges,
  por isso nunca correu sobre velas reais.
