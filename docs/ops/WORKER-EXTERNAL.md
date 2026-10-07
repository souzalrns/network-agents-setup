# Worker do modo `external` (AU-23)

> **Estado (2026-10-01):** implementado, testado com o Gemini falso (17 testes em `runner/tests/test_external_worker.py`) e **validado com o Gemini real (B1, feito pelo maestro a 2026-10-01)**: o `seo-article-demo` correu do início ao fim, 4 chamadas, 13 130 tokens. Ver "Primeiro run real (B1)".

## O que faz

Antes, o `plan_runner` em `--mode external` escrevia `pending_steps/<id>/request.json` e parava em `waiting_external` à espera de um worker que não existia (`runner/plan_runner/engine.py`, ramo `mode == "external"`). O módulo `runner/plan_runner/external_worker.py` é esse worker. Para cada passo:

1. **Lê** o `request.json` e o `AGENT.md`/`SKILL.md` que o executor copia para o directório do passo. Junta:
   - a directiva de grounding (`agents/_shared/grounding.directive.md`);
   - os `inputs` do passo; sem eles, os artefactos dos passos de que depende;
   - o `knowledge_context.md` (S9) e o `CLIENT_MEMORY.md` (S30), se existirem.
2. **Chama** o Gemini: `generateContent` do `gemini-flash-lite-latest`, que hoje responde como `gemini-3.5-flash-lite`.
   - O modelo muda com `AGENT_MODEL`, a mesma variável do MCP.
   - **D5 (2026-10-03):** um passo com `model_tier: planner | executor | verifier` usa o modelo desse tier em `config/model-tiers.yaml` (`runner/plan_runner/model_tiers.py`). Tier a `null` (omissão) ou passo sem tier = o modelo normal (`AGENT_MODEL` ou `gemini-flash-lite-latest`); tier desconhecido = erro antes de chamar. O modelo usado fica no ledger e no `result.json` (`meta.model`, `meta.model_tier`).
   - A chave vai no header `x-goog-api-key`, nunca no URL.
   - Artefactos `.json` pedem `responseMimeType: application/json` e o JSON é validado antes de ser aceite.
3. **Escreve** o `result.json` no formato que `executor.py` já lê: `{ok, detail, artifact_content}`. Junta-lhe um `meta` com o modelo, os tokens e o `responseId`. O executor escreve o artefacto em `output_artifact`.
4. **Regista os tokens** no ledger J6, com a mesma linha que a tabela `token_usage` do `agent-network-mcp`:
   - **sempre** em `<run>/token_usage.jsonl`. Esta cópia local guarda também o `run_id` original do runner, o `step_id` e o que aconteceu do lado remoto;
   - **no Supabase só** se `SUPABASE_URL` **e** `SUPABASE_SERVICE_ROLE_KEY` estiverem definidas (POST no PostgREST com o `service_role`, como o MCP);
   - `call_kind = 'agent'`;
   - `agent_id` = o `id:` do agente (ex.: `marketing.research`);
   - `run_id` = um uuid5 estável do run do runner. A coluna é `uuid` e o runner usa `run_xxxxxxxxxx`.
   - **Gravar nunca faz falhar o passo**, a mesma regra do MCP.
5. **Respeita o HITL:**
   - o motor já pára antes de um passo com `human_gate`, por isso o worker nunca é chamado para ele;
   - se for chamado directamente, recusa (`HumanGateBlocked`) um passo com `human_gate` e qualquer passo de um run em `paused_human_gate`;
   - a decisão continua a ser humana: `hitl-decisions.jsonl` ou `resume --decision`.

**Falhas** (rede, HTTP 4xx/5xx, quota, resposta vazia, JSON inválido) **não escrevem `result.json`**:
- o motivo fica em `pending_steps/<id>/worker_error.json`, em `status.json` (`worker_error`) e no evento `step_waiting_external`;
- o run fica em `waiting_external`;
- tentar outra vez = `resume`;
- uma chamada que chegou ao Gemini e voltou vazia fica registada no ledger, porque gastou tokens.

Sem dependências novas: usa o `httpx`, que já está em `runner/requirements.txt` e é usado pelo `embedder.py`.

## Como correr

Pré-requisitos: `cd runner`, as dependências de `requirements.txt` e uma chave gratuita do Gemini (aistudio.google.com/apikey).

```bash
export GEMINI_API_KEY=...            # nunca commitar
# opcional: ledger também no Supabase (projecto agent-network-memory)
# export SUPABASE_URL=...  SUPABASE_SERVICE_ROLE_KEY=...
```

### Correr um plano com o worker (engine native)

```bash
python -m plan_runner run ../docs/orchestration/marketing/templates/examples/seo-article-demo.plan.yaml \
  --mode external --worker gemini --out ../pilots/run-worker-seo
```

- O run executa os passos com o Gemini até ao primeiro `human_gate` (ou até ao fim).
- O `--out` tem de ficar dentro de `pilots/` (guard do motor). `pilots/run-worker-*/` está no `.gitignore`.

```bash
# Rever os artefactos e decidir
python -m plan_runner resume ../pilots/run-worker-seo --decision approve   # continua com o mesmo worker
```

O `status.json` guarda `"worker": "gemini"`, por isso o `resume` continua com o mesmo worker sem flag. O `resume --worker none` volta ao contrato antigo (esperar por `result.json`). O `resume --worker gemini` liga o worker num run que arrancou sem ele.

