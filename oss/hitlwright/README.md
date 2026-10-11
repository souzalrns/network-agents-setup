# hitlwright

**A typed, versioned, auditable human-in-the-loop approval contract.**

When an agent or a workflow must pause for a human decision, hitlwright writes a
**typed request** and reads a **typed decision** — both following a versioned JSON
Schema (`hitl-request-v1`), stored as **append-only JSONL** so the whole approval
trail is auditable and nothing is overwritten. Zero dependencies.

```python
from pathlib import Path
from hitlwright import write_request, read_decision, write_decision, pending_request

run = Path("runs/42")
req_id = write_request(run, step_id="publish", action="publish",
                       allow=["approve", "reject"], title="Approve publish")

# the run pauses; is a human still owed a decision?
if pending_request(run):
    ...  # wait / notify

# a human (or another process) responds:
write_decision(run, req_id, response="approve", responder_id="user:ana", comment="ok")

decision = read_decision(run)   # {"response": "approve", ...} or None
```

Or from the shell:

```console
$ hitlwright request runs/42 --step publish --action publish
hitl_1b2c...
$ hitlwright decide runs/42 hitl_1b2c... --response approve --by user:ana
$ hitlwright decision runs/42        # the latest decision as JSON
```

## Why it exists

Most frameworks offer a generic "interrupt" and leave the rest to you: no typed
request, no versioned contract, no audit trail, and no language-neutral way for a
*different* system to answer. hitlwright is the opposite:

| Property | hitlwright |
|----------|-----------|
| **Typed** | every request/decision follows `hitl-request-v1` (shipped, `schema_path()`) |
| **Versioned** | the schema id is in every record; v2 can coexist |
| **Auditable** | append-only JSONL — the full history, nothing overwritten |
| **Two-sided & language-neutral** | just two JSONL files; any producer writes requests, any responder writes decisions (Python, Node, a CLI, a web UI) |
| **Resumable** | `read_decision` / `pending_request` after a pause — survives a restart |
| **Zero-dep** | pure stdlib; the schema is validated in your tests, not at runtime |

The producer and the responder never call each other — they share two files and one
schema. That is what makes it survive restarts and cross language boundaries.

## API

- `write_request(run_dir, *, step_id, action=None, allow=None, title=None, ...) -> str`
- `read_decision(run_dir) -> dict | None` — the latest valid decision (last wins)
- `write_decision(run_dir, request_id, *, response, responder_id="cli", comment=None) -> dict`
- `pending_request(run_dir) -> dict | None` — latest request with no decision yet
- `latest_request(run_dir) -> dict | None`
- `build_request(...)` / `build_decision(...)` — construct & validate shape without IO
- `schema_path() -> Path` — the shipped `hitl-request-v1` JSON Schema

## How it compares

See `POSITIONING.md` for the evidence-based comparison with LangGraph interrupts,
Temporal signals, Inngest `waitForEvent`, and Humanlayer — and the honest limits
(polling-based, no built-in notifications or auth).

## Install

```console
pip install hitlwright
```

MIT licensed. Part of the [network-agents-setup](https://github.com/souzalrns/network-agents-setup)
ecosystem; extracted from its governed runner so any project can gate on typed human approval.
