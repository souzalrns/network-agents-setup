# L5 — Domain knowledge / RAG (lab)

Camada **L5** = corpus recuperável (vector ± keyword). Não substitui L3 (skills) nem bancos operacionais de status.

## Padrão de retrieve (alinhado à produção)

```text
query → embed(RETRIEVAL_QUERY)
     → match(agent_id, fetchK)
     → match(global, fetchK)     # merge, não só se agent vazio
     → filter minSimilarity
     → dedupe + rank
     → topK results
```

| Parâmetro | Default recomendado |
|-----------|---------------------|
| topK | 12 |
| fetchK | min(topK×2, 24) |
| minSimilarity | 0.22 (env `RAG_MIN_SIMILARITY`) |
| alsoGlobal | true |

## Ingest

- Chunk estável + replace por `(agent_id, source)` antes de reinserir
- taskType documento vs query distintos no embedder
- `agent_id=global` para conhecimento transversal

## Dual-source (quando existir banco operacional)

```text
Prompt:
  [OPERATIONAL BANK]  ← verdade para status
  [L5 SUPLEMENTO]     ← docs; se conflitar, prevalece o banco
  [EMPTY]             ← “não tens o dado”
```

Ingest só em L5 **não** actualiza o banco operacional.

## Integração futura neste repo

- Spec: este doc + `contracts.md` (`retrieve_knowledge`)
- Produção de referência: `agent-network-mcp` (`lib/knowledge.js`, `lib/agentRuntime.js`)
- Workflow lab: `.github/workflows/ingest-knowledge.yml` (delta dry-run)

Não migrar monólitos sem consumidor; adoptar o **contrato** e o **grounding**.
