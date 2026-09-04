# Multi-knowledge-base por domínio

## Porquê

Um único vector store para jurídico + marketing + operacional:

- mistura intents  
- dificulta ACL  
- reindex e versionamento acoplados  

## Modelo

```text
RAG Service (API / MCP tools)
  route(domain | agent_id | explicit kb)
    → kb_legal
    → kb_marketing
    → kb_ops
    → kb_method (Item 13, playbooks setup)
```

Cada KB: pipeline de ingest próprio, embeddings eventualmente partilhados, **colecções/namespaces separados**.

## Tool contract (exemplo)

```json
{
  "action": "retrieve_knowledge",
  "kb": "legal",
  "query": "...",
  "filters": { "doc_type": "lei" },
  "top_k": 8,
  "require_citations": true
}
```

`tools_allowed` no plan step restringe quais KBs o agent pode tocar.

## ACL

Filtro no **retrieve**, não só na UI final. Utilizador/agente sem scope não vê chunks.
