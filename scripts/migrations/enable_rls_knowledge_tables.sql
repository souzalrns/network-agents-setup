-- Alinhar knowledge_chunks_t6 e knowledge_sources com o padrão já
-- aplicado a knowledge_chunks e knowledge_log (RLS activa + policy
-- explícita de negação ao anon).
--
-- Contexto (ver AUDIT-SECURITY-2026.md secção 6 e EXECUTION-PROMPTS.md A2):
-- - O writer (supabase_writer.py) usa role "postgres" com BYPASSRLS —
--   não é afectado por RLS.
-- - Nenhum código lê estas tabelas via anon; o bloqueio do anon fecha
--   a exposição via PostgREST (que expõe todas as tabelas por omissão).
-- - Não há isolamento por agente (modelo de identidade inexistente).

ALTER TABLE knowledge_chunks_t6 ENABLE ROW LEVEL SECURITY;

CREATE POLICY knowledge_chunks_t6_anon_deny
  ON knowledge_chunks_t6
  FOR ALL
  TO anon
  USING (false);

ALTER TABLE knowledge_sources ENABLE ROW LEVEL SECURITY;

CREATE POLICY knowledge_sources_anon_deny
  ON knowledge_sources
  FOR ALL
  TO anon
  USING (false);
