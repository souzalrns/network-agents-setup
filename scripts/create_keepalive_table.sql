-- Tabela lida pelo workflow de keep-alive (J1 / AU-47).
--
-- O workflow (.github/workflows/keep-alive.yml) faz, com a chave anon:
--   GET $SUPABASE_URL/rest/v1/keepalive?select=id&limit=1
-- e só passa com HTTP 200. Por isso precisa de: tabela `public.keepalive`
-- com coluna `id`, e o role `anon` com SELECT nela.
--
-- Segurança: RLS activa; o anon só pode LER (nada sensível aqui). Tabelas
-- novas em `public` dão ALL ao anon por omissão (pg_default_acl, verificado
-- em 2026-09-30), por isso o REVOKE é necessário.
--
-- Projecto: agent-network-memory (mpsuurqilnhsvbnjmrpm). Correr uma vez no
-- SQL Editor do Supabase. Idempotente.

CREATE TABLE IF NOT EXISTS public.keepalive (
  id         smallint PRIMARY KEY DEFAULT 1,
  last_ping  timestamptz NOT NULL DEFAULT now(),
  created_at timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT keepalive_single_row CHECK (id = 1)
);

INSERT INTO public.keepalive (id) VALUES (1) ON CONFLICT (id) DO NOTHING;

ALTER TABLE public.keepalive ENABLE ROW LEVEL SECURITY;

REVOKE ALL ON public.keepalive FROM anon, authenticated;
GRANT SELECT ON public.keepalive TO anon;

DROP POLICY IF EXISTS keepalive_anon_select ON public.keepalive;
CREATE POLICY keepalive_anon_select
  ON public.keepalive
  FOR SELECT
  TO anon
  USING (true);
