# Camadas do pipeline RAG

## 1. Document understanding

Objectivo: preservar **estrutura** (títulos, artigos, tabelas, notas), não só plain text.

| Entrada | Risco se ignorar |
|---------|------------------|
| PDF escaneado | OCR fraco → retrieval lixo |
| Lei / contrato | Chunk a meio do artigo |
| Tabela de prazos | Perde linhas |

Ferramentas de referência: Docling, MinerU, parse RAGFlow.

## 2. Chunking estruturado

Preferir limites semânticos/estruturais:

- artigo / secção / cláusula  
- parent-child (pai = secção, filho = parágrafo)  
- metadados: `doc_id`, `domain`, `source_path`, `page`, `article_ref`, `acl`

## 3. Indexação multi-índice

| Índice | Query type |
|--------|------------|
| Dense vector | Semelhança semântica |
| BM25 / keyword | Termos exactos (nº processo, artigo lei) |
| Graph | Caminhos entre entidades |

## 4. Hybrid retrieve → merge → rerank

```text
candidates_vector ∪ candidates_keyword ∪ candidates_graph
        → dedupe
        → reranker
        → top_k context pack
```

## 5. Geração com citação

- Prompt exige fontes; UI mostra spans.  
- Se não houver evidência no pack → agent deve dizer incerteza (critic).

## 6. Avaliação

Golden questions por domínio. Métricas: context relevance, faithfulness, answer relevancy (família RAGAS).  
Regredir retrieval **antes** de culpar o LLM.
