-- L4 -- memoria semantica persistente (D3, VIA A: L4 propria sobre o Supabase).
--
-- Contrato: docs/architecture/memory/contracts.md (remember/recall/forget),
--           docs/architecture/memory/scopes.md (ambitos), layers.md:40-45 (L4).
-- Codigo:   runner/plan_runner/memory_l4.py. Operacao: docs/ops/MEMORY-L4.md.
--
-- Regras impostas AQUI (na BD, nao so no codigo):
--   * ambito obrigatorio: scope_kind em global|org|project|user|agent e scope_id
--     nao vazio (o `run` e L2 -- events.jsonl -- e nao entra na L4);
--   * status: candidate (omissao) | active | archived (forget) | superseded
--     (invalidado por um facto novo);
--   * NAO EDITAR EM SILENCIO: o trigger recusa mudar statement/subject/ambito.
--     Corrigir um facto = escrever um facto novo com `supersedes` (layers.md:44);
--   * NAO APAGAR: o trigger recusa DELETE. `forget` = tombstone (status archived).
--     Apagamento real por compliance so numa sessao de admin com
--     `SET LOCAL memory_l4.allow_delete = 'on'` (fica explicito e auditavel).
--
-- Seguranca (como token_usage/keepalive): RLS ligado e sem politicas, REVOKE ao
-- anon/authenticated (o default ACL do projecto da ALL ao anon em tabelas novas).
-- O runner escreve com o DATABASE_URL (role postgres, BYPASSRLS).
--
-- Projecto: agent-network-memory (mpsuurqilnhsvbnjmrpm). Correr no SQL Editor
-- ANTES de create_recall_l4_rpc.sql. Idempotente. Os blocos DO so mexem nos
-- papeis do Supabase se eles existirem (assim o mesmo ficheiro corre num
-- Postgres local de teste).

CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS public.memory_l4 (
  id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  scope_kind      text NOT NULL CHECK (scope_kind IN ('global', 'org', 'project', 'user', 'agent')),
  scope_id        text NOT NULL CHECK (length(btrim(scope_id)) > 0),
  subject         text,
  statement       text NOT NULL CHECK (length(btrim(statement)) > 0 AND char_length(statement) <= 2000),
  status          text NOT NULL DEFAULT 'candidate'
                  CHECK (status IN ('candidate', 'active', 'archived', 'superseded')),
  confidence      real CHECK (confidence IS NULL OR (confidence >= 0 AND confidence <= 1)),
  source_run_id   text,
  tags            text[] NOT NULL DEFAULT '{}',
  metadata        jsonb NOT NULL DEFAULT '{}'::jsonb,
  embedding       vector(768),
  supersedes      uuid REFERENCES public.memory_l4(id),
  superseded_by   uuid REFERENCES public.memory_l4(id),
  created_by      text NOT NULL DEFAULT 'agent',     -- 'agent:<id>' | 'human:<id>' | 'agent'
  created_at      timestamptz NOT NULL DEFAULT now(),
  updated_at      timestamptz NOT NULL DEFAULT now(),
  expires_at      timestamptz,                        -- ttl? de layers.md:43 (null = sem prazo)
  promoted_at     timestamptz,
  promoted_by     text,
  archived_at     timestamptz,
  archived_by     text,
  archived_reason text
);

CREATE INDEX IF NOT EXISTS idx_memory_l4_scope_status ON public.memory_l4 (scope_kind, scope_id, status);
CREATE INDEX IF NOT EXISTS idx_memory_l4_tags ON public.memory_l4 USING gin (tags);
CREATE INDEX IF NOT EXISTS idx_memory_l4_created ON public.memory_l4 (created_at DESC);
CREATE INDEX IF NOT EXISTS idx_memory_l4_embedding ON public.memory_l4 USING hnsw (embedding vector_cosine_ops);

-- Nao editar em silencio + updated_at
CREATE OR REPLACE FUNCTION public.memory_l4_guard_update() RETURNS trigger
LANGUAGE plpgsql AS $$
BEGIN
  IF NEW.statement IS DISTINCT FROM OLD.statement
     OR NEW.subject IS DISTINCT FROM OLD.subject
     OR NEW.scope_kind IS DISTINCT FROM OLD.scope_kind
     OR NEW.scope_id IS DISTINCT FROM OLD.scope_id
     OR NEW.created_at IS DISTINCT FROM OLD.created_at
     OR NEW.created_by IS DISTINCT FROM OLD.created_by THEN
    RAISE EXCEPTION 'memory_l4: statement/subject/ambito sao imutaveis (escreve um facto novo com supersedes)'
      USING ERRCODE = 'check_violation';
  END IF;
  NEW.updated_at := now();
  RETURN NEW;
END $$;

DROP TRIGGER IF EXISTS memory_l4_guard_update ON public.memory_l4;
CREATE TRIGGER memory_l4_guard_update BEFORE UPDATE ON public.memory_l4
  FOR EACH ROW EXECUTE FUNCTION public.memory_l4_guard_update();

-- Nao apagar (forget = tombstone)
CREATE OR REPLACE FUNCTION public.memory_l4_guard_delete() RETURNS trigger
LANGUAGE plpgsql AS $$
BEGIN
  IF coalesce(current_setting('memory_l4.allow_delete', true), '') <> 'on' THEN
    RAISE EXCEPTION 'memory_l4: DELETE proibido -- usa forget (status archived). Compliance: SET LOCAL memory_l4.allow_delete = ''on'''
      USING ERRCODE = 'insufficient_privilege';
  END IF;
  RETURN OLD;
END $$;

DROP TRIGGER IF EXISTS memory_l4_guard_delete ON public.memory_l4;
CREATE TRIGGER memory_l4_guard_delete BEFORE DELETE ON public.memory_l4
  FOR EACH ROW EXECUTE FUNCTION public.memory_l4_guard_delete();

ALTER TABLE public.memory_l4 ENABLE ROW LEVEL SECURITY;

DO $$
BEGIN
  IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'anon') THEN
    EXECUTE 'REVOKE ALL ON TABLE public.memory_l4 FROM anon';
  END IF;
  IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'authenticated') THEN
    EXECUTE 'REVOKE ALL ON TABLE public.memory_l4 FROM authenticated';
  END IF;
END $$;
