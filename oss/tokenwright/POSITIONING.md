# tokenwright — positioning & competitive analysis

> Evidence-based, per the repo playbook (`docs/initiatives/REPO-EVAL-PLAYBOOK.md`).
> The honest question: *what do the others have that we don't, and what would make
> tokenwright the recommended choice in its lane?*

## The lane

tokenwright answers one question: **will the next LLM call keep me under budget, and is
the cost of what already ran counted honestly?** It is a *cost-ledger + pre-call budget
guard*. It is **not** a proxy, **not** a provider router, **not** an observability
dashboard.

## The competitors (and what each actually does)

### `tokencost`
- **What it is:** a library mapping model → price, with helpers to compute a call's cost.
- **What it has that we don't:** a large, maintained **price table** for many providers.
- **Why it is not the whole lane:** it computes cost; it does not define a **cap** nor a
  **pre-call guard**, and an unknown model typically returns 0 / raises inconsistently.
  tokenwright is deliberately price-table-agnostic (you bring the mapping — even
  tokencost's) and adds the fail-closed rule and the projective guard on top.

### LiteLLM cost tracking
- **What it is:** a provider gateway that also tracks spend per request/key, with
  budgets enforced at the **proxy**.
- **What it has that we don't:** real multi-provider routing, keys, and server-side
  budgets.
- **Why it is heavier / different:** it is a gateway you run; the budget lives in the
  proxy, coupled to LiteLLM. tokenwright is a tiny in-process check you call before a
  request, with no server and no provider coupling — usable *inside* an agent step even
  when you are not going through a gateway.

### Langfuse / Helicone
- **What they are:** excellent observability platforms — traces, cost dashboards, alerts.
- **What they have that we don't:** UI, storage, multi-tenant analytics, alerting.
- **Why they are not this lane:** they **measure after** the fact. An alert fires once
  you have already spent. tokenwright **refuses before** — the call that would cross the
  cap does not happen.

## Where tokenwright wins (and the evidence)

| Property | tokenwright | tokencost | LiteLLM | Langfuse/Helicone |
|----------|-------------|-----------|---------|-------------------|
| **Fail-closed** on unknown price | ✅ `CostUnknown` | ❌ (often 0) | ⚠️ gateway | ❌ |
| **Pre-call** cap (refuse before spend) | ✅ `guard_next_call` | ❌ | ⚠️ at proxy | ❌ (after) |
| Counts **reasoning** tokens (`total - in`) | ✅ | ⚠️ manual | ⚠️ | ⚠️ |
| In-process, no server/gateway | ✅ | ✅ | ❌ | ❌ |
| Zero dependency / provider-agnostic | ✅ | ⚠️ ships a table | ❌ | ❌ |

The distinctive pair is **fail-closed on an unknown price** and a **projective,
in-process cap**: spend is never under-counted by a missing price, and the call that
would cross the cap is refused rather than merely logged.

## Honest limits (what tokenwright does NOT do)

- **No price table.** You bring the mapping. (By design: prices move; coupling to one
  table dates fast. Pair it with `tokencost`'s table if you want one.)
- **No token counting.** It costs tokens you already counted; it does not tokenize text.
  (Pair it with the provider's `countTokens` or a tokenizer to get `projected_in`.)
- **In-process only.** No cross-process/global budget; for a shared budget across workers
  you persist `spent` yourself (e.g. the ledger file) and pass it in.
- **No analytics UI.** It is a guard, not a dashboard.

## What would make it "more the choice" (roadmap, not claims)

- An optional adapter that reads a `tokencost`-style table so `prices` can be one import.
- A tiny persistent-ledger helper (append a row, read running total) for shared budgets.
- Per-model and per-tag sub-caps, not just a single global cap.
