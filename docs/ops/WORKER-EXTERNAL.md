# Worker do modo `external` (AU-23)

> **Estado (2026-10-01):** implementado e testado com o Gemini falso (17 testes em `runner/tests/test_external_worker.py`). O plano `seo-article-demo` corre do início ao fim pela CLI. **Ainda não foi feita nenhuma chamada real**: a sessão em que foi escrito não tinha `GEMINI_API_KEY`. O primeiro run real é o passo 2 abaixo.

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

### Primeiro run real (passo do DEV)

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

## Custo

Medido no `seo-article-demo`, com os `AGENT.md` e `SKILL.md` reais: o prompt de cada passo tem 0,9 a 1,5 mil tokens de entrada. O `maxOutputTokens` é 4096 (`DEFAULT_MAX_OUTPUT_TOKENS`). Um plano de 4 passos faz 4 chamadas ao `flash-lite`, dentro do tier gratuito.

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