### Run já parado em `waiting_external` (qualquer engine, incluindo langgraph)

```bash
python -m plan_runner.external_worker ../pilots/<run>            # executa só o passo pendente
python -m plan_runner.external_worker ../pilots/<run> --resume   # e depois retoma (engine native)
```

| Código de saída | Significado |
|---|---|
| 0 | Passo executado |
| 1 | Erro (sem chave, HTTP, run fora de `waiting_external`) |
| 2 | Bloqueado por HITL |

### Primeiro run real (B1): FEITO a 2026-10-01

Corrido pelo maestro: `seo-article-demo.plan.yaml`, `--mode external --worker gemini`, engine `native`. Correu do início ao fim e o estado final é `done`.

| Passo | tokens_in | tokens_out | tokens_total | Input injectado (artefacto completo) |
|---|---:|---:|---:|---|
| research | 1 426 | 467 | 1 893 | — |
| seo_brief | 2 189 | 1 226 | 3 415 | `01-research.md` (dependência, sem `inputs`) |
| copy | 2 270 | 1 389 | 3 659 | `02-seo-brief.json` |
| critic | 3 819 | 344 | 4 163 | `02-seo-brief.json` + `03-copy.md` |
| **Total** | **9 704** | **3 426** | **13 130** | 4 chamadas |

**Leitura:**
- O `tokens_in` é ~1–1,5k de base (AGENT.md + SKILL.md + grounding + pedido) **mais os artefactos injectados completos**.
- O passo que mais cresce é o `critic` (+68%), que recebe dois artefactos.
- O `copy` quase não cresce (+4%): recebe um só, e a skill dele é mais curta.
- A optimização (injectar resumos em vez de artefactos completos) é um item do PLANO-DE-ACAO.

### Repetir um run real (passo do DEV)

1. Com `GEMINI_API_KEY` e **sem** `SUPABASE_*`, correr um plano de 1 passo, ou o `seo-article-demo`, que faz 4 chamadas até ao gate.
2. Confirmar:
   - em `pilots/<run>/token_usage.jsonl`: `status: ok`, `model_version: gemini-3.5-flash-lite` e tokens não nulos;
   - em `pending_steps/<id>/result.json`: `ok: true`.
3. Só depois, se quiseres o ledger central: exportar `SUPABASE_*` e repetir. Ver em `token_usage`:

```sql
select created_at, agent_id, call_kind, model_version, tokens_in, tokens_out, tokens_total, status
from token_usage where call_kind = 'agent' and agent_id like 'marketing.%'
order by created_at desc limit 10;
```

