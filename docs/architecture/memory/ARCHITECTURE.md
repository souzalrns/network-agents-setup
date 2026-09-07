# Arquitectura de memória (genérica)

**Âmbito:** framework de rede de agentes — **qualquer domínio** (não amarrado a um cliente, vertical ou site).

**Objectivo:** separar tipos de informação por camada, com contratos de leitura/escrita, scopes e gates. Memória ≠ RAG; episódio ≠ skill; facto de utilizador ≠ documento de corpus.

**Regra de ouro:** o modelo só vê fatias autorizadas; gravações estáveis (L3/L4/L5) não são auto-merge opacas.

---

## Camadas (L0–L6)

```text
L0  IDENTITY / POLICY     regras do sistema, constitution
L1  WORKING CONTEXT       turno / step actual (efémero)
L2  EPISODIC              runs, eventos, artefactos de execução
L3  PROCEDURAL            skills, playbooks (como fazer)
L4  SEMANTIC              factos estáveis (user / agent / project)
L5  DOMAIN KNOWLEDGE      corpus RAG multi-KB
L6  RELATIONAL            grafo de entidades (opcional)
```

| ID | Nome | Persistência | Write | Read típico |
|----|------|--------------|-------|-------------|
| L0 | Identity / policy | Git | humano | sempre (compacto) |
| L1 | Working | RAM / run state | runtime | só o step actual |
| L2 | Episodic | append-only log + artefactos | orchestrator | audit, resume, debug |
| L3 | Procedural | git `skills/` | humano (+ candidate) | progressive disclosure |
| L4 | Semantic | store de memória | recall API + gate | início de sessão / tool |
| L5 | Knowledge | vector (+ keyword) multi-KB | ingest jobs | tool `retrieve_knowledge` |
| L6 | Relational | graph store | extractors | tool `retrieve_graph` / hybrid |

Detalhe operacional: [layers.md](./layers.md) · contratos: [contracts.md](./contracts.md) · scopes: [scopes.md](./scopes.md).

---

## O que cada camada **não** é

| Camada | Anti-padrão |
|--------|-------------|
| L0 | Preferências de um utilizador; dumps de chat |
| L1 | “Memória de longo prazo” |
| L2 | Fonte de verdade de factos de negócio sem projeção |
| L3 | Guardar PII ou secrets em skills |
| L4 | Indexar PDFs de domínio inteiros |
| L5 | Preferências (“o user gosta de tom X”) |
| L6 | Substituir L5 no dia 1 sem necessidade multi-hop |

---

## Fluxo genérico de um run

```text
1. Load L0
2. Optional recall L4 (scope: user | project | agent)
3. Plan / step → action do registry
4. Se procedural: load L3 (só a skill escolhida)
5. Se precisa corpus: retrieve L5 (+ L6 se hybrid)
6. Executar tools (L1)
7. Append eventos L2 + artefactos
8. Optional: skill_candidate (L3) ou memory_candidate (L4) → human_gate
```

---

## Scopes (multi-tenant mental, genérico)

```text
global      framework, constitution, skills base
org         opcional: políticas da organização
project     knowledge KBs e decisões de projecto
user        preferências e factos L4
agent_role  allowlist de tools e KBs
run         L2 episódico (plan_id / run_id)
```

Nenhum agent lê KB ou memória fora do scope permitido pelo plan / `tools_allowed`.

---

## Implementação de referência (não obrigatória)

| Camada | Opções ilustrativas |
|--------|---------------------|
| L2 | `events.jsonl`, Postgres, checkpoint estilo LangGraph |
| L3 | `skills/**/SKILL.md` + registry de actions |
| L4 | API remember/recall (Postgres, Cognee, Mem0, …) |
| L5 | LlamaIndex / LightRAG / Haystack + Qdrant / pgvector |
| L6 | Property graph, LightRAG graph, Cognee graph |

O **contrato** é estável; o motor por baixo é plugável.

---

## Fora de scope deste doc

- Configuração de um cliente ou vertical concreto  
- Escolha final de vendor  
- Cutover de produção  

Ver também: `docs/architecture/patterns-from-hermes/`, `patterns-from-rag/`, `patterns-from-orchestrators/MASTER-EXTRACTION.md`.
