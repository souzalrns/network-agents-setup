# doneproof

**Accept a task only when its done-ness is proven by evidence — never the agent's own word.**

An agent (or a plan) declares *doneproof* conditions as plain strings. `doneproof`
checks each one against real evidence and reports **passed**, **failed** or
**unverifiable**. Zero dependencies, pure stdlib, pluggable into any runner or agent.

```python
from pathlib import Path
from doneproof import evaluate, is_satisfied

result = evaluate(Path("runs/42"), [
    "artifacts/report.md exists",
    "human_gate_resolved on publish",
], gate_resolved=lambda step: step in resolved_steps)

if not is_satisfied(result):
    raise SystemExit(f"not done: {result['failed']}")
```

Or from the shell:

```console
$ doneproof check runs/42 "artifacts/report.md exists" "human_gate_resolved on publish" --resolved publish
ok   file_exists: artifacts/report.md
ok   gate_resolved: publish
doneproof: satisfied (0 failed, 0 unverifiable)
```

## Why it exists

Most agent frameworks accept `status: done` because the agent *said* it was done.
That is the failure mode `doneproof` refuses. A task is accepted only when its
completion is **verifiable**:

| Condition | Evidence checked |
|-----------|------------------|
| `<path> exists` | the file exists under the run's root (no `../` escape) |
| `human_gate_resolved on <step>` | a human approval for `<step>` was recorded |

Everything else is reported as **unverifiable** — not failed. Refusing to fail on
what you cannot check by evidence is as important as refusing to pass on a say-so.
The caller decides what to do with the unverifiable bucket (log it, require review,
or ignore it).

## The gate seam (store-agnostic)

`doneproof` never talks to an event store, queue or database. "Was the gate on
`<step>` resolved?" is answered by a predicate you pass in:

```python
evaluate(root, conditions, gate_resolved=lambda step: my_log.approved(step))
```

Omit it and gates **fail closed** (nothing is considered resolved). This one seam
is why the same engine runs inside a governed runner and standalone in a test.

## API

- `evaluate(root, conditions, gate_resolved=None) -> dict` — returns
  `{"passed": [...], "failed": [...], "unverifiable": [...]}`, JSON-serializable.
  `passed`/`failed` items are `{"kind", "target"}` (kind = `file_exists` |
  `gate_resolved`); `failed` items also carry `{"condition", "reason"}`.
- `is_satisfied(result) -> bool` — true iff nothing failed (unverifiable does not fail).
- `GateResolved` — the `Callable[[str], bool]` type of the gate predicate.

## How it compares

`doneproof` is an **acceptance primitive** for agent/task runs, not a test runner
or a BDD framework. See `POSITIONING.md` for the evidence-based comparison with
pytest, BDD (Gherkin) and shell CI gates, and for what it deliberately does not do.

## Install

```console
pip install doneproof
```

MIT licensed. Part of the [network-agents-setup](https://github.com/souzalrns/network-agents-setup)
ecosystem; extracted from its governed runner so any project can accept tasks by evidence.
