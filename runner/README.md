# plan_runner

> Infrastructure for running multi-step AI workflows with governance:
> declarative plans, human approval, auditable execution.

[![Runner tests](https://github.com/souzalrns/network-agents-setup/actions/workflows/runner-tests.yml/badge.svg)](https://github.com/souzalrns/network-agents-setup/actions/workflows/runner-tests.yml)
[![Coverage](https://codecov.io/gh/souzalrns/network-agents-setup/branch/main/graph/badge.svg?flag=runner)](https://codecov.io/gh/souzalrns/network-agents-setup)

---

## Why

Most AI agent frameworks optimise for autonomy. This runner optimises for **governance**.

It executes **declarative plans** (YAML) that define what steps to run, in what order (`depends_on`), where a human must approve (`human_gate`), and what to produce at each step (`output_artifact`).

Everything is **auditable**: each run writes a `status.json` (current state), an `events.jsonl` (append-only log), and a `checkpoints.db` (LangGraph state). If the process dies mid-run, `resume` picks up where it stopped.

---

## Quickstart (3 commands)

    git clone https://github.com/souzalrns/network-agents-setup
    cd network-agents-setup/runner

    # 1. Install (minimal - native engine only)
    pip install -r requirements.txt

    # 2. Install (with LangGraph engine - recommended)
    pip install -r requirements-langgraph.txt

    # 3. Run an example plan
    python -m plan_runner run ../docs/orchestration/marketing/templates/examples/seo-article-demo.plan.yaml --mode stub --out ../pilots/demo

After the run, look at:

- `../pilots/demo/status.json` - final state
- `../pilots/demo/events.jsonl` - full execution log
- `../pilots/demo/artifacts/` - generated artifacts

---

## What's in the box

- **Two engines**
  - `native` - sequential execution, no external dependencies
  - `langgraph` - state graph with waves, real checkpoints (SqliteSaver)
- **Human-in-the-loop (HITL)**
  - `approve` / `reject` / `edit` decisions
  - `--payload-file` for structured input on edit
  - `interrupt()` native to LangGraph
- **Crash recovery**
  - 3 tested scenarios (mid-run death, wave interruption, corrupted state)
  - Emits `resume_after_interrupt` event when recovering
- **External workers**
  - `--mode external` writes `pending_steps/<step>/request.json`
  - Waits for `<step>/result.json` from any worker (LLM, human, script)
- **Quality**
  - 51 tests, 83% coverage
  - CI on every push (GitHub Actions)
  - Coverage reported to Codecov
  - Release workflow (tag v* -> GitHub Release)

---

## User levels

| Level | Wants | Sees |
|---|---|---|
| **Curious** | try in 2 minutes | pip install + run example |
| **Practitioner** | use in production | run plan with --out dir |
| **Advanced** | full control | env vars + config file + Python API |

---

## CLI reference

    # Run a plan
    python -m plan_runner run <plan.yaml> [--engine native|langgraph] [--mode dry-run|stub|external] [--out <dir>]

    # Resume a paused run (after HITL or external wait)
    python -m plan_runner resume <out_dir> [--decision approve|reject|edit] [--payload-file <file.json>]

    # Show wave compilation (debug tool)
    python -m plan_runner compile-graph <plan.yaml>

### Modes

| Mode | Behaviour |
|---|---|
| `dry-run` | Validates the plan, prints topological order, writes nothing |
| `stub` | Runs steps in order; writes placeholder artifacts; stops at `human_gate` |
| `external` | Writes `pending_steps/<step>/request.json`; waits for `result.json` |

### Engines

| Engine | Behaviour |
|---|---|
| `native` | Sequential execution. No external dependencies. |
| `langgraph` | State graph with parallel waves and persistent checkpoints. Requires `requirements-langgraph.txt`. |

---

## Example: full HITL cycle

    # 1. Start a run that pauses at a human gate
    python -m plan_runner run ../docs/orchestration/marketing/templates/examples/seo-article-demo.plan.yaml --engine langgraph --mode stub --out ../pilots/demo

    # status.json: state = "paused_human_gate"

    # 2. Approve it
    python -m plan_runner resume ../pilots/demo --decision approve

    # status.json: state = "done"

Every step emits events to `events.jsonl`, so you can reconstruct exactly what happened, in what order, and why.

---

## Architecture

For a deep dive on the LangGraph engine (state model, waves, checkpoints, HITL internals, crash recovery), see:

- `docs/architecture/langgraph-lab/README.md`
- `docs/architecture/plug-in-agents.md` (planned)

---

## What's NOT in the box (yet)

This runner is intentionally focused. The following are planned, not implemented. See `docs/initiatives/backlog.md` for the full list.

- **Memory integration** (LightRAG + Cognee) - per-client episodic + knowledge memory
- **Web UI** - currently CLI-only
- **Multi-provider LLM** - the runner is LLM-agnostic; workers decide which LLM to use
- **Observability** (OpenTelemetry) - events log is currently the primary signal

---

## Testing

    cd runner
    pip install -r requirements-langgraph.txt
    python -m pytest tests/ -v

    # With coverage
    python -m pytest tests/ --cov=plan_runner --cov-report=term-missing

The suite covers: plan validation, native engine, external mode, HITL decisions, crash recovery, event deduplication, and LangGraph wave execution.

---

## Em portugues

**plan_runner** e um motor de execucao de planos declarativos (YAML) para workflows de IA que exigem **governacao**: gates humanos, execucao auditavel, recuperacao de crashes, e integracao com workers externos.

Quickstart (3 comandos):

1. `pip install -r requirements.txt`
2. `pip install -r requirements-langgraph.txt`
3. `python -m plan_runner run <plan.yaml> --out <dir>`

O motor tem **51 testes**, **83% de cobertura**, corre em CI a cada push, e suporta dois motores: `native` (sequencial) e `langgraph` (grafo com checkpoints reais).

---

**License:** see repository root.
