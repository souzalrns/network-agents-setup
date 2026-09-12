# Arquitectura de memória (genérica)

**Âmbito:** framework de rede de agentes — **qualquer domínio** (não amarrado a um cliente, vertical ou site).

**Objectivo:** separar tipos de informação por camada, com contratos de leitura/escrita, scopes e gates. Memória ≠ RAG; episódio ≠ skill; facto de utilizador ≠ documento de corpus.

**Regra de ouro:** o modelo só vê fatias autorizadas; gravações estáveis (L3/L4/L5) não são auto-merge opacas.

**Grounding:** [GROUNDING.md](./GROUNDING.md) — se o contexto não tiver o dado, **não inventar**.

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

Detalhe: [layers.md](./layers.md) · [contracts.md](./contracts.md) · [scopes.md](./scopes.md) · [rag-l5.md](./rag-l5.md).

---

## O que cada camada **não** é

| Camada | Anti-padrão |
|--------|-------------|
| L0 | Preferências de um utilizador; dumps de chat |
| L1 | “Memória de longo prazo” |
| L2 | Fonte de verdade de factos de negócio sem projeção |
| L3 | Guardar PII ou secrets em skills |
| L4 | Indexar PDFs de domínio inteiros |
| L5 | Preferências (“o user gosta de tom X”); status operacional de tools |
| L6 | Substituir L5 no dia 1 sem necessidade multi-hop |

**L5 ≠ banco de status.** Avaliações operacionais (integrado/rejeitado) vivem noutro registo; ver [GROUNDING.md](./GROUNDING.md).

---

## Fluxo genérico de um run

```text
1. Load L0 (+ grounding directive)
2. Optional recall L4 (scope: user | project | agent)
3. Plan / step → action do registry
4. Se procedural: load L3 (só a skill escolhida)
5. Se precisa corpus: retrieve L5 (+ L6 se hybrid) — merge agent+global, minSimilarity
6. Executar tools (L1)
7. Append eventos L2 + artefactos
8. Optional: skill_candidate (L3) ou memory_candidate (L4) → human_gate
```

Se L5/L4 devolverem vazio para o facto pedido → resposta **(b) não está no contexto**, nunca inventar.
