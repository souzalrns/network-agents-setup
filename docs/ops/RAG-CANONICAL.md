# RAG canónico — migração t6 → knowledge_chunks (J3)

> **Estado (2026-09-30): passos 1 e 2 FEITOS pelo DEV** (migração corrida, `match_knowledge` sem ambiguidade; código na `main` via PR #31). **Em aberto:** passos 3 e 5 (verificação) e o passo 6 (apagar a t6, irreversível).

## O problema (verificado ao vivo em 2026-09-30, SELECT read-only)

| Lado | O quê | Tabela | Evidência |
|---|---|---|---|
| Ingestão | `scripts/ingest_apply.py` → `supabase_writer.replace_chunks` | **`knowledge_chunks_t6`** (até agora) | `runner/plan_runner/supabase_writer.py` (antes de `fbad7bb`) |
| Retrieve | `agent-network-mcp/lib/knowledge.js:54` → RPC `match_knowledge` | **`knowledge_chunks`** | `agent-network-mcp/memory/schema.sql:45-58` |

- `knowledge_chunks_t6` tem 110 linhas e 33 fontes; `knowledge_chunks` tem 210 linhas e 88 fontes.
- Só 1 fonte se sobrepõe (`docs/knowledge/ai-findability.md`), e as suas 9 linhas já tinham sido copiadas à mão (`project='network-agents-setup'`).
- **Descoberto nesta sessão, mais grave:** existem **2 overloads** de `match_knowledge`, `(vector,text,int)` e `(vector,text,int,text)`. A chamada do MCP, com 3 argumentos com nome, dá `ERROR 42725: function match_knowledge(...) is not unique` (reproduzido no Postgres).
  - **Se o PostgREST resolver da mesma forma, o retrieve está partido para todos os agentes, não só para a t6.** Não foi confirmado pelo PostgREST: não há chamadas nos logs das últimas 24h e esta sessão não tem a chave anon.
- 11 linhas da t6 têm `agent_id` composto `marketing+produto-tech-transversal`. O retrieve filtra por igualdade, por isso esse `agent_id` nunca é encontrado.
- Os esquemas são compatíveis:
  - a `knowledge_chunks` já tem `project`, `content_hash`, `chunk_index`, `kb` e `updated_at`;
  - `source_path` → `source`;
  - os ids da t6 convertem para uuid (110/110);
  - ambas as tabelas usam `vector(768)`;
  - o embedder é o mesmo (`gemini-embedding-001`).

## Passos para o DEV (por ordem)

### 1. Correr a migração
Supabase → projecto `mpsuurqilnhsvbnjmrpm` → **SQL Editor** → colar [`scripts/migrate_t6_to_knowledge_chunks.sql`](../../scripts/migrate_t6_to_knowledge_chunks.sql) → Run.
- Corre numa única transacção e é idempotente.
- Se a verificação interna falhar, faz `RAISE` e não muda nada.
- Remove a overload de 4 argumentos. A definição exacta está no ficheiro, em comentário, para a poderes repor se precisares.
- Foi testado num Postgres 16 + pgvector local, com réplica do esquema: 2 execuções seguidas, contagens certas, ambiguidade resolvida.

### 2. Confirmar contagens
```sql
SELECT count(*) FROM knowledge_chunks WHERE project = 'network-agents-setup';  -- esperado 121
SELECT count(*) FROM knowledge_chunks;                                          -- esperado 322
SELECT count(*) FROM pg_proc WHERE proname = 'match_knowledge';                 -- esperado 1
SELECT source FROM match_knowledge(
  query_embedding => (SELECT embedding FROM knowledge_chunks WHERE source = 'docs/knowledge/geo-agent.md' LIMIT 1),
  match_agent_id => 'marketing', match_count => 3);                            -- deve incluir geo-agent.md
```
Registar aqui: `2026-09-30 — 121 / 322 / 1 / geo-agent: SIM` (reconfirmado por SELECT read-only no fim do dia: 121 / 322 / 1).

### 3. Correr o ingest e confirmar que escreve no sítio certo
**Atenção:** o workflow `ingest-knowledge` só **aplica** o ingest em `push` para a `main` (`.github/workflows/ingest-knowledge.yml:3-4,36`). O `workflow_dispatch` só faz o *dry-run* (`:33-34`). O writer corrigido está só na `claude/audit-completo` até haver merge. Até lá, um push para a `main` que toque em `docs/**/*.md` continua a escrever na **t6**.

Por isso, antes do merge, correr **localmente** a partir da `claude/audit-completo`, com o `.env` do PC (`DATABASE_URL`, `GEMINI_API_KEY`):
```bash
git checkout claude/audit-completo && git pull
python scripts/ingest_apply.py --max-chunks 5     # orçamento pequeno de embeddings
```
Depois:
```sql
SELECT max(updated_at) FROM knowledge_chunks WHERE project = 'network-agents-setup';  -- deve ser de hoje
SELECT max(updated_at) FROM knowledge_chunks_t6;                                     -- NÃO deve mudar
```
Se não houver delta (nenhum ficheiro mudou), o ingest não escreve nada, e isso está certo. Nesse caso a verificação fica para depois do merge.

### 4. Teste ingest → retrieve
Contra um Postgres **descartável** com pgvector, nunca o Supabase:
```bash
docker run -d --rm -p 5433:5432 -e POSTGRES_PASSWORD=pg pgvector/pgvector:pg16
cd runner && RAG_TEST_DATABASE_URL=postgresql://postgres:pg@localhost:5433/postgres python -m pytest tests/test_rag_canonical.py -v
```
Esperado: 6 passed: os 3 J3 e 3 ponta a ponta (`test_e2e_*`: ficheiro → `scripts/ingest_apply.py::apply_one` com embedder falso → `match_knowledge`). Sem `RAG_TEST_DATABASE_URL`, saem como *skipped*, com a razão; com `RAG_TEST_REQUIRED=1`, a falta da BD é um erro.

**No CI:** o job `test-rag` do `runner-tests.yml` corre isto em cada PR do runner, contra um serviço `pgvector/pgvector:pg16` descartável e com `RAG_TEST_REQUIRED=1` (PLANO item 10).

### 5. Teste real no MCP
Numa conversa com o conector do `agent-network-mcp`, pedir ao agente `marketing` algo sobre "GEO / answer-first". A resposta deve citar `[Fonte: docs/knowledge/geo-agent.md …]`.

### 6. (Depois de 1–5 verdes) Apagar a t6 — IRREVERSÍVEL
1. Backup: `pg_dump --data-only -t public.knowledge_chunks_t6 "$DATABASE_URL" > t6-backup.sql`
2. Correr [`scripts/drop_knowledge_chunks_t6.sql`](../../scripts/drop_knowledge_chunks_t6.sql). Aborta sozinho se alguma fonte da t6 não estiver na `knowledge_chunks`.

## Se algo falhar
| Sintoma | Causa provável |
|---|---|
| `migracao incompleta: N linhas da t6 sem par` | Linha da t6 com `chunk_index` repetido para o mesmo agente; colar o erro aqui |
| O MCP continua sem resultados depois do passo 1 | Confirmar que `pg_proc` tem 1 só `match_knowledge`; ver os logs do Vercel do `agent-network-mcp` |
| O ingest escreve na t6 | Correu código anterior a `fbad7bb` (ex.: push para a `main` antes do merge) |

```
(colar aqui logs de falhas)
```

## F3a: proveniência no retrieve (2026-10-06, P-26 = A)

> ADR: `docs/architecture/adr/ADR-F3-PROVENANCE-RETRIEVE.md`. Migração: `scripts/migrations/f3_provenance_retrieve.sql`. Testes: `runner/tests/test_f3_provenance.py` (Postgres + pgvector, no job `test-rag`) e `runner/tests/test_provenance.py`.

**O que muda (tudo aditivo):**
- **`knowledge_sources` ganha** `uri`, `final_url`, `title`, `document_type`, `retrieved_at`, `status` (`active` por omissão; CHECK `active`/`superseded`/`revoked`/`expired`/`deleted`), `jurisdiction`, `effective_from`, `effective_until` e `meta` (jsonb).
- **`knowledge_chunks` ganha** `locator` (`l.<início>-<fim>`, que o chunker já calculava).
- **RPC nova `match_knowledge_v2(query_embedding, match_agent_id, match_count, filters jsonb)`:**
  - devolve a proveniência por `LEFT JOIN` à `knowledge_sources`, só para linhas do T6 (`project = 'network-agents-setup'`);
  - filtros: `status` (`active` por omissão, `any` desliga o filtro), `jurisdiction`, `document_type` e `valid_at` (por omissão, agora).
- **O `match_knowledge` antigo não muda.**
- **Writer** (`runner/plan_runner/supabase_writer.py`): `has_f3_columns` detecta a migração. Sem ela, escreve exactamente como antes; com ela, grava a proveniência do `<nome>.meta.yaml` e o `locator`.
- **`scripts/ingest_apply.py`:**
  - um sidecar inválido dá `INVALID_META`, sem escrita, e conta como falha da corrida (regra 3);
  - com o `.md` igual e o sidecar mudado, dá `META_UPDATED`, sem embeddings (por exemplo, um documento revogado deixa de ser devolvido);
  - sem sidecar, a proveniência vem do git (`uri` = path, `document_type` = `md`, `status` = `active`).

**Ordem segura para o DEV** (nenhum passo parte produção):
1. **Merge do PR do NAS.** O `ingest-knowledge` corre com o writer novo. Sem a migração, detecta-a em falta e escreve como antes.
2. **Correr `scripts/migrations/f3_provenance_retrieve.sql`** no SQL Editor do Supabase (`agent-network-memory`). É idempotente e pode correr outra vez sem efeito. As queries de controlo estão no fim do ficheiro.
3. **Esperado logo a seguir:**
   - as linhas antigas da `knowledge_sources` ficam com `status = 'active'` e o resto `NULL`;
   - o `locator` fica `NULL` nas linhas antigas.
   - Na próxima corrida do `ingest-knowledge`, as fontes iguais passam de `UNCHANGED` a `META_UPDATED` **uma vez** (passam a ter `uri` e `document_type`), sem embeddings. O `locator` só aparece quando cada fonte for re-ingerida.
4. **Merge do PR do MCP (`agent-network-mcp` #19) e ligar `KNOWLEDGE_RPC_V2=1`** nas env vars da Vercel (Production), seguido de redeploy. Até lá, o MCP usa o `match_knowledge` antigo. A flag desliga-se a qualquer momento (rollback sem SQL).
   - Se a flag for ligada antes do passo 2, o MCP detecta `PGRST202` (a função não existe), regista um aviso e cai para o `match_knowledge`: o RAG não fica vazio.
5. **Confirmar:** uma chamada a `retrieve_knowledge` traz `citation.uri`, `citation.locator`, `metadata.status`… e os `filters` passam a ter efeito.
   - **Atenção:** o `provenance_ok` do `l5_eval` **não distingue** a v1 da v2, porque só olha para o `citation.source`, que a v1 também devolve (R-006). O sinal certo é o `metadata`: `null` na v1, preenchido na v2.
   - Comando de 1 linha (em `runner/`, com o `MCP_URL`, o `MCP_API_KEY` e o `VERCEL_PROTECTION_BYPASS` no ambiente). Imprime só `v1` ou `v2`, sem conteúdo:
     ```powershell
     python -c "from plan_runner.mcp_knowledge import McpKnowledge as M; h=M().retrieve('security','auditoria defensiva',top_k=1,filters=None,require_citations=True); print('v2' if h and h[0].get('metadata') else 'v1')"
     ```
   - **Estado em 2026-10-06: v2 activa em produção.** SQL aplicado (verificado no catálogo); `l5_eval` com a flag sem regressão; um `tools/call` do `retrieve_knowledge` (`kb=security`, `top_k=1`) devolveu `citation.uri` e `metadata` preenchido (`document_type` = `md`, `status` = `active`). O `locator` vem `null` nas linhas antigas até cada fonte ser re-ingerida (passo 3). **F3a FECHADO.**

**Rollback:** desligar a flag (passo 4) devolve o MCP ao caminho antigo. As colunas novas e a v2 podem ficar: não mudam nada do que existia.

## F3c: cobertura de `docs/knowledge/` (2026-10-06, P-35 = A, P-36 = A)

> Decisões do maestro de 2026-10-06 (`docs/initiatives/PENDENCIAS.md` §10). A regra fica em teste: **todo o `.md` de `docs/knowledge/` está no MANIFEST ou no `EXCLUDED`** de `scripts/ingest_delta.py`, com a razão (`runner/tests/test_knowledge_coverage.py`, que corre também quando muda `docs/knowledge/**`).

**Antes:** 69 `.md` em `docs/knowledge/`, 37 no MANIFEST e 32 sem decisão (eram 33 no `L5-F0-REVALIDATION.md` §2; o `security-agents-stack.md` entrou no F0.4).
**A t6 não faz parte do F3c:** as 33 fontes da `knowledge_chunks_t6` estão todas na `knowledge_chunks` (SELECT só de leitura, 2026-10-06). Apagá-la é o F0.12.

| Grupo | Ficheiros | Chunks | Decisão | Razão |
|---|---:|---:|---|---|
| `marketing/` | 7 | 15 | **MANIFEST** (`marketing`, P1) | Lidos pelos agentes `creative_review`, `influencer`, `media_buyer`, `ugc` e `editor_video` e pelas skills `creative_review`, `critic` e `seo_brief`; o `kb: marketing` tem 16 dos 17 blocos `knowledge:` dos planos |
| `imported-from-production/` (conteúdo) | 7 | 109 | EXCLUDED: duplicado | Cópias ou resumos de `agent-network-mcp/ingestion/`, cujo conteúdo já está em produção pelo MCP (`project` NULL: "ECC marketing-agent", "ECC planner+architect+…", etc.). O teste confirma o cabeçalho de cópia |
| `imported-from-production/` (2 docs) | 2 | 5 | EXCLUDED: cópia sem consumidor | `ADDENDUM_PADROES_ORQUESTRADORES.md` e `PADROES_ERROS_IA.md` |
| `design/` | 10 | 22 | EXCLUDED (P-36 = A) | Sem consumidor de `kb: design`; as skills de design lêem o ficheiro. O teste falha se um plano passar a usar `kb: design` → **F3c-DESIGN-1** |
| `imported-from-harnesses.md` | 1 | 17 | EXCLUDED: sem consumidor | Só citado em docs de portfólio |
| READMEs, MANIFEST e `skills-map.md` | 5 | 21 | EXCLUDED: meta | Índices e mapas |

**Nenhum ficheiro é apagado do git.** O `EXCLUDED` só diz "não vai para o RAG".

**Escrita em produção (W-prod, no merge):** o push para a `main` toca em `scripts/ingest_delta.py` e dispara o `ingest-knowledge`. As 39 fontes anteriores ficam `UNCHANGED`; as 7 de marketing são ingeridas (~15 chunks, dentro do `--max-chunks 50` por omissão). Controlo depois da corrida (só leitura):

```sql
SELECT source, agent_id, count(*) AS chunks
FROM knowledge_chunks
WHERE project = 'network-agents-setup' AND source LIKE 'docs/knowledge/marketing/%'
GROUP BY source, agent_id ORDER BY source;   -- esperado: 7 fontes, agent_id marketing, 15 chunks no total
```

## F3b: validade das fontes (2026-10-06, P-27 = C, P-28 = C, P-29 = A)

> Política em `config/knowledge-validity.yaml`; código em `runner/plan_runner/validity.py`; aplicada pelo `scripts/ingest_apply.py` a cada fonte. **Sem SQL novo**: a `match_knowledge_v2` (F3a) já filtra por `effective_from`/`effective_until` contra o `valid_at` (por omissão, agora).

| Classe | Como se reconhece | O que exige | Quem define a data |
|---|---|---|---|
| (nenhuma) | Tudo o resto: playbooks e checklists | Nada | Ninguém. Vale até `status: superseded` ou `revoked` no sidecar |
| `legal` | `docs/knowledge/legal/**`, ou `validity_class: legal` no sidecar | `effective_from` | O autor, no `<nome>.meta.yaml`, a partir da própria lei |
| `market_data` | `docs/knowledge/imobiliario/**`, ou `validity_class: market_data` | `effective_until` | O autor, no sidecar |
| `web` | `uri` com `http`/`https` (páginas do F2) | — | O ingest: `effective_until` = `retrieved_at` + 90 dias, salvo se o autor declarar outra. Fica no `meta` como `effective_until_source: ttl:90d` |

**No ingest:**
- sidecar de classe datada **sem** a data → `INVALID_META`: a fonte não entra e a corrida falha (regra 3);
- classe datada **sem sidecar** → entra como antes, com `AVISO` no fim da corrida (`validity_warnings=N`). Não se inventam datas. Hoje há 2 casos: `legal/direito-br-pt.md` e `imobiliario/fipezap.md` (item **F3b-VAL-1**: o autor dá as datas reais);
- `validity_class: <id>` no sidecar fixa a classe (ex.: uma lei convertida pelo F1 para `docs/knowledge/ingested/`).

**Expirados (P-29 = A):** ficam na BD e saem do retrieve por omissão. Para auditoria, usar `filters: {"valid_at": "<data antiga>"}` ou `{"status": "any"}`.

**Relatório local** (só leitura do git; sem BD, sem workflow):

```bash
python scripts/validity_report.py              # o que está expirado, a expirar em 30 dias ou sem a data exigida
python scripts/validity_report.py --at 2027-01-01
python scripts/validity_report.py --strict     # exit 1 se houver expirados ou datas em falta
```

**Exemplo de sidecar** (ao lado de `docs/knowledge/legal/direito-br-pt.md`; o `content_hash` é o SHA-256 do `.md`):

```yaml
uri: docs/knowledge/legal/direito-br-pt.md
title: Direito BR-PT
document_type: md
retrieved_at: 2026-10-06T00:00:00+00:00
content_hash: <sha256 do .md>
status: active
jurisdiction: PT
effective_from: 2024-01-01   # a data da própria fonte, nunca inventada
```
