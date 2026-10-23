-- F3b: autoridade e conflitos no retrieve (PENDENCIAS §10: P-31 = D, P-32 = B, P-33 = B).
--
-- ADITIVA e idempotente, mesmo padrão do F3a (scripts/migrations/f3_provenance_retrieve.sql,
-- que tem de ter corrido antes: a v3 lê as colunas e o `meta` que ele criou):
--   - sem colunas novas: a autoridade e o `superseded_by` vêm do `meta` (jsonb) da
--     knowledge_sources, onde o ingest_apply já os grava (runner/plan_runner/authority.py);
--   - 2 CHECK novos sobre o `meta` (a BD recusa um nível desconhecido ou um `superseded_by`
--     sem `status = 'superseded'`) e 1 função nova;
--   - match_knowledge e match_knowledge_v2 NÃO mudam. O MCP continua na v2 até a feature
--     flag KNOWLEDGE_RPC_V3 ser ligada na Vercel (ANM:lib/knowledge.js).
--
-- Quem corre: o DEV, no SQL Editor do Supabase (agent-network-memory), depois do merge.
-- Antes de o correr: o ingest pode gravar `authority` no `meta` (fica lá, sem efeito até à v3).
--
-- Testado contra Postgres + pgvector no CI (runner/tests/test_f3b_authority.py): sobre o
-- schema com a F3a e dados já gravados, 2 vezes.

BEGIN;

-- 1. A BD recusa o que o ingest já recusa (INVALID_META). Os níveis são os da P-32 = B.
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'knowledge_sources_authority_check'
      AND conrelid = 'knowledge_sources'::regclass
  ) THEN
    ALTER TABLE knowledge_sources ADD CONSTRAINT knowledge_sources_authority_check
      CHECK (meta->>'authority' IS NULL
             OR meta->>'authority' IN ('oficial', 'curado', 'experimental'));
  END IF;
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'knowledge_sources_superseded_by_check'
      AND conrelid = 'knowledge_sources'::regclass
  ) THEN
    ALTER TABLE knowledge_sources ADD CONSTRAINT knowledge_sources_superseded_by_check
      CHECK (meta->>'superseded_by' IS NULL OR status = 'superseded');
  END IF;
END $$;

-- 2. Retrieve v3 = v2 + `authority` + `superseded_by` + o filtro `min_authority`.
--    Mesmos filtros da v2 (status, jurisdiction, document_type, valid_at), mais:
--      min_authority  'oficial' | 'curado' | 'experimental'; fica de fora o que for mais
--                     fraco. Por omissão não filtra (P-33 = B: devolve tudo, com a
--                     autoridade no metadata). Valor desconhecido = erro (nunca um RAG
--                     vazio em silêncio).
--    Sem autoridade gravada = 'curado' (as fontes de hoje e as linhas do MCP, P-32 = B).
--    Sem reordenação: a ordem continua a ser a da semelhança (P-33 = B).
CREATE OR REPLACE FUNCTION match_knowledge_v3(
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
  effective_until timestamptz,
  authority text,
  superseded_by text
)
LANGUAGE plpgsql STABLE
AS $$
#variable_conflict use_column
DECLARE
  min_rank int := 1;
BEGIN
  IF filters ? 'min_authority' THEN
    min_rank := CASE filters->>'min_authority'
      WHEN 'oficial' THEN 3 WHEN 'curado' THEN 2 WHEN 'experimental' THEN 1 END;
    IF min_rank IS NULL THEN
      RAISE EXCEPTION 'min_authority invalido: % (oficial, curado ou experimental)',
        filters->>'min_authority' USING ERRCODE = '22023';
    END IF;
  END IF;

  RETURN QUERY
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
    (1 - (c.embedding <=> query_embedding))::float,
    c.agent_id,
    c.kb,
    c.locator,
    COALESCE(s.content_hash, c.content_hash),
    COALESCE(s.uri, c.source),
    s.final_url,
    s.title,
    COALESCE(s.document_type, CASE WHEN c.source LIKE '%.md' THEN 'md' END),
    s.retrieved_at,
    COALESCE(s.status, 'active'),
    s.jurisdiction,
    s.effective_from,
    s.effective_until,
    COALESCE(s.meta->>'authority', 'curado'),
    s.meta->>'superseded_by'
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
    AND CASE COALESCE(s.meta->>'authority', 'curado')
          WHEN 'oficial' THEN 3 WHEN 'curado' THEN 2 WHEN 'experimental' THEN 1 ELSE 0
        END >= min_rank
  ORDER BY c.embedding <=> query_embedding
  LIMIT match_count;
END;
$$;

COMMIT;

-- Query de controlo ANTES (SÓ LEITURA). Tem de dar 0 linhas; se der, os CHECK falham e a
-- transacção inteira volta atrás (nada muda). Corrigir o sidecar e re-ingerir primeiro:
--   SELECT source_path, status, meta FROM knowledge_sources
--   WHERE (meta->>'authority' IS NOT NULL
--          AND meta->>'authority' NOT IN ('oficial', 'curado', 'experimental'))
--      OR (meta->>'superseded_by' IS NOT NULL AND status <> 'superseded');
--
-- Queries de controlo DEPOIS (SÓ LEITURA):
--   SELECT proname, pg_get_function_identity_arguments(oid) FROM pg_proc
--   WHERE proname IN ('match_knowledge', 'match_knowledge_v2', 'match_knowledge_v3');
--   SELECT conname FROM pg_constraint WHERE conrelid = 'knowledge_sources'::regclass
--   AND conname LIKE 'knowledge_sources_%_check';
--   SELECT COALESCE(meta->>'authority', 'curado') AS authority, count(*)
--   FROM knowledge_sources GROUP BY 1;
-- Esperado: as 3 funções (as 2 antigas inalteradas), os 3 CHECK (status, authority,
-- superseded_by) e, hoje, todas as fontes em 'curado' (P-32 = B).
