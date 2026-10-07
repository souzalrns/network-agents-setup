-- AU-11: schema canónico do RAG (L5), num só sítio.
--
-- Fonte de verdade das tabelas que o ingest T6 escreve (runner/plan_runner/
-- supabase_writer.py) e que o retrieve lê (match_knowledge, chamado pelo
-- agent-network-mcp em lib/knowledge.js). O teste ingest -> retrieve
-- (runner/tests/test_rag_canonical.py, job test-rag do CI) cria o schema a
-- partir DESTE ficheiro, por isso qualquer mudança aqui é testada.
--
-- Estado de produção (projecto agent-network-memory): estas tabelas já existem.
-- Colunas verificadas ao vivo em 2026-09-30 (J3). Índices extra, RLS e grants de
-- produção NÃO estão aqui nem foram verificados; ver a query de controlo no fim.
-- NÃO correr em produção sem ordem do DEV. É idempotente (IF NOT EXISTS), por
-- isso correr por cima do que existe não apaga nem altera dados.
--
-- Histórico:
--   - knowledge_chunks nasceu no agent-network-mcp (memory/schema.sql:29-36, só as
--     colunas base); as colunas do T6 (project, content_hash, chunk_index, kb,
--     updated_at) foram acrescentadas no J3 e não estavam versionadas em lado nenhum.
--   - knowledge_sources só existia como DDL no teste.
--   - A knowledge_chunks_t6 (scripts/create_t6_chunks_table.sql, modelo Prisma
--     KnowledgeChunk) foi abandonada no J3 (scripts/drop_knowledge_chunks_t6.sql).

CREATE EXTENSION IF NOT EXISTS vector;

-- Registo de fontes do ingest (1 linha por ficheiro do MANIFEST).
CREATE TABLE IF NOT EXISTS knowledge_sources (
  source_path      text PRIMARY KEY,
  content_hash     text NOT NULL,
  agent_id         text NOT NULL,
  priority         text NOT NULL DEFAULT 'P1',
  last_ingested_at timestamptz NOT NULL DEFAULT now(),
  chunk_count      int NOT NULL DEFAULT 0,
  git_sha          text,
  size_bytes       int,
  updated_at       timestamptz NOT NULL DEFAULT now()
);

-- Tabela canónica de chunks (J3). Partilhada com o agent-network-mcp: as linhas
-- do T6 têm project = 'network-agents-setup'; as do MCP têm project NULL.
CREATE TABLE IF NOT EXISTS knowledge_chunks (
  id         uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  agent_id   text NOT NULL,
  source     text NOT NULL,
  content    text NOT NULL,
  embedding  vector(768),
  created_at timestamptz DEFAULT now()
);
ALTER TABLE knowledge_chunks ADD COLUMN IF NOT EXISTS project      text;
ALTER TABLE knowledge_chunks ADD COLUMN IF NOT EXISTS content_hash text;
ALTER TABLE knowledge_chunks ADD COLUMN IF NOT EXISTS chunk_index  integer;
ALTER TABLE knowledge_chunks ADD COLUMN IF NOT EXISTS kb           text;
-- R-005 / P-20: sem DEFAULT (o 'marketing' classificava mal as linhas do MCP). Quem
-- insere sem kb fica com kb = agent_id pelo trigger de
-- scripts/migrations/r005_kb_default.sql, que também reclassifica a produção.
ALTER TABLE knowledge_chunks ALTER COLUMN kb DROP DEFAULT;
ALTER TABLE knowledge_chunks ADD COLUMN IF NOT EXISTS updated_at   timestamptz DEFAULT now();

CREATE INDEX IF NOT EXISTS idx_knowledge_chunks_agent ON knowledge_chunks (agent_id);

-- F3a (2026-10-06, P-26 = A): a proveniência no retrieve está na migração ADITIVA
-- scripts/migrations/f3_provenance_retrieve.sql (colunas novas + match_knowledge_v2).
-- Schema completo = este ficheiro + essa migração (os testes aplicam os 2, por esta ordem).
-- Retrieve: o único overload (o de 4 argumentos foi removido no J3).
-- Igual a agent-network-mcp/memory/schema.sql:45-58.
CREATE OR REPLACE FUNCTION match_knowledge(
  query_embedding vector(768),
  match_agent_id text,
  match_count int DEFAULT 4
)
RETURNS TABLE (id uuid, content text, source text, similarity float)
LANGUAGE sql STABLE
AS $$
  SELECT id, content, source, 1 - (embedding <=> query_embedding) AS similarity
  FROM knowledge_chunks
  WHERE agent_id = match_agent_id OR agent_id = 'global'
  ORDER BY embedding <=> query_embedding
  LIMIT match_count;
$$;

-- Query de controlo (SÓ LEITURA, para o DEV comparar com produção):
--   SELECT table_name, column_name, data_type, column_default, is_nullable
--   FROM information_schema.columns
--   WHERE table_schema = 'public' AND table_name IN ('knowledge_chunks', 'knowledge_sources')
--   ORDER BY table_name, ordinal_position;
--   SELECT indexname, indexdef FROM pg_indexes WHERE tablename IN ('knowledge_chunks', 'knowledge_sources');
