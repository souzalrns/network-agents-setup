# HITL Alignment — Python ↔ TypeScript

> Design note: how `plan_runner` (Python) and the Node platform (TypeScript) will share HITL state.
>
> **Status:** design. Not implemented.
> **Last updated:** 2026-09-11

---

## Why this exists

Two HITL systems already exist in this repo, built independently:

| System | Where | Language |
|---|---|---|
| **`plan_runner` HITL** | `runner/plan_runner/` | Python |
| **`HitlManager`** | `packages/core/src/hitl/` | TypeScript |

They use the same concepts (request, approve, reject, checkpoint) but different APIs. A run that pauses in `plan_runner` is invisible to the Node API. A request created in the Node API cannot be resolved by the `plan_runner` CLI.

This document defines a **shared contract** so both sides can interoperate. The contract lives at:

```
docs/architecture/hitl/hitl-request-v1.json
```

---

## What each side has today

### Python (`plan_runner`)

**Writes:**
- `status.json` — `state: "paused_human_gate"`, `paused_at_step`, `completed`
- `events.jsonl` — event `human_gate_requested` with `step_id`, `level`, `kind`, `allow`
- `checkpoints.db` — LangGraph checkpoint (SQLite)
- `HITL.md` — human-readable note in the run directory

**Reads:**
- CLI `--decision approve|reject|edit`
- `--payload-file` for `edit`

**Has:**
- `edit` decision (with structured payload)
- Declarative `human_gate` in YAML plans
- Crash recovery (3 scenarios)
- Event audit log
- LangGraph `interrupt()` integration

**Missing:**
- Priority (always implicit)
- Category (never set)
- Expiration (never expires)
- Alternatives / risks / impacts
- Unique request id (uses `run_id` + `step_id`)
- Full status enum (only `paused` / resolved)

### TypeScript (`HitlManager`)

**Writes / reads:**
- In-memory maps (`pendingRequests`, `approvedRequests`, `rejectedRequests`, `checkpoints`)
- Emits events: `request-created`, `request-approved`, `request-rejected`, `request-expired`

**Types** (`packages/shared/src/types/hitl.ts`):
- `HitlStatus`: `pending | approved | rejected | expired | cancelled`
- `HitlPriority`: `low | medium | high | critical`
- `HitlCategory`: `financial | legal | medical | architectural | contractual | strategic | security | approval`
- `HitlRequest` (23 fields)
- `HitlCheckpoint`

**Has:**
- Priority, category
- Expiration (`scheduleExpiration`, `expireRequest`)
- Alternatives, risks, impacts
- Unique id (`hitl_<uuid>`)
- Full status enum
- Event emitter
- Checkpoint with `memorySnapshot`

**Missing:**
- `edit` decision (only `approved` / `rejected`)
- Declarative plans (API-only)
- Crash recovery of in-flight runs
- Integration with LangGraph

---

## The contract (v1)

The full JSON Schema is at `hitl-request-v1.json`. Key decisions:

### Base is TypeScript

The TypeScript `HitlRequest` is richer (priority, category, expiration, alternatives). The contract uses it as the base, with adjustments:

| Decision | Rationale |
|---|---|
| `schema: "hitl-request-v1"` field added | Allows versioning; both sides check it |
| `source: "plan_runner" \| "node_api"` field added | Tells each side where the request came from |
| `run_id`, `plan_id`, `step_id` added | Python-specific; null when created by Node API |
| `allow: ["approve", "reject", "edit"]` added | Python-specific; Node API defaults to `["approve", "reject"]` |
| `response` uses `approve`/`reject`/`edit` | Normalises TS's `approved`/`rejected` and Python's `approve`/`reject`/`edit` |
| `priority` defaults to `"medium"` | Python never sets it; avoids null-handling |
| `category`, `alternatives`, `risks`, `impacts` nullable / default empty | Optional for Python; used by Node API |
| `expires_at` nullable | Python never sets it; Node API always sets it |

### What stays Python-specific

- `allow` — the plan decides which decisions are valid
- `run_id`, `plan_id`, `step_id` — the run context
- `metadata.paused_at_step`, `metadata.completed`, `metadata.mode`

### What stays Node-specific

- `metadata.memorySnapshot` (in checkpoint, not in request)
- `metadata.responderId` format (`user:luiz` vs `cli`)

---

## Where shared state lives

Three options, in order of complexity:

### Option A — Shared file (recommended for now)

**Where:** `pilots/<run>/hitl-requests.jsonl` (one JSONL file per run, append-only)

