# Orçamento de tokens por run

> **Estado (2026-10-01):** implementado e testado com o Gemini falso (15 testes em `runner/tests/test_budget.py`). Fecha a parte "aplicar orçamento" do item 4 do [PLANO-DE-ACAO](../audit/PLANO-DE-ACAO.md). As outras partes do item ("somar por passo, persistir num ledger") já estavam feitas pelo ledger J6 do worker.

## Regra

O **worker** (`runner/plan_runner/external_worker.py`) aplica o tecto. **Antes de cada chamada ao Gemini**:
1. soma o `tokens_total` de todas as linhas do ledger do run (`<run>/token_usage.jsonl`), incluindo passos e router;
2. se `gasto >= tecto`, **não chama** o Gemini e lança `BudgetExceeded`.

O motor (`engine.py`) **pausa** o run em vez de o matar:
- `status.json` fica com `state: paused_budget`, `paused_at_step` e `budget_spent`;
- `events.jsonl` recebe `budget_exceeded {step_id, spent, cap}`;
- `<run>/BUDGET.md` diz o que aconteceu e como retomar;
- o pedido do passo (`pending_steps/<id>/request.json`) fica pronto. Não há `worker_error.json`, porque uma pausa de orçamento não é um erro.

**O tecto é verificado antes de cada chamada, não durante.** Uma chamada que começa abaixo do tecto acaba sempre, por isso o gasto final pode passar o tecto **no máximo em uma chamada**: o prompt mais até `maxOutputTokens`, que é 4096. Exemplo real (Gemini falso, 955 tokens por chamada, tecto 2000): o passo 3 começa aos 1910 (< 2000) e o run pára aos 2865, antes do passo 4.

Não cortar a meio é deliberado. Um artefacto truncado a meio (`MAX_TOKENS`) parte JSONs e não serve a ninguém; parar entre passos deixa sempre o run num estado retomável.

## De onde vem o tecto (por prioridade)

| Fonte | Como | Quando usar |
|---|---|---|
| `--max-tokens N` no `run` ou no `resume` | Fica em `status.json` como `max_tokens` e ganha a tudo | Tecto ad hoc de um run; subir o tecto de um run parado |
| `budget.max_tokens` do plano | `budget: {max_steps: 10, max_tokens: 20000}` no `plan.yaml` | Planos escritos à mão |
| `budget.max_tokens` da **área** (`config/areas.yaml`) | O router passa-o ao plano que gera: **tecto da área menos os tokens que o router já gastou** a decidir. Assim o tecto cobre o pedido inteiro | Política por área (D2 R6, ADR-M6) |
| Nada | Sem tecto: tudo como antes | — |

O validador E7 (`python -m plan_runner.areas`) aceita na área `budget: null` ou `{max_steps?, max_tokens?}`, com inteiros > 0, e recusa o resto.

> Hoje todas as áreas têm `budget: null`: **nenhum tecto está ligado por omissão.** Escolher os valores por área é decisão do maestro (B5-bis em `docs/initiatives/OPEN-ITEMS.md`).

## Como correr

```bash
cd runner
# Tecto de 20k tokens neste run
python -m plan_runner run ../docs/orchestration/marketing/templates/examples/seo-article-demo.plan.yaml \
  --mode external --worker gemini --max-tokens 20000 --out ../pilots/run-worker-seo

# O run parou (state: paused_budget)? Ver porquê:
cat ../pilots/run-worker-seo/BUDGET.md

# Retomar a partir do passo onde parou, com um tecto maior
python -m plan_runner resume ../pilots/run-worker-seo --max-tokens 40000
```

- O `resume` com `--max-tokens`:
  - regista `budget_resumed {step_id, spent, max_tokens}`;
  - continua **só** os passos que faltam (os feitos não repetem nem gastam);
  - volta a parar se chegar ao tecto novo.
- O `resume` **sem** `--max-tokens` num run em `paused_budget` pára outra vez no mesmo passo, sem chamar o Gemini.
- O worker standalone (`python -m plan_runner.external_worker <run>`) respeita o mesmo tecto e sai com o **código 3** quando o encontra.
- No engine `langgraph`, `--max-tokens` dá erro explícito: o tecto é aplicado pelo worker inline, que só existe no `native`.

## Rastreio

| Onde | O quê |
|---|---|
| `<run>/token_usage.jsonl` | Cada chamada: tokens in, out e total (a fonte da soma) |
| `<run>/events.jsonl` | `budget_exceeded`, `budget_resumed` |
| `<run>/status.json` | `max_tokens` (tecto em vigor), `budget_spent` (enquanto parado) |
| `token_usage` no Supabase | As mesmas linhas, se `SUPABASE_*` estiver configurado (ver [WORKER-EXTERNAL.md](./WORKER-EXTERNAL.md)) |

## Limites

- **Embeddings contam 0.** O `embedContent` não devolve `usageMetadata` (J6). Só pesa no router com `--embeddings`.
- **Uma chamada sem `usageMetadata` também conta 0.** Fica registada como `missing_usage` e com aviso no log. Se a API deixar de devolver tokens, o tecto deixa de travar. A consulta de controlo está em `agent-network-mcp/docs/ops/TOKEN-LEDGER.md` (`missing_usage` em `router`/`agent` devia ser 0).
- **Por run, não por dia nem por cliente.** Um tecto global (ex.: tokens por dia para todos os runs) precisaria do ledger central (Supabase) e fica fora daqui.
- **`max_steps` continua separado:** é aplicado pelo motor e acaba em `aborted_budget`, que é terminal. Só o tecto de tokens é retomável.
