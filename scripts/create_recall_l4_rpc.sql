-- L4 -- recall_l4: le as memorias de uma CADEIA de ambitos (D3; scopes.md).
--
-- Correr DEPOIS de create_memory_l4_table.sql. Idempotente. Codigo:
-- runner/plan_runner/memory_l4.py::recall. Operacao: docs/ops/MEMORY-L4.md.
--
-- O caller declara a cadeia que lhe pertence (ex.: global:global, org:acme,
-- project:site-x, agent:marketing.copy_social) em dois arrays paralelos; so
-- linhas cujo (scope_kind, scope_id) esteja nessa cadeia saem -- nunca as de
-- outro projecto/agente ("intersecta com as permissoes", scopes.md:9).
--
-- * Nunca devolve archived/superseded nem expiradas (expires_at no passado).
-- * candidate so com include_candidates => true (ainda sem gate humano).
-- * Com query_embedding: ordena por similaridade (as sem embedding no fim);
--   sem query_embedding: as mais recentes primeiro.
-- * match_count limitado a 1..50 (contracts.md:46). Tags: a memoria tem de ter
--   TODAS as tags pedidas.
--
-- SECURITY INVOKER (omissao): corre com as permissoes de quem chama. EXECUTE so
-- para o service_role (o runner usa o DATABASE_URL, role postgres).

CREATE OR REPLACE FUNCTION public.recall_l4(
  query_embedding   vector(768),
  scope_kinds       text[],
  scope_ids         text[],
  match_count       int     DEFAULT 10,
  filter_tags       text[]  DEFAULT NULL,
  include_candidates boolean DEFAULT false
)
RETURNS TABLE (
  id uuid, scope_kind text, scope_id text, subject text, statement text, status text,
  confidence real, tags text[], source_run_id text, created_at timestamptz,
  updated_at timestamptz, similarity double precision
)
LANGUAGE sql STABLE AS $$
  WITH chain AS (
    SELECT k AS scope_kind, i AS scope_id FROM unnest(scope_kinds, scope_ids) AS c(k, i)
  )
  SELECT m.id, m.scope_kind, m.scope_id, m.subject, m.statement, m.status, m.confidence,
         m.tags, m.source_run_id, m.created_at, m.updated_at,
         CASE WHEN query_embedding IS NULL OR m.embedding IS NULL THEN NULL
              ELSE 1 - (m.embedding <=> query_embedding) END AS similarity
  FROM public.memory_l4 m
  JOIN chain c ON c.scope_kind = m.scope_kind AND c.scope_id = m.scope_id
  WHERE (m.status = 'active' OR (include_candidates AND m.status = 'candidate'))
    AND (m.expires_at IS NULL OR m.expires_at > now())
    AND (filter_tags IS NULL OR m.tags @> filter_tags)
  ORDER BY
    CASE WHEN query_embedding IS NULL OR m.embedding IS NULL THEN 1 ELSE 0 END,
    CASE WHEN query_embedding IS NULL OR m.embedding IS NULL THEN NULL
         ELSE m.embedding <=> query_embedding END,
    m.updated_at DESC
  LIMIT greatest(1, least(coalesce(match_count, 10), 50));
$$;

REVOKE ALL ON FUNCTION public.recall_l4(vector, text[], text[], int, text[], boolean) FROM PUBLIC;

DO $$
BEGIN
  IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'anon') THEN
    EXECUTE 'REVOKE ALL ON FUNCTION public.recall_l4(vector, text[], text[], int, text[], boolean) FROM anon';
  END IF;
  IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'authenticated') THEN
    EXECUTE 'REVOKE ALL ON FUNCTION public.recall_l4(vector, text[], text[], int, text[], boolean) FROM authenticated';
  END IF;
  IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'service_role') THEN
    EXECUTE 'GRANT EXECUTE ON FUNCTION public.recall_l4(vector, text[], text[], int, text[], boolean) TO service_role';
  END IF;
END $$;