**How:**
- `plan_runner` appends when it pauses
- `HitlManager` reads it when the API is queried
- Both write decisions to a separate `hitl-decisions.jsonl`
- `plan_runner resume` reads the decision from there

**Pros:** zero infra, easy to test, single-user
**Cons:** not multi-user, not real-time

### Option B — Supabase (recommended when multi-user)

**Where:** table `hitl_requests` in the existing Supabase project

**How:**
- Both sides write/read from the same table
- Python: `supabase-py`
- TypeScript: `@supabase/supabase-js`
- Real-time via Supabase Realtime (WebSocket)

**Pros:** multi-user, real-time, already in stack
**Cons:** +1 dependency for Python

### Option C — Redis (later)

**Where:** Redis (local or cloud)

**How:**
- `plan_runner` publishes to `hitl:requests`
- `HitlManager` subscribes
- API Node serves via WebSocket

**Pros:** very fast, real-time
**Cons:** +1 service to run

**Decision for now:** **Option A.** It proves the contract without new dependencies. Option B when the first multi-user scenario appears.

---

## Implementation plan (phased)

### Phase A.1 — Contract (done)

- `docs/architecture/hitl/hitl-request-v1.json`
- `docs/architecture/hitl/README.md` (this file)

### Phase A.2 — Python side (1 day)

**New file:** `runner/plan_runner/hitl.py`

Responsibilities:
- `write_request(run_dir, *, step, run_id, plan_id, completed) -> str` — appends to `hitl-requests.jsonl`, returns `hitl_id`
- `read_decision(run_dir) -> dict | None` — reads `hitl-decisions.jsonl`, returns the latest decision

**Changes:**
- `runner/plan_runner/engine.py` — replace direct writes with `hitl.write_request()`
- `runner/plan_runner/langgraph_engine.py` — same
- `runner/plan_runner/cli.py` — `resume` reads the decision from the file (still supports `--decision` for CLI override)

**Tests:**
- `tests/test_hitl_contract.py` — verify written JSON validates against the schema

### Phase A.3 — TypeScript side (1 day)

**Changes:**
- `packages/core/src/hitl/HitlManager.ts` — add `importFromFile(path)` and `exportToFile(path)` methods
- `packages/shared/src/types/hitl.ts` — align with the contract (add `schema`, `source`, `run_id`, `plan_id`, `step_id`, `allow`)

**Tests:**
- `packages/core/src/hitl/HitlManager.test.ts` — roundtrip: write → read → decision

### Phase A.4 — End-to-end test (0.5 day)

Test scenario:
1. Run `plan_runner run design-flow-demo.plan.yaml --mode stub`
2. Run pauses at `hitl` → writes `hitl-requests.jsonl`
3. Node API reads the file → exposes via `GET /hitl`
4. Node API approves via `POST /hitl/:id/approve` → writes `hitl-decisions.jsonl`
5. `plan_runner resume <out>` reads the decision → completes

**Total Phase A:** ~2.5 days.

### Phase B — Supabase (when needed)

Migrate the shared file to a Supabase table with the same schema. Both sides read/write via Supabase clients. Estimated: 2-3 days.

---

## Non-regression constraints

Nothing in this plan may break existing behaviour.

- `plan_runner` must keep passing all 72 tests
- `test_client.py` (MCP server) must keep passing
- `HitlManager` must keep its current public API
- Existing YAML plans must remain valid
- `checkpoints.db` must keep being used (not replaced)

**Additive, not substitutive.** The new `hitl.py` module and the new file-based storage are added alongside the current `status.json` / `events.jsonl` writes.

---

## What this document is not

It is not a specification. It is a **design note** — enough to guide implementation, not enough to be one.

For the general vision, see `docs/architecture/plug-in-agents.md`.
For the memory integration design, see `docs/architecture/memory-integration.md`.
For the MCP server, see `mcp/plan_runner/README.md`.

---

## Em português

**Alinhamento HITL.** Existem dois sistemas HITL no repo:

- **Python** (`plan_runner`) — `human_gate` no YAML, `approve`/`reject`/`edit`, crash recovery, eventos.
- **TypeScript** (`HitlManager`) — priority, category, expiration, alternatives, checkpoint com memorySnapshot.

**O contrato comum** está em `hitl-request-v1.json`. Base é o TypeScript (mais rico), Python adapta.

**Sincronização:** ficheiro partilhado (`hitl-requests.jsonl`) agora; Supabase quando houver multi-user.

**Não-regressão:** nenhuma alteração quebra os 72 testes, o `test_client.py` ou o `HitlManager` atual. Aditivo, não substitutivo.

**Plano:** 2.5 dias para a Fase A completa (Python + TypeScript + teste end-to-end).