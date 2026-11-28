-- leads: empresas extraídas do Google Maps pelo workflow leads.yml (ferramenta opcional LEADS).
-- Aplicar no SQL Editor do SEU projeto Supabase. Genérico: serve qualquer negócio.
--
-- RGPD / LGPD / lei do spam:
--   * Só dados de EMPRESAS (nome, morada, telefone, site, email genérico tipo info@).
--   * Emails de pessoas singulares: não usar para envio sem base legal.
--   * Toda a comunicação precisa de opção de recusa; quem recusar fica com status = 'recusou'
--     e a linha mantém-se de propósito, para nunca voltar a ser contactado.
--   * Retenção: 12 meses (expires_at). Quem estiver em 'cliente' ou 'recusou' não expira.
--
-- RLS ativo e sem políticas: só o service_role acede (a chave pública não lê nem escreve).

create table if not exists public.leads (
  id            uuid primary key default gen_random_uuid(),
  place_key     text not null unique,            -- place_id do Google (ou nome+morada): evita duplicados
  query         text not null,                   -- ex.: "restaurantes Porto"
  nicho         text,                            -- etiqueta livre do utilizador
  nome          text not null,
  categoria     text,
  morada        text,
  telefone      text,
  website       text,
  email         text,
  emails        text[] default '{}',
  rating        numeric,
  reviews       integer,
  latitude      double precision,
  longitude     double precision,
  maps_url      text,
  status        text not null default 'novo'
                check (status in ('novo','contactado','respondeu','cliente','recusou','descartado')),
  notas         text,
  created_at    timestamptz not null default now(),
  expires_at    timestamptz not null default (now() + interval '12 months')
);

create index if not exists idx_leads_status on public.leads (status);
create index if not exists idx_leads_nicho on public.leads (nicho);
create index if not exists idx_leads_expires_at on public.leads (expires_at);

alter table public.leads enable row level security;  -- sem políticas: só o service_role

-- Limpeza: apaga leads vencidos que não são clientes nem recusas. Chamar à mão ou com pg_cron.
create or replace function public.cleanup_expired_leads()
returns integer
language plpgsql
security definer
set search_path = public
as $$
declare n integer;
begin
  delete from public.leads
   where expires_at < now() and status not in ('cliente','recusou');
  get diagnostics n = row_count;
  return n;
end;
$$;
revoke all on function public.cleanup_expired_leads() from public, anon, authenticated;
