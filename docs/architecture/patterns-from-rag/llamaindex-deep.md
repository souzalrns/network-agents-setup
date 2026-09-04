# LlamaIndex — extracção profunda (o que nos interessa roubar)

**Posição:** melhor *framework* de camada de conhecimento/RAG (não produto fechado tipo RAGFlow). Encaixa como **implementação do RAG Service** atrás de tools MCP; orquestração de agentes continua Plan-Execute / (lab) LangGraph|Agno.

Stack frequente 2026: **LlamaIndex (retrieval) + LangGraph/Agno (agent graph)**.

---

## 1. Modelo mental de primitivos

| Primitivo | Função | Roubar como |
|-----------|--------|-------------|
| **Reader / connector** | Fonte → Document | Ingest por origem (drive, pasta, URL) |
| **Document → Node** | Unidade indexável + metadata | Chunk estruturado + `doc_id`, ACL, domain |
| **Transformation** | Split, extract title, embed… | Pipeline de ingest componível |
| **IngestionPipeline** | Cadeia de transforms → (vector store) | Job de reindex idempotente |
| **Index** | Estrutura sobre nodes | Vector / PropertyGraph / … |
| **Retriever** | Query → nodes | Hybrid, BM25, graph sub-retrievers |
| **Node postprocessor** | Rerank, filter | Rerank obrigatório |
| **QueryEngine** | Retrieve + synthesize | “RAG clássico” encapsulado |
| **QueryEngineTool** | Query engine como **tool** do agent | `retrieve_*` no registry |
| **Agent / FunctionAgent** | LLM + tools | Só se o agent for *deste* stack |
| **Workflow** | Event-driven steps | Orquestração RAG multi-step |

Cadeia canónica:

```text
Readers → Documents → Nodes (transforms) → Index
                              ↓
                    Retriever → (Rerank) → QueryEngine
                              ↓
                    QueryEngineTool → Agent / nosso MCP tool
```

---

## 2. IngestionPipeline — o ouro da ingestão

### Composição

```text
transformations = [
  splitter (sentence | semantic | hierarchical),
  metadata extractors (Title, …),
  embed_model,
]
(+ vector_store opcional)
(+ docstore para document management)
```

### Document management (docstore)

- Mapa `doc_id → content_hash`  
- Hash igual → **skip**  
- Hash mudou → **reprocess** (upsert)  

**Roubar:** reindex incremental por hash — essencial em KB jurídico/marketing que actualiza PDFs sem rebuild total.

### Cache de ingestão

`IngestionCache` evita re-embed do que não mudou.

---

## 3. Nodes e metadata (não “só texto”)

Cada node deve carregar o que o retrieve e o ACL precisam:

| Campo típico | Uso |
|--------------|-----|
| `ref_doc_id` / `doc_id` | Proveniência, citações |
| `domain` / `kb` | Multi-KB routing |
| `acl` / `tenant` | Filtro no retrieve |
| `page`, `article_ref`, `section` | Citação humana |
| `doc_type` | lei, contrato, playbook |

**Roubar:** schema de metadata **obrigatório** por KB no setup (`kb_method`, futuro `kb_legal`).

---

## 4. Índices — Vector + Property Graph

### VectorStoreIndex

Padrão dense; plug Qdrant/etc. via integrações.

### PropertyGraphIndex

- Extractors de KG por chunk (`kg_extractors`) → entidades + relações como metadata/grafo  
- Retrievers: `VectorContextRetriever`, `LLMSynonymRetriever`, `TextToCypherRetriever`  
- `PGRetriever` combina sub-retrievers  
- `include_text=True` devolve chunk fonte + path no grafo  

**Roubar:** dual path vector+graph sem abandonar citações de texto; alinha `graph-rag.md`.

---

## 5. Retrieval avançado (além do top_k cego)

| Técnica | Ideia | Interesse |
|---------|--------|-----------|
| **Hybrid** | Dense + BM25/keyword | Termos exactos (artigo, nº processo) |
| **Alpha weighting** | Mistura scores | Tunable |
| **Parent/child** | Chunk fino + contexto do pai | Jurídico |
| **Chunk + doc embedding** | Reweight por similaridade do doc inteiro | Long docs |
| **RouterQueryEngine** | Escolhe qual índice/engine | Multi-KB |
| **SubQuestionQueryEngine** | Decompõe pergunta → sub-queries → merge | Multi-hop |
| **LLMRerank / cross-encoder** | 2ª passagem | R05 |
| **Self-RAG / CRAG-style** | Criticar se o contexto basta; re-retrieve | Agentic retrieve com **cap** de iterações |
| **Composite / routed multi-index** | Um API sobre vários índices | RAG Service façade |

