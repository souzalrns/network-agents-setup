# Padrões RAG 2026 — extracção para a rede de agentes

**Regra:** RAG não é “PDF → embedding → um vector DB gigante”. Para plataforma multi-agente: **document understanding + hybrid retrieval + rerank + (opcional) graph + eval + citações + ACL**.

Não substituir MCP prod por um produto RAG; o **RAG Service** é camada de conhecimento que os agents consomem (tools/MCP).

---

## Shortlist (referência)

| Projecto | Força | Uso típico |
|----------|-------|------------|
| **RAGFlow** | Docs complexos, estrutura, citações | Jurídico / PDFs pesados |
| **LlamaIndex** | Framework completo (ingest→query→agent) | Núcleo de orquestração RAG |
| **LightRAG** | Vector + graph + keyword | Conhecimento relacionado |
| **Haystack** | Pipelines modulares produção | Backend pipeline |
| **GraphRAG** | Relações entidade–conceito | Knowledge graph queries |
| **Qdrant** | Vector DB sólido | Storage retrieval |
| **Milvus** | Escala | Volumes grandes |
| **Weaviate** | Vector + hybrid | Apps completas |
| **BGE / rerankers** | Relevância 2ª etapa | Pós-retrieval |
| **RAGAS** | Avaliação | Qualidade contínua |
| **Langfuse** | Observabilidade | Traces RAG+LLM |
| **Docling / MinerU** | Parse estruturado | Ingestão |

Top 3 para testar no *vosso* contexto: **RAGFlow** (jurídico) · **LlamaIndex** (framework) · **LightRAG** (híbrido/grafo).

---

## Princípio arquitectónico

```text
DOCUMENTOS
    → Document understanding (estrutura, não só texto)
    → Indexação multi-modal de retrieval
    → Hybrid retrieval (vector + keyword + graph)
    → Rerank
    → Context pack (+ citações)
    → LLM / agente
    → resposta + fontes
```

**Multi-KB por domínio** (não um blob único):

```text
AGENT NETWORK
    → RAG SERVICE (ACL + routing)
        → KB Jurídico
        → KB Marketing / Item 13
        → KB Operacional
```

Isolamento: ACL, reindex independente, menos canibalização semântica entre domínios.

---

## Camadas (separar sempre)

| Camada | Função | Exemplos de stack |
|--------|--------|-------------------|
| **Ingest / understanding** | Layout, tabelas, OCR, hierarquia | Docling, MinerU, RAGFlow parse |
| **Chunk / structure** | Unidades indexáveis (artigo, secção, tabela) | Hierárquico, semântico, agentic |
| **Index** | Vector, BM25/keyword, graph nodes/edges | Qdrant, OpenSearch, Neo4j/LightRAG |
| **Retrieve** | Hybrid + filtros metadados/ACL | multi-query, parent-child |
| **Rerank** | Ordenar candidatos | BGE-reranker, cross-encoder |
| **Generate** | LLM + citações obrigatórias | agent tool `retrieve_knowledge` |
| **Evaluate** | Faithfulness, relevância, context precision | RAGAS |
| **Observe** | Traces, latência, custo | Langfuse |

Detalhe: [`pipeline-layers.md`](./pipeline-layers.md) · multi-KB: [`multi-kb.md`](./multi-kb.md) · graph: [`graph-rag.md`](./graph-rag.md)

---

## Padrões portáveis (IDs R)

| ID | Padrão |
|----|--------|
| R01 | Document understanding antes de chunk cego |
| R02 | Chunk alinhado a estrutura (artigo/secção) no jurídico |
| R03 | Hybrid: dense + sparse/keyword |
| R04 | Graph retrieval para relações (cliente–processo–órgão) |
| R05 | Rerank obrigatório em produção séria |
| R06 | Citações rastreáveis até span/página |
| R07 | Multi-KB + router por domínio/agente |
| R08 | ACL no retrieve (não só no chat) |
| R09 | Eval contínuo (RAGAS-style) em golden set |
| R10 | Observabilidade de retrieval separado do LLM |
| R11 | Tool `retrieve_*` com schema (query, kb, filters, top_k) |
| R12 | Context pack limitado (token budget) pós-rerank |

---

## Ligação aos agents

- Knowledge ≠ Memory de sessão (Hermes layers).  
- Agent **consome** RAG via tool allowlisted; não embute o índice no prompt system.  
- Vertical jurídico: priorizar RAGFlow-style structure + graph leve.  
- Marketing/Item 13: KB de método + content guidelines; hybrid para intent SEO.  
- Orquestração do *quando* chamar RAG = Plan-Execute / LangGraph/Agno patterns — não o vector DB.

---

## Fora de scope imediato

- Trocar produção site/MCP por RAGFlow monólito  
- Um único índice global sem ACL  
- Confiar em benchmark do vendor sem golden set **vosso**  
