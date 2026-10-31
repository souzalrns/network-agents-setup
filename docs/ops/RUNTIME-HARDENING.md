# Runtime hardening — secção 3 (fecho)

> **Estado:** fecho documental + kill-switch operador, 2026-10-31.
> Complementa a secção 2 (budget, done_when, HITL actor, security routine).
> Não substitui o AGT (Cedar/AgentMesh): documenta o que o `plan_runner` **já garante** e o gap residual.

## 1. Matriz de fecho

| Tema | Estado no setup | Evidência | Residual (não bloqueia o fecho) |
|---|---|---|---|
| **Policy antes da tool** | **Parcial → aceite** | `human_gate` no passo; `tools_allowed`; worker `check_hitl` não executa passo com gate; tool `act` → `paused_human_gate` + `tool_approval` (AU-20); W-020 no resume | Motor de política tipo Cedar/AGT (EX-C4) fica decisão de produto |
| **Atribuição de custo** | **Feito** | `token_usage.jsonl`: `agent_id`, `step_id`, `runner_run_id`, modelo, tokens; eventos `budget_exceeded` com `step_id`; Supabase opcional (W-004) | Chargeback multi-tenant / por dia |
| **Idempotência / resume** | **Feito** | Passos em `completed` não reexecutam; `EventLog.has_event` evita duplicar no re-run LangGraph; `done_when` antes de `done` | Exactly-once distribuído entre workers |
| **Kill switch / containment** | **Feito (run)** | `paused_budget`, `aborted_budget` (max_steps), `rejected` (HITL), **`aborted_operator`** via `plan_runner abort` | Quarentena de agente na rede / cortar subárvore de delegação (precisa Delegation Graph / AGT) |
| **Decision trace** | **Feito** | `events.jsonl` append-only: `step_*`, `human_gate_*`, `budget_*`, `plan_aborted`, `plan_done`, `done_when_*`; `status.json`; HITL jsonl | Pacote único exportável "replay bundle" (nice-to-have) |
| **Inventário de agentes** | **Feito** | `python -m plan_runner.inventory` → `docs/generated/INVENTORY.md`; office + MCP check; CI de consistência (H-01) | — |

## 2. Decision trace (contrato mínimo)

Ordem típica de um run governado:

1. arranque do plano / status `running`
2. por passo: início → (opcional `human_gate_requested` / worker) → `step_finished` | `step_failed`
3. pausas: `budget_exceeded` | tool approval | `waiting_external`
4. retomas: `budget_resumed` | resolução HITL
5. fecho: `done_when_checked` → `plan_done` | `done_when_failed` | `plan_aborted`

Ficheiros: `status.json`, `events.jsonl`, `token_usage.jsonl`, `hitl-*.jsonl`.

## 3. Policy antes de tool `act`

1. O plano declara `tools_allowed` / `human_gate` no passo.
2. Pedido de tool sensível → estado `paused_human_gate` + `tool_approval` no `status.json`.
3. `resume` exige `--decision` explícito (sem default approve em tool act).
4. Decisão de ficheiro `node_api` passa W-020 (`responder_id` / `response_comment`).

Isto **não** é um policy engine universal; é o controlo no perímetro do plan_runner.

## 4. Kill-switch do operador

```bash
cd runner
python -m plan_runner abort ../pilots/run-<id> --reason "stop-requested"
```

- `state` → `aborted_operator`
- evento `plan_aborted` com `by: operator`
- `ABORT.md` no directório do run
- ledger e artefactos **preservados** (nunca cortar evidência)

Não retoma a partir de `aborted_operator` (terminal). Novo run = novo directório.

## 5. Critério de done da secção 3

- [x] Matriz acima alinhada com código em `main`
- [x] `plan_runner abort` disponível
- [x] Link em `docs/architecture/GOVERNANCE.md` §1.2
- [ ] (Opcional) linhas PENDENCIAS se o maestro quiser IDs formais

## 6. Fora de escopo (secção 3)

- Adoptar Microsoft AGT / Cedar / AgentMesh (EX-C3/EX-C4)
- Kill-switch federado multi-run
- Policy por cada JSON-RPC MCP no Vercel (repo `agent-network-mcp`)