> Nota: no Supabase, a tabela `token_usage` vive no projecto do MCP (`agent-network-memory`). A configuração está em [TOKEN-LEDGER.md](https://github.com/souzalrns/agent-network-mcp/blob/main/docs/ops/TOKEN-LEDGER.md) do `agent-network-mcp`. As linhas do worker distinguem-se pelos `agent_id` dos agentes deste repo (`marketing.*`, `design.*`…) e por `run_id`s que não vêm do MCP.

## Optimização de contexto (B1-bis, 2026-10-01)

> **Estado:** implementado (modo `opt`, a omissão) e testado offline: 18 testes em `runner/tests/test_context_opt.py`.
> - **Run real (B1-bis-R, maestro, 2026-10-01): −2,6%, mas o run "opt" correu com o prompt `legacy`.** Os prompts-base dos dois runs são idênticos token a token em todos os passos, e o código actual corta 16–34% dos caracteres de cada prompt-base. O −2,6% é variância da saída do modelo, não efeito do `opt`.
> - **Run real válido (B1-bis-R2, 2026-10-03, modo `opt` verificado): −22%** (12 998 → 10 136). research −20%, seo_brief +9% (gera o resumo), copy −31%, critic −41%. Ver "Medição real (B1-bis-R2)".
> - **`opt` continua a omissão (decisão do maestro), agora confirmada por medição real.** Com as saídas do research e do copy fixadas nos valores do legacy, o ganho atribuível ao `opt` é ~**−16%** (10 914), em linha com a projecção. Os outros ~6 pontos vêm de o copy ter escrito menos (1 amostra).
> - A meta de <9k passou para o item próprio B1-bis-C (PLANO item 12).

### Diagnóstico: onde estavam os 13 130 tokens do B1
O `tokens_in` de cada passo é o prompt-base mais os artefactos injectados. A calibração dá 3,29–3,50 caracteres por token nos 4 passos, o que confirma a decomposição.

| Componente | Tokens | % |
|---|---:|---:|
| Prompt-base (AGENT.md + SKILL.md + grounding + pedido) | 5 396 | 41% |
|   …grounding completo, repetido em cada passo | ~1 600 | 12% |
|   …frontmatter YAML e secções de documentação | ~900 | 7% |
| Artefactos injectados completos | 4 308 | 33% |
| Saídas | 3 426 | 26% |

O contexto acumulado conta, mas o **prompt-base pesa mais** (41% vs 33%). A subida também não é de +50% por passo: o `copy` sobe +4%, porque só recebe 1 input.

### Técnicas: escolhidas e descartadas

| # | Técnica | Decisão | Porquê |
|---|---|---|---|
| 1+2+5 | Artefacto dual + política de injecção + pin | **Sim, num só mecanismo** (`plan_runner/context_policy.py`) | **Pin:** o último input de cada passo vai completo; os anteriores vão como resumo. **Resumo:** gerado pelo passo produtor **na mesma chamada** (0 chamadas extra), com schema fixo (factos com fonte, keywords, estrutura, tom, restrições, decisões), a partir do próprio artefacto (nunca resumo de resumo), e **só quando algum passo o consome como resumo**. Sem resumo, o consumidor recebe o completo. **Override no plano:** `context: {full: [...], summary: [...]}` |
| 4 | Grounding por área | **Sim** | `grounding: slim` no `areas.yaml` em marketing, docs e research (`agents/_shared/grounding.slim.md`, as mesmas 4 regras). Omissão `full`. **O E7 recusa `slim` em áreas com `hitl: required`**, por isso finance, legal e security não podem perder a directiva completa |
| extra | Sem frontmatter nem secções de documentação | **Sim** (não estava na lista) | Os metadados YAML e as secções para humanos/runner (notas de migração, ponteiros "Skill", camadas de memória, handoff, "quando usar", trigger, knowledge ref) não são instruções para o modelo. Lista fechada em `DOC_ONLY_SECTIONS`; tudo o que muda comportamento fica (Enforcement Note, Não usar, Anti-padrões, Red Flags…). O que sai fica registado em `meta.context.dropped_sections` |
| extra | JSON injectado compacto | **Sim** | O mesmo conteúdo sem indentação |
| 3 | Tectos de output por tipo | **Não** | No B1 todos os passos já estavam dentro ou à beira dos tectos propostos (research 467 < 600, brief 1226 ≈ 1200, copy 1389 < 1500, critic 344 < 400): poupa ~0 e traz risco de JSON truncado. O travão de custo é o tecto por run ([BUDGET.md](./BUDGET.md)) |
| 6 | Cache de prefixo | **Não** (não muda a métrica) | Os tokens em cache continuam no `promptTokenCount`; só mudam a fatura. A ordem do prompt já é estável (system → user) |

`PLAN_RUNNER_CONTEXT=legacy` repõe o prompt anterior, para A/B e rollback. Cada `result.json` tem `meta.context` com a política, o grounding, cada input (modo e tamanho) e o estado do resumo.

### Medição real (B1-bis-R2, 2026-10-03, run do maestro, modo `opt` verificado)

Plano `seo-article-demo`, `--worker gemini` (`flash-lite`), run `opt` repetido com a verificação de "Medir a sério". O `legacy` é o do B1-bis-R, que esse correu de facto em `legacy`.

**Modo: MODO OPT CONFIRMADO.** `meta.context.policy = "opt"` nos 4 passos e `02-seo-brief.summary.md` existe. Este run é uma medição válida, ao contrário do braço "opt" do B1-bis-R.

Números do `pilots/run-opt2/token_usage.jsonl` do maestro (`usageMetadata` real):

| Passo | Legacy in | Opt in | Δ in | Legacy out | Opt out | Δ out | Legacy total | Opt total | Δ total |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| research | 1426 | 911 | −36% | 511 | 645 | +26% | 1937 | 1556 | **−20%** |
| seo_brief | 2233 | 2064 | −8% | 1130 | 1591 | +41% | 3363 | 3655 | **+9%** |
| copy | 2174 | 1591 | −27% | 1425 | 902 | −37% | 3599 | 2493 | **−31%** |
| critic | 3759 | 2091 | −44% | 340 | 341 | 0% | 4099 | 2432 | **−41%** |
| **TOTAL** | **9592** | **6657** | **−31%** | **3406** | **3479** | **+2%** | **12 998** | **10 136** | **−22%** |

#### Decomposição: o que é do `opt` e o que é variância da saída

O `tokens_in` de cada passo é o prompt-base mais os inputs injectados, e cada input vale o `tokens_out` do passo que o produziu (análise do B1-bis-R):

| Passo | Legacy | Opt | Δ | O que mede |
|---|---:|---:|---:|---|
| research (só prompt-base) | 1426 | 911 | **−515 (−36%)** | corte do prompt-base (frontmatter, secções de documentação, grounding `slim`) |
| seo_brief, prompt-base (in − research out) | 2233 − 511 = 1722 | 2064 − 645 = 1419 | **−303 (−18%)** | corte do prompt-base |
| critic, prompt-base + brief (in − copy out) | 3759 − 1425 = 2334 | 2091 − 902 = 1189 | **−1 145 (−49%)** | prompt-base + **brief em resumo** em vez de completo |
| seo_brief out | 1130 | 1591 | **+461** | **custo do resumo** que o seo_brief escreve para o critic (mais variância) |
| research out | 511 | 645 | +134 | variância (o research não gera resumo); entra também no `tokens_in` do seo_brief |
| copy out | 1425 | 902 | **−523** | variância provável: o modelo escreveu um artigo mais curto. Conta 2×, porque também reduz o `tokens_in` do critic |

**Ganho atribuível ao `opt`.** Fixando as saídas do research (511) e do copy (1425) nos valores do legacy, e mantendo tudo o resto como medido, o total fica em **10 914, −16%** contra os 12 998. É o número que a projecção dava (−16%).

Os ~6 pontos que faltam até aos −22% medidos vêm do copy mais curto. Com uma amostra de cada lado não se distingue se isso é variância ou efeito do brief compacto (o copy recebe o brief inteiro, só sem indentação). Só repetições o dizem.

#### Conclusão

- **O `opt` compensa:** −22% medido (−2 862 tokens) e ~**−16% atribuível ao mecanismo** com as saídas normalizadas. Fica a omissão, agora com dados.
- **De onde vem o ganho:**
  - **do prompt-base, em todos os passos:** −515 no research, −303 no seo_brief, e o copy também desce na entrada (−27%);
  - **do resumo no critic:** −1 145 na parte prompt-base + brief da entrada do critic.
- **O que custa:** o seo_brief escreve +461 de saída (o resumo). Recupera-se 2,5× no critic.
- **A entrada do critic cai 44% (3759 → 2091).** Desses −1 668 tokens, −1 145 são do `opt` e −523 vêm de o copy ser mais curto.
- **A hipótese "o `opt` só compensa em planos com 4+ passos" fica refutada:** o 1.º passo (research) já corta 36% na entrada. Só os resumos dependem de haver um passo que consuma um artefacto que não é o seu último input. Em planos mais longos o ganho deve crescer (a projecção de 8 passos dá −31%), mas isso é projecção, não medição.
- **A projecção (−16%) acertou no ganho do mecanismo**, mas não previu a variância das saídas. Por passo previa: research −26%, seo_brief +1%, copy −11%, critic −31%. A lição de método mantém-se: decidir com `usageMetadata` real, e separar entrada e saída antes de atribuir causas.
- **Só o seo_brief piora no total (+9%):** é o passo que escreve o resumo extra para o critic, na mesma chamada. É o custo previsto do mecanismo (`context_policy.needs_summary`).
- **Meta <9k:** faltam **1 136 tokens** (10 136 contra 9 000). O caminho continua a ser o B1-bis-C (PLANO item 12), que fica para quando houver ordem.
- **Análise do Grok (parceiro de design, 2026-10-03):**
  - ~10k em `opt` é saudável, e o critic deixou de ser o buraco do `tokens_in`;
  - **não abrir o B1-bis-C só porque não está <9k**: o ganho real já apareceu, e o patamar dos 13k ficou para trás.

**Limite deste registo:** 1 run por braço. A separação entre o efeito do `opt` e a variância das saídas usa a decomposição acima. Uma 2.ª repetição do `opt` diria quanto do copy mais curto é ruído.

### Medição real (B1-bis-R, 2026-10-01, run do maestro)

Plano `seo-article-demo`, `--worker gemini` (`flash-lite`), os dois comandos de "Medir a sério". Números do `token_usage.jsonl` de cada run (`usageMetadata` real):

| Passo | Legacy in | Legacy out | "Opt" in | "Opt" out | Leg total | "Opt" total | Δ |
|---|---:|---:|---:|---:|---:|---:|---:|
| research | 1426 | 511 | 1426 | 564 | 1937 | 1990 | +3% |
| seo_brief | 2233 | 1130 | 2286 | 1131 | 3363 | 3417 | +2% |
| copy | 2174 | 1425 | 2175 | 1180 | 3599 | 3355 | −7% |
| critic | 3759 | 340 | 3515 | 379 | 4099 | 3894 | −5% |
| **TOTAL** | **9592** | **3406** | **9402** | **3254** | **12 998** | **12 656** | **−2,6%** |

Critic `tokens_in`: 3759 → 3515 (−6,5%; projectado −33%).

#### Análise: o run "opt" não exercitou o modo `opt`

Separando o `tokens_in` em prompt-base + inputs injectados (cada input conta o `tokens_out` do passo que o produziu, no mesmo run):

| Passo | Inputs | Base legacy | Base "opt" | Corte de caracteres do `opt` no código actual |
|---|---|---:|---:|---:|
| research | (nenhum) | 1426 | **1426** | 5004 → 3312 (**−34%**) |
| seo_brief | research | 2233 − 511 = **1722** | 2286 − 564 = **1722** | 5827 → 4900 (−16%) |
| copy | seo_brief | 2174 − 1130 = **1044** | 2175 − 1131 = **1044** | 3619 → 2464 (−32%) |
| critic | seo_brief + copy | 3759 − 1130 − 1425 = **1204** | 3515 − 1131 − 1180 = **1204** | 4040 → 2869 (−29%) |

A coluna dos cortes vem de construir os 4 prompts com o código actual nos dois modos (worker real, Gemini falso; mesmo método da `token_projection.py`, aqui só a contar caracteres e sem estimar tokens).

Três factos, cada um suficiente, mostram que o run "opt" usou o prompt `legacy`:

1. **Prompt-base idêntico ao token em todos os passos**, incluindo o `research`, que não tem inputs. Com o `opt` activo, o prompt do `research` perde 34% dos caracteres (sem frontmatter, sem secções de documentação, grounding `slim`). Isso não pode dar exactamente 0 tokens de diferença.
2. **O critic recebeu o brief completo.** A base 1204 só fecha somando o brief **inteiro** (1131) ao copy (1180). No `opt`, o brief entra no critic como resumo (~300 tokens).
3. **O seo_brief não gerou resumo:** saída 1131 contra 1130. No `opt`, o seo_brief escreve o resumo para o critic na mesma chamada (+~200–300 tokens de saída).

**Logo, os −2,6% são variância da saída**, propagada pelos inputs:
- o copy escreveu 1180 em vez de 1425 (−245), e esses mesmos −245 aparecem no `tokens_in` do critic;
- o research escreveu +53, que aparecem no `tokens_in` do seo_brief.

Causa provável, por confirmar no `result.json` do run (ver "Medir a sério"):
- em PowerShell, `$env:PLAN_RUNNER_CONTEXT="legacy"` fica na sessão e aplica-se ao comando seguinte (em bash, o prefixo `VAR=x cmd` só vale para esse comando);
- ou o run correu com um checkout anterior ao #45.

#### O padrão "research e seo_brief gastam mais no opt" (hipótese do maestro)

> **Refutado pelo B1-bis-R2** (`opt` verificado): o research gasta −20% e só o seo_brief gasta mais (+9%, o resumo). A análise abaixo, feita sobre o B1-bis-R, previa isto.

**Não confirmado: os dados não o mostram, e o mecanismo diz o contrário.**

- **research +3%:** o `tokens_in` é igual (1426 = 1426). A diferença está toda na saída (511 → 564). Não há overhead nenhum do mecanismo. No `opt` real, o research **não gera resumo** (ninguém o consome como resumo: o seo_brief recebe-o como pin) e o prompt encolhe 34%. O research é, pelo contrário, o passo onde o `opt` deve poupar mais, em proporção.
- **seo_brief +2%:** a entrada sobe +53, que é exactamente a saída extra do research. A saída fica igual (1131). No `opt` real, este é o único passo com overhead (gera o resumo do brief), compensado pelo corte de 16% do prompt-base.
- **copy e critic:** os ganhos (−7%, −5%) vêm do copy mais curto (1180 contra 1425), não de resumos.

**"O `opt` só compensa em planos com 4+ passos"** fica registado como **hipótese não verificada**, com esta contra-evidência:
- 3 das 4 alavancas do `opt` (frontmatter, secções de documentação, grounding `slim`) cortam o prompt-base de **todos** os passos, incluindo o primeiro. Não dependem do comprimento do plano;
- só a alavanca de resumos depende de haver 3+ passos encadeados (um passo que consome um artefacto que não é o seu último input).

A medição que decide: o run `opt` repetido, com a verificação de "Medir a sério".

**Decisão (maestro, 2026-10-01):** `opt` continua a omissão.

### Lição de método: medir com usage real, não com proxies de caracteres

> **Correcção (2026-10-01, depois da tabela por passo):** a comparação "−16% projectado vs −2,6% real" **não é válida**, porque o run "opt" não exercitou o `opt` (ver acima). As causas abaixo continuam a ser **riscos** de qualquer projecção por caracteres, e a regra mantém-se. Mas não ficou demonstrado que a projecção errou, nem por quanto.

Riscos de uma projecção por caracteres:

1. **Caracteres ≠ tokens, sobretudo no que se corta.**
   - A projecção não usou ÷4: usou caracteres por token **calibrados no B1** (3,29–3,50, média do prompt inteiro).
   - Mas aplicou essa média ao texto **cortado**: frontmatter YAML, cabeçalhos, tabelas, a directiva de grounding.
   - Esse texto tem outra densidade no tokenizer do Gemini. Se o que saiu tem mais caracteres por token do que a média, poupa muito menos tokens do que os caracteres sugerem.
   - Um rácio fixo é um proxy, não o tokenizer.
2. **A saída não foi medida, foi assumida.**
   - A projecção fixou as saídas nos valores do B1, mais 300 tokens de resumo.
   - No run real, o modelo pode escrever mais (ou o resumo sair maior) com o prompt novo. Isso come o ganho na entrada.
3. **O próprio legacy reproduzir o B1 (+0,4%) não validava nada sobre o opt.** Era circular: a calibração foi feita nesses mesmos números.
4. **(Aprendido no B1-bis-R)** Um A/B real também engana se não se verificar que cada braço correu no modo pretendido. Cada run tem de provar o seu modo (`meta.context.policy` no `result.json`) antes de os números entrarem numa tabela.

**Regra a partir daqui** (vale para o B1-bis-C e para qualquer optimização de tokens):
- **Só se decide com `usageMetadata` real** (`promptTokenCount`, `candidatesTokenCount`).
- Para medir só a entrada sem gerar texto, há o endpoint `models/{model}:countTokens` da API Gemini. Dá a contagem exacta do tokenizer, e é uma alternativa barata a um run completo por cada hipótese (pendente: ver OPEN-ITEMS).
- A `token_projection.py` fica no repo só como ferramenta exploratória, marcada como **não usar para decisões**.

### Antes/depois: `seo-article-demo` (PROJECÇÃO; o real, B1-bis-R2, deu −22% contra −16% projectado)

| Passo | in antes | out antes | total antes | in depois | out depois | total depois | Δ total |
|---|---:|---:|---:|---:|---:|---:|---:|
| research | 1430 | 467 | 1897 | 946 | 467 | 1413 | −26% |
| seo_brief | 2201 | 1226 | 3427 | 1926 | 1526 | 3452 | +1% |
| copy | 2284 | 1389 | 3673 | 1896 | 1389 | 3285 | −11% |
| critic | 3843 | 344 | 4187 | **2561** | 344 | 2905 | −31% |
| **TOTAL** | | | **13 184** | | | **11 055** | **−16%** |

- **"Antes" é a projecção do modo `legacy`:** reproduz o B1 real (13 130) com +0,4% de erro, e é essa a verificação da calibração.
- **Critic `tokens_in`: −33%** (meta 30–50% ✓).
- **seo_brief:** +300 de saída para gerar o resumo do brief, que o critic recebe no lugar do brief completo.
- **Inputs por passo** (opt):
  - seo_brief ← `01-research.md` completo (é o pin);
  - copy ← `02-seo-brief.json` completo e compacto (pin);
  - critic ← `02-seo-brief.json` em resumo + `03-copy.md` completo (pin).

**Extrapolação, plano sintético de 8 passos** (agentes reais de marketing; pior caso de acumulação, com cada passo a declarar **todos** os anteriores; saídas de ~900 tokens):
- legacy **41,3k** → opt **28,3k (−31%)**;
- o `tokens_in` do 8.º passo cai 54% (7 174 → 3 293);
- o crescimento passa de ~+900 por passo (um artefacto) para ~+300 (um resumo).

### Qualidade (o que os testes garantem)
- O critic recebe **a checklist inteira da skill**, **o copy completo** (é o alvo) e o brief em bullets estruturados (keywords, estrutura, restrições, decisões).
- O copy recebe **o brief inteiro** (só sem indentação).
- **HITL:** pára nos mesmos gates nos dois modos. Não houve fusão de passos nem chamadas extra.
- Em finance, legal e security o grounding fica completo, e isso é garantido pelo E7.
- **Falta:** a qualidade real do texto só se vê num run real (ver abaixo).

### Porque não chega aos 9k (análise sobre a projecção; o real, B1-bis-R2, ficou em 10 136, a 1 136 da meta)
Depois do `opt` ficam ~4,2k de prompt-base (conteúdo das skills e dos agentes), ~3,7k de saídas e ~3,3k de inputs. A maior parte destes é o copy completo para o critic, que a crítica precisa. As alavancas que restam mexem em conteúdo:

| Alavanca adicional | Total projectado |
|---|---:|
| (opt, sem perda de conteúdo) | 11 055 (−16%) |
| A: o copy recebe o **resumo** do brief (override `context` no plano) | 10 182 (−22%) |
| B: resumos de 150 tokens em vez de 300 | 10 755 (−18%) |
| C: brief com alvo de 700 tokens | 10 025 (−24%) |
| A+B+C | **9 206 (−30%)** |

Nem tudo junto chega a <9k. O que faltaria era o critic criticar um resumo do copy, e isso não se propõe. Para <9k é preciso encurtar o próprio prompt-base (as skills) ou as saídas, num item separado.

### Medir a sério (passo do maestro)
```bash
cd runner
PLAN_RUNNER_CONTEXT=legacy python -m plan_runner run ../docs/orchestration/marketing/templates/examples/seo-article-demo.plan.yaml \
  --mode external --worker gemini --out ../pilots/run-worker-ctx-legacy
python -m plan_runner run ../docs/orchestration/marketing/templates/examples/seo-article-demo.plan.yaml \
  --mode external --worker gemini --out ../pilots/run-worker-ctx-opt          # opt = omissão
# comparar token_usage.jsonl dos dois runs e ler os artefactos 03-copy.md e 04-critic.json lado a lado
```

**PowerShell (Windows).** `$env:` persiste na sessão, por isso tem de se limpar antes do run `opt`:
```powershell
cd runner
$env:PLAN_RUNNER_CONTEXT = "legacy"
python -m plan_runner run ..\docs\orchestration\marketing\templates\examples\seo-article-demo.plan.yaml --mode external --worker gemini --out ..\pilots\run-worker-ctx-legacy
Remove-Item Env:PLAN_RUNNER_CONTEXT          # <- sem isto, o run seguinte também é legacy
python -m plan_runner run ..\docs\orchestration\marketing\templates\examples\seo-article-demo.plan.yaml --mode external --worker gemini --out ..\pilots\run-worker-ctx-opt
```

**Verificar o modo de cada run ANTES de comparar números** (obrigatório desde o B1-bis-R):
- `pilots/run-worker-ctx-opt/pending_steps/<passo>/result.json` → `meta.context.policy` tem de ser `"opt"` em todos os passos (e `"legacy"` no outro run);
- `pilots/run-worker-ctx-opt/artifacts/02-seo-brief.summary.md` tem de existir;
- no `opt`, o `meta.context.inputs` do `critic` mostra `02-seo-brief.json` em modo `summary`;
- sinal rápido: o `tokens_in` do `research` tem de **descer** no `opt` (é o mesmo pedido, sem inputs).

## Custo

**Real (B1):** o `seo-article-demo` gastou **13 130 tokens** em 4 chamadas ao `flash-lite`, entre 1,9k e 4,2k por passo (tabela acima). A estimativa anterior, de 0,9 a 1,5k de entrada, foi feita com o Gemini falso e artefactos pequenos, e subestimava os passos com inputs. O `maxOutputTokens` é 4096 (`DEFAULT_MAX_OUTPUT_TOKENS`). Tectos por run: [BUDGET.md](./BUDGET.md).

## Evidência (2026-10-01, Gemini falso)

`seo-article-demo.plan.yaml` pela CLI (`plan_runner.cli.main`), com o transporte HTTP substituído por um falso que devolve o formato real do `generateContent`:

| Fase | Resultado |
|---|---|
| `run --mode external --worker gemini` | `research`, `seo_brief` (JSON), `copy`, `critic` (JSON) executados; pára em `paused_human_gate` no `hitl_publish_decision` |
| `resume --decision approve` | `done`; artefactos `01`…`05` escritos |
| Chamadas ao Gemini | 4 (nenhuma para o passo humano) |
| `token_usage.jsonl` | 4 linhas, o mesmo `run_id`, `agent_id` `marketing.research`, `.seo_brief`, `.copy_answer_first`, `.critic_item13`, `status: ok`, `remote: skipped` |

O mesmo fluxo está no teste `test_plano_seo_demo_do_inicio_ao_fim_com_worker`.

## Ficheiros do repo por passo (`repo_files`, SEC-1, 2026-10-03)

O worker não tem tools, por isso um passo não consegue ler o repo sozinho. Um passo pode declarar ficheiros do repo para entrarem no prompt, só de leitura:

```yaml
steps:
  - id: audit
    action: security_audit
    vertical: meta
    repo_files:
      - runner/requirements.txt
      - .github/workflows/runner-tests.yml
```

| Regra | Valor | Onde |
|---|---|---|
| Activação | **opt-in por passo**: `repo_files: [path, ...]` no passo do plano. Sem o campo, o prompt é igual ao de antes, nos dois modos (`opt`/`legacy`) | `runner/plan_runner/external_worker.py` (`build_prompt_ctx`) |
| Acesso | **só leitura**; o worker lê e injecta o texto no fim do prompt do utilizador, na secção "Ficheiros do repo (so leitura)", marcada como dados e não instruções | `runner/plan_runner/repo_files.py` |
| Paths | explícitos e relativos à raiz do repo; recusados: absolutos, `..`, globs, directórios, e symlinks que saiam do repo | idem |
| Exclusões fixas | `.env*`, `*.pem`, `*.key`, `secrets/`, `.git/`, `node_modules/` (decisão do maestro), mais `*.p12`, `*.pfx`, `*.keystore`, `*.jks`, `id_rsa*`, `id_ecdsa*`, `id_ed25519*`, `id_dsa*`, `.npmrc`, `.pypirc`, `.netrc` e `credentials*`. Valem também no **destino** de um symlink. Comparação sem maiúsculas | `DENY_NAME_PATTERNS`, `DENY_DIRS` |
| Limite | **50 KB no total** por passo (`MAX_TOTAL_BYTES`). O ficheiro que passa o limite é cortado, com marcador, e os seguintes ficam de fora (`over_limit`) | idem |
| Binários | ficam de fora (`binary`) | idem |
| Rastreio | `result.json → meta.context.repo_files`: por entrada, `status` (`included`, `truncated`, `excluded`, `invalid`, `missing`, `over_limit`, `binary`), bytes e motivo. **Nunca** o conteúdo de um excluído | idem |

**Custo:** os ficheiros contam no `tokens_in` do passo, ~1 token por 3,3–3,5 caracteres (B1). Os 50 KB do limite dão no máximo ~15k tokens de entrada. Os 10 KB do demo de security dão ~3k. O tecto de tokens da área continua a aplicar-se ([BUDGET.md](./BUDGET.md)).

**Não confundir com o `knowledge_refs`** do topo do plano, que continua sem ser lido (AU-22): o `repo_files` é por passo e explícito, para não mudar os prompts dos planos existentes (incluindo o `seo-article-demo`, base do B1-bis-R2).

## Activação da skill e scripts (`activate_for_task`, SEC-1.3, 2026-10-07)

Antes do worker, o executor chama `activate_for_task` (`runner/plan_runner/skill_activation.py`). Faz quatro coisas:
- resolve agente + skill;
- regista o sha256 de cada um;
- aplica a allow-list de scripts de `config/skills.yaml` (deny-by-default);
- só com `should_search_external: true` no passo, pesquisa skills externas (candidatas, nunca instaladas).

Escreve `pending_steps/<id>/skill_activation.json` e, só quando a skill tem scripts ou houve pesquisa, `SKILL_ACTIVATION.md`, que entra no fim do prompt do utilizador na secção "Activacao da skill (SEC-1.3)", nos dois modos. Sem isso, o prompt é igual ao de antes. As tools do worker são o AU-20 (secção abaixo). Contrato completo: [SKILL-ACTIVATION.md](./SKILL-ACTIVATION.md).

## Tools do worker (AU-20, P-37 = B, 2026-10-07)

**Desligadas por omissão.** Com `PLAN_RUNNER_TOOLS=1`, um passo cujo `tools_allowed` tenha tools do registo passa a ter um loop de function calling. Sem a flag, o passo faz a chamada única de sempre.

O `result.json` diz sempre em que caso se está, num passo que declare `tools_allowed`:
- **com a flag:** `meta.tools.enabled: true`, com as chamadas;
- **sem a flag (AU-20b, P-42 = A):** `meta.tools: {"enabled": false, "reason": "PLAN_RUNNER_TOOLS desligada", ...}`;
- **passo sem `tools_allowed`:** sem `meta.tools`.

| Tool | Nível | O que faz |
|---|---|---|
| `read_repo_file(path)` | read | lê um ficheiro do repo pelas regras do SEC-1 (denylist de segredos, sem `..`, sem symlinks para fora, até 20 KB) |
| `retrieve_knowledge(kb, query, top_k?)` | read | pesquisa o L5 (MCP, v2 com proveniência), até 8 trechos com a fonte; **só nos kb permitidos ao passo** |

Regras do loop:
- só as tools autorizadas são declaradas ao modelo; os nomes do plano fora do registo (ex.: `web_search`) ficam em `meta.tools.unsupported`;
- os argumentos são validados antes de executar;
- o resultado volta como **dados**, não instruções;
- limites: `max_turns` 6 e `max_tool_calls` 12, ajustáveis no passo com `tool_limits:` (tectos 10 e 24). Ao atingir um limite, o passo fica em `waiting_external`;
- o orçamento é verificado antes de cada turno extra (`paused_budget`);
- cada turno é uma linha no ledger;
- cada chamada é um evento `tool_called`, com o sha256 dos argumentos e nunca os argumentos em claro.

**kb permitido ao passo** (decisão do maestro, 2026-10-07):
- os kb vêm de `tool_kbs: [legal, global]` no passo; sem isso, do `kb` do bloco `knowledge:`;
- o modelo vê o `kb` como enum desses valores;
- um kb fora da lista volta como `kb_not_allowed` e não chega ao L5;
- um passo sem kb declarado não recebe o `retrieve_knowledge`, que fica em `meta.tools.refused_policy`.

**Nível `act`: aprovação humana em cada chamada** (decisão do maestro, 2026-10-07):
- quando o modelo pede uma tool `act`, o loop **pára antes de correr qualquer chamada desse turno**;
- o worker escreve:
  - um pedido em `hitl-requests.jsonl` (contrato `hitl-request-v1`, com os argumentos em `context.tool_calls`, para o humano ver o que aprova);
  - o estado da conversa em `pending_steps/<id>/tool_approval.json`;
  - o evento `tool_approval_requested`;
- o run fica em `paused_human_gate`, com `status.tool_approval` e o `HITL.md`;
- decide-se com `python -m plan_runner resume <run> --decision approve|reject`, ou do lado Node no mesmo contrato. Aqui o `--decision` é obrigatório: aprovar nunca é o default. Se o Node já respondeu a esse pedido, é essa a decisão que conta; uma decisão de outro pedido nunca conta;
- `approve` executa a chamada tal como foi pedida. `reject` devolve `rejected_by_human` ao modelo, que continua: o run não acaba;
- cada decisão vale para uma chamada e para o seu pedido (por id), e `edit` não é aceite;
- `prepare` continua recusado;
- o registo ainda não tem nenhuma tool `act` real: entram só com idempotência e rollback (contrato §15.6).

Contrato e tabela de testes: [`docs/architecture/AU-20-TOOL-EXECUTOR.md`](../architecture/AU-20-TOOL-EXECUTOR.md).

## Limites actuais

- **Tools só com a flag.** Sem `PLAN_RUNNER_TOOLS=1`, o `tools_allowed` continua declarativo e o prompt diz ao modelo que não tem tools. Com a flag, só `read_repo_file` e `retrieve_knowledge` existem; `web_search` e tools `prepare`/`act` não (secção "Tools do worker"). O `repo_files` continua a funcionar como antes.
- **Campos de plano que o runner não aplica (AU-22):** o `knowledge_refs` é lido mas não tem efeito; o L5 entra pelo bloco `knowledge:` do passo (S9). O `budget.max_replans` e o `steps[].on_fail` **foram removidos** do schema e dos planos do repo (P-10 = A; fora até ao F3, replanning). Nunca tiveram efeito: um passo que falha pára o run em `failed` e quem decide é o humano. Um plano antigo que ainda os declare corre na mesma, mas falha o `python -m plan_runner.plan_schema`. O motor regista estes 3 campos no evento `plan_fields_ignored` no arranque do run.
- **`done_when` (AU-22, P-10 = A):** verificado no fim do run, nos 2 engines (`plan_runner/done_when.py`). Formas reconhecidas: `<caminho> exists` (ficheiro dentro do run) e `human_gate_resolved on <passo>`. Se alguma falhar, o run termina em `failed` com `detail = done_when` e a lista em `status.done_when_failed` (eventos `done_when_checked` e `done_when_failed`). Uma condição noutra forma gera `done_when_unverifiable` e não falha o run; reescrevê-la é o AU-22b. O `budget.max_steps` é aplicado nos 2 engines: no `native` passo a passo; no `langgraph` antes de arrancar (um plano com mais passos do que o tecto não corre nenhum, porque as ondas são paralelas).
- **Worker inline nos 2 engines (W-005, 2026-10-03).** `--engine langgraph --worker gemini` corre cada passo como no `native`, incluindo as ondas paralelas, o `paused_budget` e o `worker_error` no status. Sem `--worker`, o langgraph continua a parar em `waiting_external` (worker standalone + `resume`, ou `resume --worker gemini`).
- **Orçamento:** tecto de tokens por run (`--max-tokens`, ou `budget.max_tokens` do plano ou da área), verificado pelo worker antes de cada chamada. O run pausa em `paused_budget` e retoma com `resume --max-tokens N`. Ver [BUDGET.md](./BUDGET.md).
