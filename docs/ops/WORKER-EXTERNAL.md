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
> - **Medido no run real (B1-bis-R, maestro, 2026-10-01): −2,6%.** A projecção dizia −16% e **foi refutada**. Ver "Medição real (B1-bis-R)" e "Lição de método".
> - **A hipótese "o custo está no contexto acumulado" não se confirmou como alavanca principal neste plano.**
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

### Medição real (B1-bis-R, 2026-10-01, run do maestro)

| Medida | Valor |
|---|---|
| Plano | `seo-article-demo`, `--worker gemini`, `legacy` vs `opt` (os comandos de "Medir a sério") |
| Δ total real (opt vs legacy) | **−2,6%** |
| Δ total projectado | −16% (tabela abaixo) |

> **Tabela por passo: POR REGISTAR.** A mensagem de 2026-10-01 trazia o marcador `[tabela]` sem os números, e nenhum valor por passo é inventado aqui. Para preencher, usar `pilots/run-worker-ctx-legacy/token_usage.jsonl` e `pilots/run-worker-ctx-opt/token_usage.jsonl` (`tokens_in`, `tokens_out` e `tokens_total` por `step_id`).

| Passo | in legacy | out legacy | in opt | out opt | Δ total |
|---|---:|---:|---:|---:|---:|
| research | _por registar_ | | | | |
| seo_brief | _por registar_ | | | | |
| copy | _por registar_ | | | | |
| critic | _por registar_ | | | | |
| **TOTAL** | | | | | **−2,6%** |

### Lição de método: medir com usage real, não com proxies de caracteres

A projecção sobrestimou o ganho em **~6×** (−16% projectado contra −2,6% real). Causas, por ordem de probabilidade. A atribuição exacta depende da tabela por passo:

1. **Caracteres ≠ tokens, sobretudo no que se corta.**
   - A projecção não usou ÷4: usou caracteres por token **calibrados no B1** (3,29–3,50, média do prompt inteiro).
   - Mas aplicou essa média ao texto **cortado**: frontmatter YAML, cabeçalhos, tabelas, a directiva de grounding.
   - Esse texto tem outra densidade no tokenizer do Gemini. Se o que saiu tem mais caracteres por token do que a média, poupa muito menos tokens do que os caracteres sugerem.
   - Um rácio fixo é um proxy, não o tokenizer.
2. **A saída não foi medida, foi assumida.**
   - A projecção fixou as saídas nos valores do B1, mais 300 tokens de resumo.
   - No run real, o modelo pode escrever mais (ou o resumo sair maior) com o prompt novo. Isso come o ganho na entrada.
3. **O próprio legacy reproduzir o B1 (+0,4%) não validava nada sobre o opt.** Era circular: a calibração foi feita nesses mesmos números.

**Regra a partir daqui** (vale para o B1-bis-C e para qualquer optimização de tokens):
- **Só se decide com `usageMetadata` real** (`promptTokenCount`, `candidatesTokenCount`).
- Para medir só a entrada sem gerar texto, há o endpoint `models/{model}:countTokens` da API Gemini. Dá a contagem exacta do tokenizer, e é uma alternativa barata a um run completo por cada hipótese (pendente: ver OPEN-ITEMS).
- A `token_projection.py` fica no repo só como ferramenta exploratória, marcada como **não usar para decisões**.

### Antes/depois: `seo-article-demo` (PROJECÇÃO, refutada pelo run real: ver acima)

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

### Porque não chega aos 9k (análise feita sobre a projecção; com −2,6% real, a distância é ainda maior)
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

## Limites actuais

- **Não usa tools.** O `tools_allowed` do passo (ex.: `web_search`) não é executado: o prompt diz ao modelo que não tem tools e que deve marcar lacunas. Tools ficam para o porte do `ToolExecutor` (D1, VIA A).
- **Worker inline só no engine `native`.** No `langgraph` usa-se o worker standalone e depois o `resume`.
- **Orçamento:** tecto de tokens por run (`--max-tokens`, ou `budget.max_tokens` do plano ou da área), verificado pelo worker antes de cada chamada. O run pausa em `paused_budget` e retoma com `resume --max-tokens N`. Ver [BUDGET.md](./BUDGET.md).
