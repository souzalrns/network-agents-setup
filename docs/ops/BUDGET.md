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

**Conselhos (Bloco C):** o tecto é o `budget.max_tokens` da área do conselho (`area:` no `config/councils.yaml`) ou `--max-tokens`. O orçamento é verificado antes de cada chamada (membro, par, chairman). Atingido o tecto, a sessão fica `paused_budget`, e `council resume <dir> --max-tokens N` retoma sem repagar o que já está feito ([COUNCIL.md](./COUNCIL.md)).

O validador E7 (`python -m plan_runner.areas`) aceita na área `budget: null` ou `{max_steps?, max_tokens?}`, com inteiros > 0, e recusa o resto.

> **Tectos por área ligados (B5-bis fase 1, decidido pelo maestro a 2026-10-01, opção A):** produção (marketing, docs, research, software) 80k; risco (finance, legal, security) 40k; exploratórias (gamedev, ops) 30k; transversal (horizontal) 20k. Estão em `config/areas.yaml` e só se aplicam a planos gerados pelo router; planos escritos à mão usam o `budget` do próprio plano ou `--max-tokens`. **Rever depois do B1-bis-C** (encurtar skills/prompt-base, PLANO item 12).

## Proposta B5-bis: tectos por área (fase 1, folgados): DECIDIDA (A) e aplicada a 2026-10-01

**Base real (B1, 2026-10-01):** o `seo-article-demo` (4 passos) gastou **13 130 tokens**, entre 1,9k e 4,2k por passo, e o custo sobe com os artefactos injectados (`WORKER-EXTERNAL.md`, B1). Um plano real de 8 passos deve gastar **25–40k** (estimativa do maestro). O router soma ~0,3–1,2k por pedido e sai do tecto da área.

**Fase 1 = freio, não optimização:** os tectos só param runs anómalos (loops, planos que crescem sem controlo). Marketing não desce de 60k antes da fase 2 (contexto por resumo, PLANO item 11). Lembrete: o tecto pode ser ultrapassado em **uma** chamada, até ~8k com os prompts reais (prompt de ~4k + `maxOutputTokens` 4096).

| Grupo | Áreas | **A (recomendada)** | B (mais justa) | C (uniforme) |
|---|---|---:|---:|---:|
| Produção | marketing, docs, research, software | **80 000** | 60 000 | 100 000 |
| Risco (`hitl: required`) | finance, legal, security | **40 000** | 30 000 | 100 000 |
| Exploratórias | gamedev, ops | **30 000** | 20 000 | 100 000 |
| Transversal | horizontal | **20 000** | 15 000 | 100 000 |

- **A (recomendada):**
  - **produção 80k** = 2× o topo da estimativa de 8 passos (40k), ~6× o B1. Nenhum plano legítimo de hoje lá chega;
  - **risco 40k** cobre um plano de 8 passos no topo da estimativa. Estas áreas já têm gate humano no fim, por isso o tecto só trava um run descontrolado antes da revisão;
  - **exploratórias 30k** ≈ 2× o B1. O `ops` hoje é sobretudo 1 passo (atendimento), e o `gamedev` não tem agentes;
  - **horizontal 20k:** o planeador é chamado com pedidos vagos, e 1–2 passos chegam.
- **B:** usa os mínimos que pediste (marketing 60k). Corre o risco de travar planos legítimos de 8 passos que gastem perto de 40k mais a ultrapassagem de uma chamada.
- **C:** um valor para tudo. Simples, mas não dá uso à política por área (D2 R6) e deixa as áreas de risco tão soltas como as outras.

Notas:
- Software não estava na tua lista; pus-o em produção porque os planos de desenvolvimento tendem a ser longos.
- Legal, gamedev e docs ainda não têm agentes: o router manda-os para triagem HITL sem chamar o LLM, por isso o tecto só passa a contar quando tiverem agentes.

**Aplicar** (depois da decisão; é 1 linha por área no `config/areas.yaml`, validada pelo E7):

```yaml
  - id: marketing
    ...
    budget: {max_tokens: 80000}
```

**Rever na fase 2:** com o contexto por resumo medido, apertar marketing e software para ~2× o gasto real de um plano de 8 passos.

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
