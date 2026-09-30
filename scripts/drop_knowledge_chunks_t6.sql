-- J3 — passo FINAL e IRREVERSÍVEL: apagar a knowledge_chunks_t6.
--
-- Só correr DEPOIS de:
--   1. scripts/migrate_t6_to_knowledge_chunks.sql ter corrido sem erro;
--   2. o ingest (ingest-knowledge.yml) ter corrido pelo menos 1 vez a escrever
--      na knowledge_chunks (supabase_writer.py já aponta para lá);
--   3. um backup da t6:  pg_dump --data-only -t public.knowledge_chunks_t6 "$DATABASE_URL" > t6-backup.sql
-- A knowledge_sources fica: continua a ser o registo de fontes do ingest.

BEGIN;

DO $$
DECLARE missing int;
BEGIN
  SELECT count(*) INTO missing
  FROM public.knowledge_chunks_t6 t
  CROSS JOIN LATERAL unnest(string_to_array(t.agent_id, '+')) AS a(agent_id)
  WHERE NOT EXISTS (
    SELECT 1 FROM public.knowledge_chunks k
    WHERE k.project = 'network-agents-setup' AND k.agent_id = a.agent_id
      AND k.source = t.source_path
  );
  IF missing > 0 THEN
    RAISE EXCEPTION 'abortado: % linhas da t6 sem fonte correspondente na knowledge_chunks', missing;
  END IF;
END $$;

DROP TABLE public.knowledge_chunks_t6;

COMMIT;
