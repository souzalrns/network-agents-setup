# ADR-F3-PROVENANCE-RETRIEVE — Proveniência no retrieve (F3)

| Campo | Valor |
|---|---|
| **ID** | ADR-F3-PROVENANCE-RETRIEVE |
| **Estado** | **Aceite: opção A** (P-26 = A, maestro, 2026-10-06). O F3a está a ser implementado; o SQL de produção é corrido pelo DEV |
| **Data** | 2026-10-06 |
| **Decisores** | Maestro (aceita ou rejeita); redigido pelo Claude |
| **Item** | F3 no `PENDENCIAS.md` (AMBOS, Alta) e F3 da cadeia F1–F6 (`docs/initiatives/PENDENCIAS_T6.md`) |
| **Fontes** | ADR-INGESTION-PRIMITIVES §4 (`source_meta`) e §9 (T6e, F2a); `docs/ops/L5-F0-REVALIDATION.md` §1 (F0.8, provenance camada a camada); `scripts/rag_schema.sql`; `ANM:lib/knowledge.js:67-75` (`matchOnce`, a chamada ao `match_knowledge`); EXECUTION-PLAN §3 (ajuste 3) e §15.8 |

## 1. Contexto

- **Hoje, a proveniência que chega ao retrieve é só o `source`** (o path no git), de ponta a ponta (F0.8).
  - O `match_knowledge` devolve `(id, content, source, similarity)` (`scripts/rag_schema.sql:58-71`).
  - O MCP chama-o com 3 argumentos com nome (`ANM:lib/knowledge.js:68`).
  - Os `filters` da tool `retrieve_knowledge` são aceites mas não têm efeito (F0.8).
- **A camada DOCUMENT** (`knowledge_sources`) tem `content_hash`, `git_sha` e `last_ingested_at`, mas o retrieve não a lê.
- **Desde o F1 e o F2**, cada documento convertido ou página buscada tem um `.meta.yaml` ao lado do `.md` (`uri`, `final_url`, `title`, `document_type`, `retrieved_at`, `content_hash`, `status`…). Esse ficheiro **não chega à BD**: o ADR-INGESTION-PRIMITIVES §4 deixou isso para o F3.
- **O F3 canónico é mais largo** que o do prompt da cadeia: validade e conflitos, autoridade da fonte, golden set alargado e cobertura dos 33 ficheiros fora do MANIFEST, pack a pack (D-EP2).

## 2. Opções (decisão P-26)

| | Opção | Efeito em produção | Custo |
|---|---|---|---|
| **A (recomendada)** | **Aditiva, em 2 PRs.** (1) NAS: colunas novas na `knowledge_sources`, coluna `locator` na `knowledge_chunks`, **RPC nova `match_knowledge_v2`** com filtros e proveniência (por JOIN), o `ingest_apply` passa a ler o `.meta.yaml`, SQL versionado em `scripts/migrations/` e testado contra Postgres no CI. (2) MCP: o `retrieve_knowledge` passa para a v2 **depois** de o DEV correr o SQL | Nenhum até o DEV correr o SQL; o `match_knowledge` antigo fica intacto, por isso o MCP não parte em nenhum momento | 2 PRs + 1 passo do DEV (SQL) |
| B | Mudar a assinatura do `match_knowledge` existente | O MCP parte entre o SQL e o deploy, se não forem simultâneos | 1 PR em cada repo, coordenados |
| C | Proveniência só no runner: no retrieve, ler o `.meta.yaml` do git pelo `source` | Nenhum, mas o MCP (Claude.ai) continua sem proveniência e os filtros continuam sem efeito | Pequeno, mas não resolve o retrieve |

**Âmbito recomendado com a A:** o F3a cobre o critério do prompt (os campos e os filtros abaixo). O resto do F3 canónico fica em F3b e F3c, sem corte e com o registo no `PENDENCIAS.md`:
- **F3a:** schema, proveniência no retrieve, filtros por `status`, `jurisdiction`, validade e `document_type`;
- **F3b:** validade e conflitos, autoridade da fonte e golden set alargado;
- **F3c:** os 33 ficheiros fora do MANIFEST, pack a pack.

## 3. Contrato do F3a (com a opção A)

| # | Item | Proposta |
|---|---|---|
| 1 | Schema `knowledge_sources` (aditivo, `ADD COLUMN IF NOT EXISTS`) | `uri`, `title`, `document_type`, `retrieved_at`, `status` (`active` por omissão; `superseded`/`revoked`/`expired`/`deleted`), `jurisdiction`, `effective_from`, `effective_until`, `final_url`, `meta` (`jsonb` com o resto do `.meta.yaml`) |
| 2 | Schema `knowledge_chunks` | `locator` (`l.<início>-<fim>`, que o chunker já calcula e hoje se perde na escrita, F0.8) |
| 3 | RPC | `match_knowledge_v2(query_embedding, match_agent_id, match_count, filters jsonb DEFAULT '{}')`: devolve `id, content, source, similarity, locator, content_hash, uri, title, document_type, retrieved_at, status, jurisdiction, effective_from, effective_until`. Por omissão, filtra `status = 'active'` e `effective_until` não passado. Os filtros aceites são `status`, `jurisdiction`, `document_type` e `valid_at` (data) |
| 4 | Escrita | O `ingest_apply.apply_one` lê o `.meta.yaml` (validado pelo `validate_ingested`, regra 3) e grava-o na `knowledge_sources`. Sem sidecar, como os 39 ficheiros actuais, os campos ficam com os valores derivados do git (`uri` = path, `document_type` = `md`, `status` = `active`). Sem regressão |
| 5 | Compatibilidade | O `match_knowledge` antigo não muda. As linhas do MCP (`project` NULL) continuam a funcionar, porque o JOIN é `LEFT JOIN` |
| 6 | Validação | Testes contra Postgres com pgvector no CI (`test-rag` / `test-ingest`): a migração 2× (idempotente), a v2 com e sem filtros, as linhas sem sidecar, um documento `superseded` que não aparece por omissão, e a validade por data |
| 7 | Produção | O SQL fica em `scripts/migrations/`, e o DEV corre-o (W-prod). Antes e depois, há queries só de leitura de controlo no PR |
| 8 | MCP (2.º PR) | O `retrieve_knowledge` chama a v2, e a `citation` passa a trazer `uri`, `title`, `retrieved_at`, `locator` e `status`; os `filters` passam a ter efeito. Verificar o impacto no conector do Claude.ai (`ANM:CLAUDE.md`) |

## 4. Consequências

- **Positivas:**
  - a proveniência que o F1 e o F2 já produzem chega a quem pergunta;
  - os filtros da tool passam a funcionar;
  - um documento revogado ou expirado deixa de ser devolvido por omissão (§15.8);
  - nada parte em produção durante a transição.
- **Custos:**
  - 1 passo manual do DEV (correr o SQL);
  - 2 RPCs a manter até o MCP migrar. O `match_knowledge` antigo sai num PR posterior, com decisão.

## 5. Decisão pedida

A P-26 no `PENDENCIAS.md` §10: **decidida A pelo maestro a 2026-10-06**. O F3a é implementado em 2 PRs (NAS e MCP), sem escrita em produção: o SQL fica em `scripts/migrations/` para o DEV correr, e o MCP usa a v2 só com a feature flag ligada.
