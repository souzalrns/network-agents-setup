# LangGraph Lab - motor de orquestracao do runner

**Estado:** funcional end-to-end. Commitado em main. Testado com 9 testes automatizados.

Este documento descreve a arquitetura do motor LangGraph usado pelo plan_runner para executar planos plan.yaml com:
- Orquestracao por ondas paralelas (waves)
- Checkpoint persistente em SQLite (checkpoints.db)
- Resume real via Command do LangGraph
- HITL nativo com interrupt()

---

## Visao geral

O plan_runner tem dois motores:

| Motor | Ficheiro | Comando |
|-------|----------|---------|
| Nativo (sequencial) | runner/plan_runner/engine.py | --engine native (default) |
| LangGraph (grafo) | runner/plan_runner/langgraph_engine.py | --engine langgraph |

Este documento cobre o motor LangGraph.

Diferencas do nativo:
- Respeita depends_on como um grafo (StateGraph)
- Agrupa steps independentes em ondas paralelas (parallel_groups)
- Persiste o estado em checkpoints.db (SqliteSaver)
- Usa interrupt() do LangGraph para HITL
- Permite resume real do ultimo checkpoint

---

## Arquitetura

### Ficheiros

| Componente | Path |
|------------|------|
| Engine LangGraph | runner/plan_runner/langgraph_engine.py |
| Compilacao plan para waves | runner/plan_runner/langgraph_compile.py |
| CLI | runner/plan_runner/cli.py |
| Deps opcionais | runner/requirements-langgraph.txt |
| Testes | runner/tests/test_langgraph_flow.py |
| Template fan-out | docs/orchestration/marketing/templates/examples/ship-parallel.plan.yaml |

### Funcoes auxiliares

| Funcao | Proposito |
|--------|-----------|
| merge_artifacts | Reducer para Annotated dict - merge de dicts entre nos |
| _WaitExternal | Excecao para mode external - transporta completed parcial |
| _build_langgraph_builder | Constroi o StateGraph (nos + arestas) |
| _run_waves_fallback | Fallback se o LangGraph falhar |

### Estado do LangGraph

PlanState tem os campos:
- plan_id
- completed (Annotated list com reducer add)
- artifacts (Annotated dict com reducer merge_artifacts)
- paused_at
- decision
- error
- log

**Importante:** Annotated, TypedDict, add e merge_artifacts tem de estar no escopo do modulo. O LangGraph 1.x usa get_type_hints que procura no globals do modulo.

### Checkpoint (SqliteSaver)

O run_plan_langgraph abre um SqliteSaver em out_dir/checkpoints.db:

    with SqliteSaver.from_conn_string(str(checkpoint_path)) as checkpointer:
        graph = builder.compile(
            checkpointer=checkpointer,
            interrupt_before=interrupt_before or None,
        )
        result = graph.invoke(initial_state, config)

O config tem thread_id igual ao run_id.

O checkpoint persiste:
- channel_values.completed (steps concluidos)
- channel_values.artifacts (paths dos artefactos)
- channel_values.log (log interno do LangGraph)
- branch:to step (proximo no a executar)

---

## Fluxos

### Modo stub

Todos os steps usam execute_stub (placeholder, sem worker externo).

    1. run --mode stub
       executa prepare, code_review, security_review, test_review, ship_decision
       chega ao no hitl (tem human_gate)
       interrupt() pausa
       status: paused_human_gate, paused_at_step=hitl

    2. resume --decision approve
       retoma do checkpoint
       hitl e concluido
       status: done, completed=[todos os steps]

### Modo external

Steps de acao usam execute_external_request, que:
- Verifica se pending_steps/step_id/result.json existe
- Se nao: cria pending_steps/step_id/ (request.json, AGENT.md, SKILL.md) e levanta _WaitExternal
- Se sim: le o resultado e continua

    1. run --mode external
       prepare: result.json nao existe - _WaitExternal(prepare)
       status: waiting_external, paused_at_step=prepare
       pending_steps/prepare/ criado

    2. Worker externo preenche pending_steps/prepare/result.json
       contendo ok true e detail prepare done

    3. resume --decision approve
       retoma do checkpoint
       prepare: result.json existe - conclui
       code_review: result.json nao existe - _WaitExternal(code_review)
       status: waiting_external, completed=[prepare], paused_at_step=code_review

    4. Worker preenche code_review, security_review, test_review

    5. resume --decision approve
       code_review, security_review, test_review concluem
       ship_decision: result.json nao existe - _WaitExternal
       status: waiting_external, completed=[prepare, code_review, security_review, test_review], paused_at_step=ship_decision

    6. Worker preenche ship_decision

    7. resume --decision approve
       ship_decision conclui
       hitl: interrupt() pausa
       status: paused_human_gate, paused_at_step=hitl

    8. resume --decision approve
       hitl conclui
       status: done

### HITL (Human-in-the-loop)

O step hitl tem human_gate no plano. O node_runner usa:

    from langgraph.types import interrupt

    decision = interrupt({
        type: human_gate,
        step_id: step.id,
        allow: step.human_gate.allow,
    })

O interrupt() pausa o grafo e devolve o controlo ao caller.

O resume usa:

    from langgraph.types import Command

    result = graph.invoke(
        Command(resume=decision),   # decision = approve ou reject
        config,
    )

### completed acumulado

