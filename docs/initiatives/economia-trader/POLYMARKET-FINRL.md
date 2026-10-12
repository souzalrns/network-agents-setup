# economia-trader: Polymarket (só leitura) e FinRL (só pesquisa)

> Decisões do maestro (2026-10-12, perguntas sim/não), sobre a lista de 12 ferramentas que ele trouxe:
> - **P-71 = A:** Polymarket só para ler probabilidades.
> - **P-72 = B:** FinRL só para pesquisa.
> - **P-73 = B:** Jev Trade não.
> - **P-74 = A:** agentic-inbox e hyperframes fora do financeiro.
> - **P-70 = B:** não se assina nada.
>
> PENDENCIAS §10.

## Os 12 da lista

| Ferramenta | Estado | Porquê |
|---|---|---|
| CCXT | **dentro** | Adapters Bybit/MEXC (#186) |
| Kronos | **dentro** | Confirmação por previsão (#192) |
| anthropics/financial-services | **dentro** | Plugins de pesquisa fundamental (P-66) |
| Polymarket (Gamma API, py-clob-client MIT) | **dentro, só leitura** | Este documento |
| FinRL (AI4Finance, MIT, `00f3596`) | **só pesquisa, fora do loop** | Este documento |
| NautilusTrader | fora | LGPL e motor completo; o ccxt resolve o que precisamos (`REUSE-AUDIT.md`) |
| Hummingbot | fora | Market making e arbitragem: não é a nossa estratégia |
| Backtrader | fora | GPL e parado; o nosso backtest cobre (sem look-ahead, testado) |
| VectorBT | fora | Commons Clause; o nosso backtest e a A/B do Kronos cobrem |
| Jev Trade (`jarrodwatts/jev-trader`, MIT) | fora (P-73) | Exige a chave paga da TypeSafe (o Jev envia dados para fora: já recusado) e faz market making numa DEX da Monad com chave privada |
| cloudflare/agentic-inbox (Apache) | fora do financeiro (P-74) | Cliente de email com IA na Cloudflare; a aprovação humana do trader já é o hitlwright |
| heygen-com/hyperframes (Apache) | fora do financeiro (P-74) | Vídeo; a skill de marketing `video` já o cita |

## Polymarket: probabilidades macro, só leitura

- **Fonte:** a API pública Gamma (`gamma-api.polymarket.com`), sem conta e sem chave. Usamos `urllib` da biblioteca
  padrão, só para esse host (qualquer outro é recusado).
- **O que entra:** mercados Sim/Não abertos cuja pergunta fala da Fed, de juros, de recessão, do CPI ou da
  inflação, com volume ≥ 50 000 USD.
  - O preço do "Sim" lê-se como a probabilidade do evento.
  - Guarda-se um retrato por mercado e por hora em `events.jsonl` (`kind: prediction_market`), com os 4 relógios.
- **Painel:** secção "Probabilidades macro (Polymarket, só leitura)".
- **Pausa por probabilidades** (`odds_block`, desligada por omissão e versionada): por exemplo
  `"odds_block": {"recession": "0.5"}` no `run.json` faz o tick não abrir nada enquanto o último retrato conhecido
  de um mercado de recessão estiver ≥ 50 %. As saídas continuam a correr. Regras:
  - só contam retratos que já tínhamos nessa altura e com menos de 48 h;
  - sem dados não há pausa: as probabilidades acrescentam cautela, não são uma porta para abrir.
- **Apostar fica fora:** precisa de carteira cripto e tem restrições legais em vários países.

```bash
economia-trader monitor --polymarket [--pm-keywords "fed,recession,cpi"] [--pm-min-volume 50000]
```

**Não verificado contra a API real:** o proxy deste ambiente bloqueia `gamma-api.polymarket.com`. Os testes usam a
forma de resposta documentada e a do cliente oficial `Polymarket/agents` (`outcomes` e `outcomePrices` como listas
em texto). A primeira corrida real é tua; se o formato tiver mudado, o monitor não grava nada em vez de gravar mal.

## FinRL: só pesquisa, num ambiente à parte

- **O que é:** agentes de aprendizagem por reforço (PPO, A2C, SAC…) treinados sobre preços.
- **Porque não entra no trader:** fixa versões antigas (`ccxt ^3`, `alpaca-trade-api`, ray, selenium, wrds) que
  não cabem com as nossas. Também tende a decorar o passado. Por isso nunca liga ao loop.
- **O que o economia-trader dá:** os nossos klines no formato do FinRL (`date, open, high, low, close, volume, tic`):

```bash
economia-trader export-klines --exchange alpaca --symbols SPY,QQQ,IWM --interval 1d --limit 1500 --out finrl.csv
python -m venv ~/venvs/finrl && ~/venvs/finrl/bin/pip install "git+https://github.com/AI4Finance-Foundation/FinRL@00f3596"
```

### Protocolo para um resultado contar

1. **Separar por tempo, sem baralhar:**
   - treino: os primeiros 60 %;
   - validação: os 20 % seguintes;
   - teste: os últimos 20 %, que só se abrem **uma vez**.
2. **Mesmos custos que o nosso backtest:**
   - comissões (`fee_rate` dos limites);
   - slippage;
   - execução na abertura seguinte.
3. **Comparar no mesmo período de teste com:**
   - comprar e manter;
   - `sma_cross` (`economia-trader backtest`);
   - a versão com Kronos.
4. **Repetir com 5 sementes:** se o resultado mudar de sinal entre sementes, não há resultado.
5. **Só um resultado que sobreviva a 1-4 vira uma decisão.** Por exemplo, usar a política do FinRL como mais uma
   confirmação, nunca como quem dá a ordem. Até lá não toca no paper nem no real.
