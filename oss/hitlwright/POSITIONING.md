# hitlwright — positioning & competitive analysis

> Evidence-based, per the repo playbook (`docs/initiatives/REPO-EVAL-PLAYBOOK.md`).
> The honest question: *what do the others have that we don't, and what would make
> hitlwright the recommended choice in its lane?*

## The lane

hitlwright answers one question: **when a run pauses for a human, what is the
request, where does the decision live, and how does any system read it back?** It is
a *typed approval contract* + its file protocol. It is **not** a workflow engine,
**not** a queue, **not** a notification service, **not** an auth system.

## The competitors (and what each actually does)

### LangGraph `interrupt` / human-in-the-loop
- **What it is:** pause a graph mid-node and resume with a value, via a checkpointer.
- **What it has that we don't:** deep integration with LangGraph state and streaming;
  resume carries arbitrary Python objects.
- **Why it is not this lane:** the interrupt payload is **untyped** (whatever you put
  in) and lives **inside LangGraph's checkpoint**, not in a portable, versioned,
  schema-validated contract a *different* system can read. It couples you to
  LangGraph. hitlwright is the contract + file protocol, framework-free.

### Temporal signals / `UpdateHandler`
- **What it is:** a durable workflow engine; a human decision arrives as a signal.
- **What it has that we don't:** true durability, retries, timers, horizontal scale.
- **Why it is heavier:** you must run Temporal (server + workers). The signal shape is
  yours to define and validate. For "pause this run for an approval and record it
  auditable", standing up Temporal is a lot; hitlwright is two JSONL files.

### Inngest `waitForEvent` / step tooling
- **What it is:** a serverless workflow/event platform; wait for a human event.
- **What it has that we don't:** hosted orchestration, retries, fan-out.
- **Why it is not this lane:** hosted and event-shaped, no portable typed approval
  record you own on disk. Vendor-coupled.

### Humanlayer
- **What it is:** the closest in intent — an approvals layer/SDK for agents, with
  notifications (Slack/email) and a hosted approval UI.
- **What it has that we don't (honest):** out-of-the-box **notifications** and a
  **reviewer UI**, and a managed backend — real product surface hitlwright has none of.
- **Where hitlwright differs:** it is a **local, zero-dep, self-owned** contract — no
  account, no network, no vendor; the approval trail is your own append-only files and
  a schema you can diff in git. You bring the UI/notifications; hitlwright guarantees
  the *shape* and the *audit*.

## Where hitlwright wins (and the evidence)

| Property | hitlwright | LangGraph interrupt | Temporal | Humanlayer |
|----------|-----------|---------------------|----------|------------|
| **Typed + versioned** request/decision (shipped schema) | ✅ `schema_path()` | ❌ untyped | ❌ you define | ⚠️ SDK types |
| **Portable** record you own (no engine/vendor) | ✅ JSONL | ❌ in checkpoint | ❌ in Temporal | ❌ hosted |
| **Append-only audit** trail in git | ✅ | ❌ | ⚠️ in history | ⚠️ in service |
| **Language-neutral** (Python + Node share it) | ✅ files + schema | ❌ | ⚠️ SDKs | ⚠️ SDKs |
| **Zero dependency / zero infra** | ✅ | ❌ | ❌ server | ❌ account |
| Notifications + reviewer UI | ❌ (bring your own) | ❌ | ❌ | ✅ |
| Durable retries/timers/scale | ❌ | ⚠️ | ✅ | ⚠️ |

The distinctive combination is **a typed, versioned, schema-validated, append-only,
language-neutral approval record you own** — no engine, no server, no vendor.

## Honest limits (what hitlwright does NOT do)

- **Polling, not push.** A responder/producer reads the files; there are no built-in
  notifications. (Roadmap: an optional watcher helper.)
- **No auth / no identity.** `responder_id` is a free string; hitlwright does not
  verify who approved. Put it behind your own authn/authz.
- **No durability guarantees** beyond the filesystem. For retries/timers/scale, drive
  hitlwright *from* a durable engine (it is complementary, not a replacement).
- **One shape (v1).** New fields are a v2 (the schema id is in every record so they
  coexist), not a silent change.

## What would make it "more the choice" (roadmap, not claims)

- An optional file watcher (`inotify`/polling) so a waiter wakes on a decision.
- A tiny reference reviewer (CLI TUI / one-file web page) that reads the JSONL.
- Signed decisions (detached signature over the record) for tamper-evidence.
