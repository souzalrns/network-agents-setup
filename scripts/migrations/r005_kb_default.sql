-- R-005 / P-20 (2026-10-07): o `kb` das linhas do MCP deixa de vir do DEFAULT.
--
-- Causa (verificada em produção a 2026-10-07, information_schema.columns):
--   knowledge_chunks.kb  text  DEFAULT 'marketing'  NULL permitido
-- e o insert do MCP (agent-network-mcp lib/knowledge.js, ingestDocument) não definia
-- o kb. As 201 linhas do MCP (project IS NULL) ficaram todas com kb = 'marketing',
-- de 18 agent_id diferentes. As linhas do T6 (project = 'network-agents-setup') têm
-- sempre kb explícito (supabase_writer) e não são tocadas.
--
-- A correcção tem 3 partes:
--   1. schema: sem DEFAULT; um trigger põe kb = agent_id quando o insert não traz kb
--      (um DEFAULT não pode ler outra coluna). Vale para qualquer writer, mesmo um
--      que ainda não envie o kb;
--   2. app: o MCP grava o kb explícito (agent-network-mcp, PR "write kb explicitly
--      on MCP ingest");
--   3. dados: reclassifica as 201 linhas. kb = agent_id (o que o retrieve_knowledge
--      chama kb); a fonte ECC "security-reviewer + database-reviewer" (8 linhas,
--      agent_id revisor-codigo) vai para kb = 'security'. O agent_id não muda, por
--      isso a pesquisa (que filtra por agent_id) devolve o mesmo que antes.
--
-- Idempotente: pode correr 2x. A reclassificação corre uma vez só (marca no
-- COMMENT da coluna kb); numa 2.ª execução não toca em linhas gravadas depois com
-- kb = 'marketing' de propósito.
--
-- Aplicar: o DEV, no SQL Editor do Supabase (escreve em produção). De preferência
-- depois do deploy do MCP, mas a ordem inversa também é segura (o trigger cobre-a).
-- Verificação depois de aplicar:
--   SELECT column_default FROM information_schema.columns
--    WHERE table_schema = 'public' AND table_name = 'knowledge_chunks' AND column_name = 'kb';
--   -- esperado: NULL
--   SELECT kb, count(*) FROM public.knowledge_chunks WHERE project IS NULL GROUP BY kb ORDER BY kb;
--   -- esperado (2026-10-07): 19 valores (os 18 agent_id + security); marketing = 3,
--   -- security = 8, revisor-codigo = 8, nenhum NULL

BEGIN;

DO $$
DECLARE
  done boolean;
  n_sec integer;
  n_agent integer;
BEGIN
  SELECT col_description(c.oid, a.attnum) LIKE 'R-005%' INTO done
    FROM pg_class c
    JOIN pg_attribute a ON a.attrelid = c.oid AND a.attname = 'kb'
   WHERE c.oid = to_regclass('knowledge_chunks');

  IF coalesce(done, false) THEN
    RAISE NOTICE 'R-005: reclassificacao ja feita (nada a fazer)';
  ELSE
    UPDATE knowledge_chunks SET kb = 'security'
     WHERE project IS NULL AND kb = 'marketing'
       AND agent_id = 'revisor-codigo' AND source = 'ECC security-reviewer + database-reviewer';
    GET DIAGNOSTICS n_sec = row_count;

    UPDATE knowledge_chunks SET kb = agent_id
     WHERE project IS NULL AND (kb IS NULL OR (kb = 'marketing' AND agent_id <> 'marketing'));
    GET DIAGNOSTICS n_agent = row_count;

    RAISE NOTICE 'R-005: % linhas para security, % linhas com kb = agent_id', n_sec, n_agent;
  END IF;
END;
$$;

-- Marca de "já aplicado": a reclassificação acima corre uma vez só, mesmo que o
-- DEFAULT já tenha sido tirado por outro caminho (ex.: scripts/rag_schema.sql).
COMMENT ON COLUMN knowledge_chunks.kb IS
  'R-005 aplicado: sem DEFAULT; o trigger knowledge_chunks_default_kb põe kb = agent_id quando o insert não traz kb.';

ALTER TABLE knowledge_chunks ALTER COLUMN kb DROP DEFAULT;

CREATE OR REPLACE FUNCTION knowledge_chunks_default_kb()
RETURNS trigger
LANGUAGE plpgsql
SET search_path = ''
AS $$
BEGIN
  IF NEW.kb IS NULL THEN
    NEW.kb := NEW.agent_id;
  END IF;
  RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS knowledge_chunks_default_kb ON knowledge_chunks;
CREATE TRIGGER knowledge_chunks_default_kb
  BEFORE INSERT ON knowledge_chunks
  FOR EACH ROW EXECUTE FUNCTION knowledge_chunks_default_kb();

COMMIT;