No mode external, o _WaitExternal transporta partial_state com o completed do step que acabou de concluir. No resume_plan_langgraph, o except _WaitExternal faz uniao entre o completed anterior (do status.json) e o novo (do partial_state):

    previous = set(status.get(completed) or [])
    new = set(w.partial_state.get(completed) or [])
    union = sorted(previous | new)
    status[completed] = union

Isto garante que os steps concluidos em runs anteriores nao se perdem.

---

## Como testar

### Testes automatizados

    cd $env:USERPROFILE\Downloads\network-agents-setup\runner
    python -m pytest tests/ -v

9 testes cobrem:

| Teste | O que valida |
|-------|--------------|
| test_no_bom_in_langgraph_engine | Sem BOM no ficheiro |
| test_engine_module_imports | Imports (Annotated, merge_artifacts, _WaitExternal) |
| test_run_stub_pauses_at_hitl | run --mode stub - paused_human_gate |
| test_resume_approve_completes_plan | resume approve - done |
| test_resume_reject_sets_rejected_state | resume reject - rejected |
| test_run_external_waits_for_worker | run --mode external - waiting_external |
| test_resume_external_accumulates_completed | completed acumulado apos resume |
| test_external_full_cycle | Ciclo completo external (5 workers) - HITL - done |
| test_checkpoint_db_persists_completed | checkpoints.db e SQLite valido |

### Manualmente

    cd $env:USERPROFILE\Downloads\network-agents-setup\runner

    # Ver waves
    python -m plan_runner compile-graph ..\docs\orchestration\marketing\templates\examples\ship-parallel.plan.yaml

    # Run stub
    python -m plan_runner run ..\docs\orchestration\marketing\templates\examples\ship-parallel.plan.yaml --engine langgraph --mode stub --out ..\pilots\run-ship-lg

    # Resume
    python -m plan_runner resume ..\pilots\run-ship-lg --decision approve

---

## Limitacoes conhecidas

| Limitacao | Impacto | Workaround |
|-----------|---------|------------|
| Eventos duplicados no HITL | Cosmetico | Ignorar no events.jsonl |
| --decision edit tratado como approve | Semantico | Usar reject + re-run |
| Steps reexecutados no resume (external) | Performance | Aceitavel (steps rapidos) |
| Paralelismo logico por waves | Performance | LangGraph executa sequencialmente na wave |
| Sem crash recovery testado explicitamente | Confiabilidade | Precisa de teste adicional |

---

## Troubleshooting

### BOM (U+FEFF) no langgraph_engine.py

**Sintoma:** SyntaxError: invalid non-printable character U+FEFF.

**Causa:** Set-Content -Encoding UTF8 do PowerShell adiciona BOM.

**Solucao:**

    $path = (Resolve-Path runner/plan_runner/langgraph_engine.py).Path
    $bytes = [System.IO.File]::ReadAllBytes($path)
    if ($bytes[0] -eq 0xEF -and $bytes[1] -eq 0xBB -and $bytes[2] -eq 0xBF) {
        $bytes = $bytes[3..($bytes.Length - 1)]
        [System.IO.File]::WriteAllBytes($path, $bytes)
    }

Ou usar python com open em modo w com encoding utf-8 e newline vazio.

### NameError: name Annotated is not defined

**Causa:** imports dentro da funcao. O get_type_hints do LangGraph procura no globals do modulo.

**Solucao:** mover todos os imports para o topo do modulo:

    from operator import add
    from typing import Annotated, Any, TypedDict

### InvalidUpdateError: At key artifacts

**Causa:** varios nos escrevem artifacts em paralelo (wave). Sem reducer, o LangGraph nao sabe combinar.

**Solucao:** usar Annotated dict com merge_artifacts no PlanState e definir merge_artifacts no escopo do modulo.

### _WaitExternal nao transporta completed

**Causa:** o except _WaitExternal nao atualiza status completed ou _WaitExternal nao recebe partial_state.

**Solucao:** garantir que:
1. _WaitExternal.__init__ aceita partial_state
2. node_runner passa partial_state=dict(state)
3. except _WaitExternal faz uniao com previous | new

---

## Mapa mental

    plan.yaml depends_on
        |
        +-- parallel_groups (waves)          # langgraph_compile.py
        |
        +-- build_graph(plan, node_runner)   # StateGraph builder
        |
        +-- graph.invoke(initial_state, config)
        |       |
        |       +-- SqliteSaver (checkpoints.db)
        |       +-- thread_id = run_id
        |       |
        |       +-- node_runner(step, state)
        |       |       |
        |       |       +-- if human_gate: interrupt()
        |       |       +-- if external: execute_external_request()
        |       |       |       +-- _WaitExternal(step_id, partial_state)
        |       |       +-- else: execute_stub()
        |       |
        |       +-- return result (dict)
        |
        +-- status.json                      # persistido
        +-- events.jsonl                     # log append-only

---

## Referencias

| Documento | Conteudo |
|-----------|----------|
| docs/architecture/plan-execute/ | Schema do plano (Plan.schema.json) |
| docs/orchestration/marketing/ | Orquestrador da vertical marketing |
| docs/orchestration/marketing/templates/examples/ship-parallel.plan.yaml | Template fan-out |
| runner/plan_runner/langgraph_engine.py | Codigo fonte |
| runner/tests/test_langgraph_flow.py | Testes de integracao |

---

**Ultima atualizacao:** 2026-09-10.
