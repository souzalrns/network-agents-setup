-- J3 — RAG canónico: migrar knowledge_chunks_t6 -> knowledge_chunks.
--
-- Decisão fechada: tabela canónica = knowledge_chunks (a que o retrieve lê:
-- match_knowledge em agent-network-mcp/lib/knowledge.js:54). A t6 é abandonada.
-- Este ficheiro NÃO apaga a t6 (ver scripts/drop_knowledge_chunks_t6.sql, passo
-- posterior e separado). Correr no SQL Editor do projecto mpsuurqilnhsvbnjmrpm.
-- Idempotente: pode correr-se mais de uma vez. Tudo numa transacção.
--
-- Estado verificado ao vivo em 2026-09-30 (SELECT read-only):
--   knowledge_chunks 210 linhas; knowledge_chunks_t6 110 linhas (33 fontes);
--   9 linhas da t6 (docs/knowledge/ai-findability.md) já copiadas antes para a
--   knowledge_chunks com project='network-agents-setup' (mesmo embedding).
--   11 linhas da t6 têm agent_id composto 'marketing+produto-tech-transversal'.
-- Resultado esperado: +112 linhas (99 simples + 22 do composto desdobrado - 9 já
-- existentes); 121 linhas com project='network-agents-setup'; 322 no total.

BEGIN;

-- 1) Desfazer a ambiguidade do match_knowledge.
-- Existem 2 overloads; a chamada do MCP (3 argumentos com nome) falha com
-- "42725 function match_knowledge(...) is not unique" (reproduzido em
-- 2026-09-30). A versão de 4 argumentos não está versionada em nenhum repo e
-- ninguém lhe passa match_project. Fica a de 3 argumentos, que é a versionada
-- (agent-network-mcp/memory/schema.sql:45-58) e inclui agent_id='global'.
-- Para repor a removida (definição exacta lida em 2026-09-30):
--   CREATE OR REPLACE FUNCTION public.match_knowledge(query_embedding vector,
--     match_agent_id text, match_count integer DEFAULT 4,
--     match_project text DEFAULT NULL::text)
--   RETURNS TABLE(id uuid, content text, source text, similarity double precision)
--   LANGUAGE sql STABLE SET search_path TO 'public' AS $f$
--     SELECT id, content, source, 1 - (embedding <=> query_embedding) AS similarity
--     FROM public.knowledge_chunks
--     WHERE agent_id = match_agent_id AND (match_project IS NULL OR project = match_project)
--     ORDER BY embedding <=> query_embedding LIMIT match_count; $f$;
DROP FUNCTION IF EXISTS public.match_knowledge(vector, text, integer, text);

-- 2) Copiar a t6. O agent_id composto 'a+b' desdobra-se numa linha por agente:
-- o retrieve filtra por igualdade (agent_id = match_agent_id), por isso
-- 'marketing+produto-tech-transversal' nunca seria encontrado por nenhum dos dois.
INSERT INTO public.knowledge_chunks (
  agent_id, source, content, embedding,
  project, content_hash, chunk_index, kb, created_at, updated_at
)
SELECT a.agent_id, t.source_path, t.content, t.embedding,
       'network-agents-setup', t.content_hash, t.chunk_index, t.kb,
       t.created_at, t.updated_at
FROM public.knowledge_chunks_t6 t
CROSS JOIN LATERAL unnest(string_to_array(t.agent_id, '+')) AS a(agent_id)
WHERE NOT EXISTS (
  SELECT 1 FROM public.knowledge_chunks k
  WHERE k.project = 'network-agents-setup'
    AND k.agent_id = a.agent_id
    AND k.source = t.source_path
    AND k.chunk_index = t.chunk_index
);

-- 3) Verificação: cada linha da t6 (por agente) tem de ter par na knowledge_chunks.
DO $$
DECLARE missing int;
BEGIN
  SELECT count(*) INTO missing
  FROM public.knowledge_chunks_t6 t
  CROSS JOIN LATERAL unnest(string_to_array(t.agent_id, '+')) AS a(agent_id)
  WHERE NOT EXISTS (
    SELECT 1 FROM public.knowledge_chunks k
    WHERE k.project = 'network-agents-setup' AND k.agent_id = a.agent_id
      AND k.source = t.source_path AND k.chunk_index = t.chunk_index
  );
  IF missing > 0 THEN
    RAISE EXCEPTION 'migracao incompleta: % linhas da t6 sem par', missing;
  END IF;
END $$;

COMMIT;

-- Conferir depois (esperado: 121 e 322):
--   SELECT count(*) FROM knowledge_chunks WHERE project = 'network-agents-setup';
--   SELECT count(*) FROM knowledge_chunks;
