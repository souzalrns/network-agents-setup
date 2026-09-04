# Stack recomendada (referência — não implementada por este doc)

Proposta alinhada à shortlist discutida; **decisão de adopção é humana**.

```text
Ingest:        Docling + MinerU  (e/ou parse RAGFlow para lab jurídico)
Framework:     LlamaIndex        (ou Haystack se preferir pipelines explicit)
Hybrid:        Vector + BM25 + Graph (LightRAG / GraphRAG onde fizer sentido)
Vector DB:     Qdrant            (Milvus se escala extrema)
Graph:         Neo4j ou grafo LightRAG
Rerank:        BGE-reranker (ou equivalente)
Eval:          RAGAS + golden sets por domínio
Observe:       Langfuse
Orchestration: Plan-Execute / (lab) LangGraph ou Agno
Agents:        network MCP + tools retrieve_*
```

**Pilotos sugeridos (ordem):**

1. KB método (docs do setup + Item 13) — baixo risco  
2. Lab jurídico com RAGFlow ou LlamaIndex+Qdrant num corpus fechado  
3. Hybrid + rerank + RAGAS no mesmo corpus  
4. Graph só se multi-hop doer de verdade  

Não misturar cutover do site Vianna com este trilho.
