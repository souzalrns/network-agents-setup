# LangGraph lab — implementacao no setup

## O que foi implementado

| Componente | Path |
|------------|------|
| Compilacao plan → waves (parallel groups) | `runner/plan_runner/langgraph_compile.py` |
| Engine langgraph + fallback waves | `runner/plan_runner/langgraph_engine.py` |
| CLI `--engine langgraph` / `compile-graph` | `runner/plan_runner/cli.py` |
| Deps opcionais | `runner/requirements-langgraph.txt` |
| Template fan-out | `docs/orchestration/marketing/templates/examples/ship-parallel.plan.yaml` |

## Instalacao

```powershell
cd $env:USERPROFILE\Downloads\network-agents-setup\runner
pip install -r requirements-langgraph.txt
```

Sem LangGraph instalado, `--engine langgraph` usa **fallback por waves** (mesmos executores stub/external).

## Uso

```powershell
# Ver waves (parallel)
python -m plan_runner compile-graph ..\docs\orchestration\marketing\templates\examples\ship-parallel.plan.yaml

# Correr
python -m plan_runner run ..\docs\orchestration\marketing\templates\examples\ship-parallel.plan.yaml --engine langgraph --mode stub --out ..\pilots\run-ship-lg

python -m plan_runner resume ..\pilots\run-ship-lg --decision approve
```

`seo-article` continua linear (1 step por wave). `ship-parallel` tem wave com 3 reviews apos `prepare`.

## Limites (honesto)

- Fan-out **logico** por waves; paralellismo OS real so com runtime LangGraph completo e nodes async.
- Resume HITL/external reutiliza o motor native `resume_run`.
- Nao e producao MCP; lab apenas.
- Checkpointer = MemorySaver quando disponivel; sem Postgres ainda.

## Mapa mental

```text
plan.yaml depends_on
    → parallel_groups (waves)
    → StateGraph edges (se langgraph)
    → ou fallback sequencial por wave
    → mesmos stub/external + skills
```
