-- F3a: proveniência no retrieve (docs/architecture/adr/ADR-F3-PROVENANCE-RETRIEVE.md, P-26 = A).
--
-- ADITIVA e idempotente:
--   - corre sobre o schema de produção actual (scripts/rag_schema.sql) e pode correr 2 vezes;
--   - não altera nem apaga nada do que existe: só ADD COLUMN IF NOT EXISTS, 1 CHECK novo e
--     1 função nova;
--   - o match_knowledge antigo NÃO muda. O MCP continua a usá-lo até a feature flag
--     KNOWLEDGE_RPC_V2 ser ligada na Vercel (ANM:lib/knowledge.js).
--
-- Quem corre: o DEV, no SQL Editor do Supabase (agent-network-memory), depois do merge.
-- Antes de o correr, o writer do T6 (runner/plan_runner/supabase_writer.py) detecta que as
-- colunas não existem e escreve como antes; depois de o correr, passa a gravar a proveniência.
--
-- Testado contra Postgres + pgvector no CI (runner/tests/test_f3_provenance.py): sobre o
-- schema actual, 2 vezes, com dados antigos já gravados.

BEGIN;

-- 1. Proveniência por fonte (ADR-INGESTION-PRIMITIVES §4; vem do <nome>.meta.yaml do F1/F2).
ALTER TABLE knowledge_sources ADD COLUMN IF NOT EXISTS uri             text;
ALTER TABLE knowledge_sources ADD COLUMN IF NOT EXISTS final_url       text;
ALTER TABLE knowledge_sources ADD COLUMN IF NOT EXISTS title           text;
ALTER TABLE knowledge_sources ADD COLUMN IF NOT EXISTS document_type   text;
ALTER TABLE knowledge_sources ADD COLUMN IF NOT EXISTS retrieved_at    timestamptz;
ALTER TABLE knowledge_sources ADD COLUMN IF NOT EXISTS status          text NOT NULL DEFAULT 'active';
ALTER TABLE knowledge_sources ADD COLUMN IF NOT EXISTS jurisdiction    text;
ALTER TABLE knowledge_sources ADD COLUMN IF NOT EXISTS effective_from  timestamptz;
ALTER TABLE knowledge_sources ADD COLUMN IF NOT EXISTS effective_until timestamptz;
ALTER TABLE knowledge_sources ADD COLUMN IF NOT EXISTS meta            jsonb NOT NULL DEFAULT '{}'::jsonb;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'knowledge_sources_status_check'
      AND conrelid = 'knowledge_sources'::regclass
  ) THEN
    ALTER TABLE knowledge_sources ADD CONSTRAINT knowledge_sources_status_check
      CHECK (status IN ('active', 'superseded', 'revoked', 'expired', 'deleted'));
  END IF;
END $$;

-- 2. Posição do excerto na fonte (o chunker já calcula `l.<início>-<fim>`; perdia-se na escrita).
ALTER TABLE knowledge_chunks ADD COLUMN IF NOT EXISTS locator text;

-- 3. Retrieve com proveniência e filtros. O JOIN só liga linhas do T6 (project =
--    'network-agents-setup'): uma linha do MCP com o mesmo `source` não herda proveniência.
--    Filtros (jsonb, todos opcionais):
--      status        'active' por omissão; 'any' desliga o filtro
--      jurisdiction  igualdade
--      document_type igualdade ('md' para os .md sem sidecar)
--      valid_at      instante ISO 8601; por omissão now(). Fica de fora o que ainda não
--                    vigora (effective_from > valid_at) ou já expirou (effective_until <= valid_at)
CREATE OR REPLACE FUNCTION match_knowledge_v2(
  query_embedding vector(768),
  match_agent_id text,
  match_count int DEFAULT 4,
  filters jsonb DEFAULT '{}'::jsonb
)
RETURNS TABLE (
  id uuid,
  content text,
  source text,
  similarity float,
  agent_id text,
  kb text,
  locator text,
  content_hash text,
  uri text,
  final_url text,
  title text,
  document_type text,
  retrieved_at timestamptz,
  status text,
  jurisdiction text,
  effective_from timestamptz,
  effective_until timestamptz
)
LANGUAGE sql STABLE
AS $$
  WITH f AS (
    SELECT
      COALESCE(filters->>'status', 'active') AS status,
      filters->>'jurisdiction' AS jurisdiction,
      filters->>'document_type' AS document_type,
      COALESCE((filters->>'valid_at')::timestamptz, now()) AS valid_at
  )
  SELECT
    c.id,
    c.content,
    c.source,
    1 - (c.embedding <=> query_embedding) AS similarity,
    c.agent_id,
    c.kb,
    c.locator,
    COALESCE(s.content_hash, c.content_hash) AS content_hash,
    COALESCE(s.uri, c.source) AS uri,
    s.final_url,
    s.title,
    COALESCE(s.document_type, CASE WHEN c.source LIKE '%.md' THEN 'md' END) AS document_type,
    s.retrieved_at,
    COALESCE(s.status, 'active') AS status,
    s.jurisdiction,
    s.effective_from,
    s.effective_until
  FROM knowledge_chunks c
  CROSS JOIN f
  LEFT JOIN knowledge_sources s
    ON s.source_path = c.source AND c.project = 'network-agents-setup'
  WHERE (c.agent_id = match_agent_id OR c.agent_id = 'global')
    AND (f.status = 'any' OR COALESCE(s.status, 'active') = f.status)
    AND (f.jurisdiction IS NULL OR s.jurisdiction = f.jurisdiction)
    AND (f.document_type IS NULL
         OR COALESCE(s.document_type, CASE WHEN c.source LIKE '%.md' THEN 'md' END) = f.document_type)
    AND (s.effective_from IS NULL OR s.effective_from <= f.valid_at)
    AND (s.effective_until IS NULL OR s.effective_until > f.valid_at)
  ORDER BY c.embedding <=> query_embedding
  LIMIT match_count;
$$;

COMMIT;

-- Queries de controlo (SÓ LEITURA), antes e depois:
--   SELECT column_name, data_type, column_default FROM information_schema.columns
--   WHERE table_schema = 'public' AND table_name = 'knowledge_sources' ORDER BY ordinal_position;
--   SELECT count(*) FILTER (WHERE locator IS NOT NULL) AS com_locator, count(*) AS total
--   FROM knowledge_chunks;
--   SELECT proname, pg_get_function_identity_arguments(oid) FROM pg_proc
--   WHERE proname IN ('match_knowledge', 'match_knowledge_v2');
-- Esperado depois: as 10 colunas novas na knowledge_sources (status = 'active' em todas as
-- linhas antigas), a coluna locator (NULL nas linhas antigas até à próxima re-ingestão),
-- e as 2 funções (a antiga inalterada).
