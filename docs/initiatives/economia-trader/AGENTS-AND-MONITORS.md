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

## 3. Decisão D6: que modelos para os agentes

A camada "quick" serve os analistas, investigadores, debatedores e o trader: são cerca de 20 a 30
chamadas por análise. A camada "deep" serve os gestores e a decisão final: são 2 chamadas por
análise. O tecto `max_runs_per_day` (3 por defeito) limita o total a umas 90 chamadas quick e 6 deep
por dia.

**Decisão em vigor (maestro, 2026-10-17, revê a P-56): Gemini no plano grátis, nas duas camadas.**

| Configuração | Quick | Deep | Chaves | Custo |
|---|---|---|---|---|
| **Padrão** `examples/tradingagents.example.json` | Gemini 3.5 Flash Lite | Gemini 3.8 Flash | `GOOGLE_API_KEY` | **0**, dentro das quotas do plano grátis |
| Opcional `examples/tradingagents.grok-free.example.json` | Gemini 3.5 Flash Lite | **Grok `:free`** no OpenRouter (`x-ai/grok-4-fast:free`) | `GOOGLE_API_KEY` + `OPENROUTER_API_KEY` (conta grátis) | **0**, mas só enquanto existir uma variante grátis do Grok |
| Opcional `examples/tradingagents.grok.example.json` | Gemini 3.5 Flash Lite | **Grok 4.6** (xAI) | `GOOGLE_API_KEY` + `XAI_API_KEY` | Só as 2 chamadas deep por análise são pagas, por token |
| Antiga P-56 (substituída) | Gemini 3.5 Flash Lite | Claude Sonnet 5 | Google + Anthropic | Pago na camada deep |

As duas configurações foram verificadas com o TradingAgents no commit fixado (`1394a3f`): os modelos
estão no catálogo dele e o grafo constrói-se sem avisos. A camada deep do Grok usa o endpoint
oficial `https://api.x.ai/v1`. Os testes (`tests/test_llm_examples.py`) garantem que os exemplos
não têm chaves e que o padrão só usa o Google.

**Limites do plano grátis do Gemini:**
- O Google não publica números fixos. As quotas de cada projecto aparecem no Google AI Studio.
- Os números da comunidade (cerca de 500 pedidos por dia no Flash Lite e cerca de 20 no Flash)
  são indicativos.
- Se a quota acabar, o TradingAgents falha e a entrada é vetada. O agente nunca entra sem a
  segunda opinião.
- No plano grátis, o Google pode usar os pedidos para melhorar os produtos. Os pedidos só levam
  tickers, notícias e números públicos, nunca chaves ou dados pessoais.

**Grok grátis (decisão do maestro, 2026-10-17, opção A):**
- O Grok não tem um plano grátis estável. No OpenRouter aparecem às vezes variantes `:free`, que
  são promoções temporárias, com limites apertados e pedidos normalmente registados pelo
  fornecedor.
- Antes de usar o `grok-free`, confirma em openrouter.ai (modelos, filtro de preço grátis) que o
  modelo existe. Se tiver outro nome, troca o `deep_think_llm`.
- Se a variante desaparecer a meio, o analista falha e a entrada é vetada. Perde-se a segunda
  opinião, nunca dinheiro.
- Verificado com o TradingAgents `1394a3f`: o grafo constrói-se pelo endpoint
  `https://openrouter.ai/api/v1`.

### Grok: porque é opcional e não o padrão

- **Custa dinheiro.** A API da xAI é paga por token. A nossa leitura das páginas oficiais em
  setembro de 2026 não encontrou nenhum crédito grátis garantido. Há relatos de créditos
  promocionais, mas é preciso confirmar na consola da xAI.
- **A evidência de que "negoceia melhor" é mista.** No Alpha Arena (nof1):
  - na época 1 (cripto, out–nov 2025), o Grok 4 ficou em 5.º de 6, com perdas de 45% a 58%;
  - na época 1.5 (ações dos EUA, dez 2025), o Grok 4.20 ganhou, com +12% em 14 dias.

  São janelas de 2 a 3 semanas, e não chegam para provar que um modelo é melhor.
- **No nosso desenho, o LLM não negoceia.** Só confirma ou veta uma entrada que a triagem já
  escolheu. O tamanho da posição, os stops e a execução são deterministas. O que interessa medir
  é se os vetos dele evitam perdas, não o retorno que ele teria sozinho.

**Como comparar com números nossos, antes de pagar:**
1. Correr duas pastas de estado em paper, uma com cada configuração, com o mesmo fluxo de
   entrada.
2. Ao fim de 2 semanas, comparar com `economia-trader report` (resultado por versão) e com os
   tokens por modelo no diário.

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

## 5. Ver o que os agentes fazem (painel, escritório, traces)

- **Painel** (`economia-trader dashboard`): uma página HTML estática gerada a partir dos ficheiros
  que o trader já escreve. Mostra posições, resultados por versão, releases macro, opiniões do
  analista com tokens, rejeições, bloqueios, auto-kills, notícias e as últimas decisões. Funciona
  claro e escuro, no telemóvel e no computador. Exemplo: `dashboard-example.png`.
- **Escritório pixel** (`economia-trader office`): os 5 agentes (monitor, triagem, analista,
  risco, executor) aparecem como personagens no **Star-Office-UI**
  (`ringhyacinth/Star-Office-UI`, `f29c107`). Usa o protocolo do backend dele: `/join-agent`
  uma vez e depois `/agent-push`. **Licença:** o código é MIT, mas as **imagens são só para uso
  não comercial**. Serve para uso pessoal; num produto é preciso trocar as imagens.
- **Traces** (Langfuse, opcional): com `LANGFUSE_PUBLIC_KEY`/`LANGFUSE_SECRET_KEY` definidas, cada
  passo do TradingAgents fica no Langfuse (MIT, self-hostable). Sem as chaves não corre nada.
- **OpenStock** (`Open-Dev-Society/OpenStock`, `d890d91`, **AGPL-3.0**): um terminal de mercado
  (gráficos TradingView, heatmap, watchlist, alertas, sentimento) usado **ao lado** do painel,
  sem modificações (instância própria ou a deles). `dashboard --openstock-url` liga cada ativo a
  `<openstock>/stocks/<SYM>`. Ligar por URL não cria obrigações AGPL. **Não** se copia código dele
  para o `economia-trader` (MIT). Não negoceia: só observa.
- **Adanos** (a API de sentimento que o OpenStock usa: Reddit, X, notícias, Polymarket): está **em
  avaliação** (custo, termos, fiabilidade) como fonte extra, ao lado do FinBERT (P-59). Só se
  integra depois desse veredicto.
