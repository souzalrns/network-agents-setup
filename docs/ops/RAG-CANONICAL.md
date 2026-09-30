# RAG canónico — migração t6 → knowledge_chunks (J3)

> **Estado: PENDENTE-DEV.** O código está pronto (o ingest já escreve na `knowledge_chunks`). A migração dos dados e a correcção do `match_knowledge` **não foram executadas** no Supabase. Ninguém nesta sessão tinha ordem para escrever em produção.

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
Registar aqui: `____-__-__ — 121 / 322 / 1 / geo-agent: SIM / NÃO`.

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
Esperado: 3 passed. Sem `RAG_TEST_DATABASE_URL`, os 3 testes saem como *skipped*, com a razão.

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