**Roubar prioritário:** hybrid + rerank + router por KB + SubQuestion **só** quando classificador disser multi-hop (cap 2–3).

---

## 6. QueryEngineTool — ponte agent ↔ RAG

```text
QueryEngineTool.from_defaults(
  query_engine=…,
  name="kb_legal_search",
  description="…"  # prompt para o CALLER model
)
```

**Roubar (Agno as_tool + registry):**  
- Uma tool por KB ou uma tool com arg `kb` + allowlist  
- Description escrita para o modelo orquestrador  
- `tools_allowed` no plan step  

Isto é o encaixe natural com **agent-network-mcp** sem meter LlamaIndex *dentro* de cada agent de domínio.

---

## 7. Multi-agent patterns (LlamaIndex)

| Pattern | Como | Vs nosso |
|---------|------|----------|
| **AgentWorkflow** | Hand-offs built-in | Pouco controlo — evitar como core |
| **Orchestrator + sub-agents as tools** | Líder chama especialistas-tool | ≈ Team Agno / supervisor |
| **Custom planner** | LLM emite plan JSON/YAML; código executa | ≈ **Plan-Execute** (preferido) |

**Roubar:** custom planner + tools RAG; não AgentWorkflow “swarm” opaco.

Combinação saudável: **LlamaIndex = retrieval stack**; **vosso plan / LangGraph = controlo**.

---

## 8. Workflows event-driven (pós QueryPipeline)

- `@step` consome/emite **eventos tipados**  
- Async-first; paralelo natural quando eventos independentes  
- Substitui QueryPipeline (legado) como orquestração *dentro* do domínio RAG  

Exemplos de steps RAG:

```text
Start → ClassifyQuery → (SimpleRetrieve | MultiHopRetrieve)
      → Rerank → Synthesize → Stop
```

**Roubar:** event-driven para *pipeline de retrieval*, alinhado a event sourcing (cada step = evento). HITL entre steps se precisar.

Não precisa ser o orquestrador global da rede de 30+ agents.

---

## 9. Retrieval Harness / filesystem primitives (tendência 2026)

Ideia LlamaParse Index: corpus como **tools de filesystem** para o agent:

- hybrid retrieve  
- navegar árvore do doc  
- ler spans  
- layout visual  

**Roubar conceptualmente:** agents jurídicos **interrogam** documento (grep/read/list) além de “similarity search” — especialmente contratos longos. Pode ser tools MCP `doc_grep` / `doc_read` sobre corpus parseado.

---

## 10. Observabilidade e eval

- Callbacks globais (Langfuse, Phoenix, …)  
- Traces por estágio: embed, retrieve, rerank, synthesize  
- RAGAS sobre traces  

**Roubar:** métricas de **retrieval** separadas de métricas de **answer** (já em patterns-from-rag).

---

## 11. O que **não** roubar como core

| Item | Motivo |
|------|--------|
| LlamaIndex.TS (arquivado) | Stack TS → Mastra/outro |
| AgentWorkflow como SO da rede | Pouca governança |
| Tudo cloud LlamaParse obrigatório | Lab pode ser local (Docling etc.) |
| Substituir MCP prod | LI é lib Python de knowledge |

---

## 12. Mapa LlamaIndex → nosso desenho

| LlamaIndex | Nosso |
|------------|--------|
| IngestionPipeline + docstore hash | Jobs de ingest por KB |
| Node metadata schema | Contrato multi-kb |
| Hybrid + rerank | RAG Service default path |
| PropertyGraphIndex | Graph path opcional |
| Router / Composite | `kb` arg + domain router |
| SubQuestion | multi-hop capped |
| QueryEngineTool | MCP `retrieve_knowledge` |
| Custom planner | plan.yaml |
| Workflow steps | pipeline interno RAG service |
| Langfuse callback | observe R10 |

---

## 13. Checklist de adopção (lab)

- [ ] IngestionPipeline + hash skip/reprocess num corpus método  
- [ ] Metadata obrigatória (domain, doc_id, source)  
- [ ] Qdrant (ou equiv.) + hybrid + rerank  
- [ ] Tool MCP/schema `retrieve_knowledge`  
- [ ] Golden set + RAGAS  
- [ ] Router multi-KB quando 2ª KB existir  
- [ ] Property graph só se multi-hop doer  
- [ ] Nunca AgentWorkflow como orquestrador global  

---

## 14. Prioridade “roubar já” (ordenado)

1. **Ingestion com doc_id/hash** + metadata de domínio  
2. **QueryEngine/Retriever como tool** (description para caller)  
3. **Hybrid + rerank**  
4. **Router multi-índice**  
5. **SubQuestion capped**  
6. **Property graph**  
7. **Workflow event-driven só no serviço RAG**  
8. **Filesystem-style doc tools** (lab jurídico)  
