# LangGraph — padrões profundos a roubar

A tabela geral só citava “grafo + checkpoint + HITL”. Isto extrai o que o LangGraph realmente ensina para o **nosso** Plan-Execute / event log / runtime lab — **sem** obrigar a dependência LangGraph.

---

## 1. Estado tipado + **reducers** por campo

Cada campo do estado tem política de merge:

| Reducer | Comportamento | Uso nosso |
|---------|---------------|-----------|
| overwrite (default) | Último ganha | `current_step`, `status` |
| **append** (`operator.add` / list concat) | Acumula | `artifacts[]`, `tool_calls[]`, `errors[]` |
| custom | Merge explícito | scores do critic |

**Porquê importa:** em fan-out paralelo, sem reducer append, workers **apagavam** o output uns dos outros.

**Roubar:** no plan/runtime, listas de evidência e eventos são **append-only**; escalares de controlo sobrescrevem.

---

## 2. Checkpoint após cada nó (não só no fim)

- Depois de cada node/step: persistir estado do *thread*.  
- Permite crash recovery, HITL e time-travel.  
- Durability modes (ideia): só no exit vs async vs **sync** antes do próximo passo.

**Roubar:**

```text
step_finished → append event + snapshot plan_status
(não só plan_done no fim)
```

Equivalente leve: `events.jsonl` + ficheiro `status.json` por `plan_id` / `thread_id`.

---

## 3. `thread_id` como stream de execução

Tudo o que é um “run” partilha um id de thread. Histórico de checkpoints = lista ligada imutável.

**Roubar:** `plan_id` / `run_id` = thread; nunca misturar dois plans no mesmo stream.

---

## 4. Interrupt / HITL (mais fino que “human_gate: true”)

| Mecânica LangGraph | Significado |
|--------------------|-------------|
| `interrupt_before` / `interrupt_after` | Parar **antes/depois** de um nó nomeado |
| `interrupt(payload)` dentro do nó | Parar com pergunta/payload estruturado |
| `Command(resume=...)` | Retomar com decisão |
| Decisões típicas | **approve** / **reject** / **edit** (args) / **respond** (texto como resultado da tool) |

**Roubar:** human_gate não é só boolean — é **protocolo de resposta**:

```yaml
human_gate:
  when: before_side_effect
  allow: [approve, reject, edit]
  payload_ref: artifacts/pending-action.json
```

Edit = humano corrige args **sem** re-plan completo (quando faz sentido).

---

## 5. Time-travel: **replay** vs **fork**

| | Replay | Fork |
|--|--------|------|
| O quê | Re-executar a partir de checkpoint N | Novo ramo com estado **alterado** em N |
| Nós antes de N | Não re-correm (já gravados) | Idem |
| Nós depois | Re-correm (LLM pode diferir) | Re-correm no ramo novo |
| Timeline antiga | Mantém-se | Mantém-se para audit |

**Roubar:**

- Debug: “falhou no passo 5 → fork do 4 com brief corrigido”.  
- Não apagar a timeline má — **bifurcar**.  
- Alinhado a event sourcing: eventos imutáveis + novo stream ou `fork_of`.

```text
plan_id: piloto-002
fork_of: piloto-002@step-3
reason: human_edit_seo_brief
```

---

## 6. `Send` — fan-out dinâmico (map-reduce)

Arestas fixas não bastam quando o número de workers é runtime (N URLs, N keywords).

- Nó gera lista → devolve `Send(worker, partial_state)` × N.  
- Cada worker vê **estado parcial** próprio.  
- Fan-in com reducer append no collector.

**Roubar:**

```yaml
# conceptual
- id: expand
  action: plan_fanout
  output: list[item]
- id: map_item
  action: process_item
  foreach: expand.output   # N instâncias isoladas
  reducer: append artifacts
- id: reduce
  action: merge
  depends_on: [map_item]
```

Isto é o padrão orquestrador–workers **sem** mesh peer-to-peer.

---

## 7. `Command` — update + goto num só retorno

Nó pode devolver ao mesmo tempo: **actualizar estado** e **saltar** para um nó (ou END), em vez de só confiar em conditional edges externas.

**Roubar:** `on_fail: abort | retry | human | goto:compensating_step` já no plan; no runtime, um resultado de passo = `{ state_patch, next }`.

---

## 8. Subgraphs — isolamento de namespace

- Subfluxo = grafo compilado usado como nó do pai.  
- **Estado isolado** por omissão em produção (transform in/out).  
- Checkpoint **namespace** por invocação — dois subgraphs a partilhar namespace **escrevem por cima** uns dos outros.

**Roubar:**

- Cada sub-plan / área vertical = subgraph com `thread_id` ou namespace único.  
- Marketing pipeline ≠ code Spec Kit no mesmo namespace de checkpoint.  
- Alinhado a contexto isolado (Hermes/dsh) e a `inputs` mínimos por passo.

---

## 9. Superstep / paralelismo

Nós sem dependência entre si no mesmo “wave” correm em paralelo; fan-in espera todos.

**Roubar:** no plan, passos com o mesmo `depends_on` satisfeito e sem dependência mútua → elegíveis a paralelo (budget e tools_allowed ainda aplicam).

---

## 10. Untracked / efémero vs persistido

Alguns valores **não** entram no checkpoint (caches locais, handles). No resume, recomeçam vazios.

**Roubar:** distinguir no desenho:

- Persistido: artefactos, decisões, tool results relevantes  
- Efêmero: tokens de streaming, locks locais  

---

## 11. Streaming de eventos intermédios

Produção séria emite progresso (node start/end, tokens) sem esperar o END.

**Roubar:** dashboard / control plane escuta `step_started` / `tool_called` (event sourcing), não só o markdown final.

---

## Mapa LangGraph → nosso setup

| LangGraph | Nosso equivalente actual / alvo |
|-----------|----------------------------------|
| State + reducers | status escalar + listas append (events, artifacts) |
| Node | `steps[].action` |
| Edge / depends | `depends_on` |
| Conditional edge | `on_fail` / routing no orchestrator |
| Checkpointer | events.jsonl + status snapshot |
| thread_id | plan_id / run_id |
| interrupt + Command(resume) | human_gate + allow approve/reject/edit |
| time-travel fork | plan `fork_of` + nova pasta pilot |
| Send map-reduce | foreach step + reducer append |
| Subgraph + namespace | sub-plan isolado / profile |
| durability sync | append event **antes** de side-effect crítico |

---

## O que **não** é necessário copiar

- Pregel internals, LangSmith obrigatório, API exacta `StateGraph`  
- Substituir MCP por LangGraph Platform  

O valor é o **modelo de execução durável**, não a biblioteca.

---

## Checklist de adopção no setup

- [x] depends_on / pipeline (arestas)  
- [x] human_gate boolean  
- [ ] human_gate com approve | reject | edit  
- [ ] reducer append documentado para artifacts/events  
- [ ] checkpoint por step (events + status)  
- [ ] fork_of / time-travel na meta do pilot  
- [ ] foreach / Send-style no schema do plan (fase 2)  
- [ ] namespaces por profile/sub-plan  
