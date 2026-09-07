# Camadas L0–L6 (operacional)

## L0 — Identity / policy

- Constitution, least privilege, separação lab/prod, bans.  
- Versionado em git.  
- Carregamento: início de sessão de framework ou de cada plan.

## L1 — Working context

- Input do step, tool results correntes, mensagens do turno.  
- Não sobrevive ao run (exceto se copiado explicitamente para L2/L4).  
- Reducers mentais: sobrescreve-se a cada step; não acumular sem limite.

## L2 — Episodic

Eventos mínimos recomendados:

```text
plan_created | plan_approved
step_started | step_finished | step_failed
tool_called | tool_finished
human_gate_requested | human_gate_resolved
verify_finished
plan_done | plan_aborted
memory_candidate_created | skill_candidate_created
```

- Append-only.  
- `run_id` / `plan_id` = thread.  
- Artefactos referenciados por path ou URI, não só texto no evento.  
- Projeção: `status` do plan (passos done/blocked).

## L3 — Procedural

- Skills com trigger, passos, `done_when`.  
- Ciclo: candidate → reviewed → active → patched → archived.  
- Progressive disclosure: catálogo de nomes/descriptions barato; corpo completo só no step.

## L4 — Semantic (user / agent / project)

- Factos curtos, preferências, decisões estáveis, correções do operador.  
- Cada registo: `id`, `scope`, `subject`, `statement`, `confidence`, `source_run`, `created_at`, `ttl?`.  
- Conflitos: novo facto + opcional invalidação do anterior (não editar silenciosamente).  
- `forget` para correcção / apagamento (compliance).

## L5 — Domain knowledge (RAG)

- **Multi-KB** por domínio ou projecto (`kb` id estável).  
- Metadata de node: `doc_id`, `kb`, `source`, `acl`, spans para citação.  
- Ingest: hash por `doc_id` → skip ou reprocess.  
- Retrieve: hybrid recomendado; rerank em caminhos de produção.  
- Resposta de tool: chunks + citations, não só prosa.

## L6 — Relational

- Nós/arestas tipados (genéricos: Entity, relates_to, … — ontologia por projecto).  
- Opcional até haver queries multi-hop reais.  
- Sempre poder voltar ao texto fonte (L5) para citação.
