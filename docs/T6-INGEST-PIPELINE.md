# T6 — Pipeline de ingestão de knowledge (RAG)

**Objectivo:** o RAG da rede reflecte o Git. Sem one-shot manual que gera chunks stale.

**Âmbito:** knowledge packs e playbooks do `network-agents-setup` (prioridade Item 13 + marketing).  
**Não faz:** alterar produção sem PR/revisão; inventar agents.

Relacionado: [item-13-ai-findability.md](./item-13-ai-findability.md) §11 · ownership rede.

---

## 1. Problema que resolve

| Sintoma | Causa típica |
|---------|----------------|
| Chunks stale | Ficheiro mudou no Git; RAG ficou antigo |
| Chunks órfãos | Ficheiro apagado; chunks continuam a rankear |
| Capabilities inactivas | Inventário desactualizado |
| Respostas correctas ontem, erradas hoje | Agent lê RAG, não o repo |

**Regra:** Git = fonte de verdade. RAG = índice derivado.

---

## 2. Princípios

1. **Hash por ficheiro** — só re-ingere o que mudou  
2. **Delta** — não “wipe all” como rotina  
3. **Purga** — remover chunks de paths inexistentes  
4. **CI no merge** — automático na `main` quando `docs/` muda  
5. **Idempotente** — duas runs = mesmo estado  
6. **Auditável** — log skipped / reingested / purged  

---

## 3. Manifesto de fontes

| Path | Agent dono (rede) | Prioridade |
|------|-------------------|------------|
| `docs/item-13-ai-findability.md` | marketing + produto-tech-transversal | P0 |
| `docs/knowledge/item-13-ai-findability.md` | marketing | P0 |
| `docs/knowledge/ai-findability.md` | marketing | P0 |
| `docs/knowledge/seo-specialist.md` | produto-tech / marketing | P0 |
| `docs/knowledge/ai-visibility.md` | marketing | P1 |
| `docs/knowledge/*.md` (resto marketing) | marketing | P1 |
| `docs/marketing-agency-agents.md` | marketing (só limites, opcional) | P2 |

Não ingerir: STATUS efémeros, secrets, dumps de cliente.

---

## 4. Modelo de dados (mínimo)

**knowledge_sources:** `source_path` (PK), `content_hash`, `agent_id`, `last_ingested_at`, `chunk_count`, `git_sha`

**knowledge_chunks:** `id`, `source_path`, `content_hash`, `chunk_index`, `content`, `embedding`, `agent_id`, `updated_at`

**system_inventory:** UPSERT quando sources/chunks mudam.

---

## 5. Algoritmo (por run)

```text
1. Checkout do commit (merge main)
2. Carregar manifesto
3. Para cada path:
   a. Ficheiro ausente → PURGE
   b. hash = sha256(conteúdo)
   c. hash == stored → SKIP
   d. senão REINGEST: delete chunks do path → chunkar → embed → insert → UPSERT source
4. PURGE global: chunks com source_path fora do manifesto/ficheiros
5. UPSERT inventory (contagens, git_sha)
6. Relatório: skipped / reingested / purged
```

Falhar o job se embed/DB down ou manifesto vazio por erro de config.

---

## 6. Chunking

- Preferir secções `##` / `###` auto-contidas  
- ~200–600 tokens  
- Metadados: `source_path`, título, `agent_id`  
- Item 13: cada item P0 pode ser chunk curto PASS/FAIL  
- Não misturar dois playbooks num chunk  

---

## 7. Ferramentas da rede

| Tool | Uso |
|------|-----|
| `ingest_knowledge` | Escrever chunks no agent dono |
| Supabase | `knowledge_*` / inventory |
| `save_project_state` | Só se agent novo — não em cada re-ingest |
| GitHub Action | Trigger em push `main` + `docs/**` |

---

## 8. GitHub Action (esqueleto)

```yaml
name: ingest-knowledge
on:
  push:
    branches: [main]
    paths: ['docs/**/*.md']
jobs:
  ingest:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Delta ingest
        env:
          SUPABASE_URL: ${{ secrets.SUPABASE_URL }}
          SUPABASE_SERVICE_KEY: ${{ secrets.SUPABASE_SERVICE_KEY }}
        run: python scripts/ingest_delta.py
```

Secrets só em GitHub Secrets.

---

## 9. Ownership do pipeline

| Papel | Responsabilidade |
|-------|------------------|
| produto-tech-transversal | Packs P0 técnicos + health do CI |
| marketing | Item 13 P1 + packs conteúdo |
| Humano | Secrets + 1.º merge do workflow |

Sem agent `ai-findability` obrigatório.

---

## 10. Aceite (T6 DONE)

- [ ] Manifesto versionado  
- [ ] Hash por ficheiro  
- [ ] 1 ficheiro mudou → só esse re-ingerido  
- [ ] Delete/rename → órfãos purgados  
- [ ] CI verde no merge `docs/`  
- [ ] Relatório legível  
- [ ] Spot-check: agent usa regra **actual** do Item 13  

---

## 11. Fora de scope

Reescrever playbook · criar agents · cutover Vianna · re-treino de modelos.

---

## 12. Ordem de implementação

1. `knowledge_sources` + `source_path` nos chunks  
2. Script `ingest_delta.py` dry-run (só hashes)  
3. Staging  
4. Purge + re-ingest real  
5. GitHub Action  
6. Spot-check Item 13 + 1 pack marketing  

---

*network-agents-setup · T6 · não altera produção sem CI/revisão*
