-- Vertical editorial: esquema inicial.
-- Nomes neutros (publication, story, newsroom): a marca é um registo em `publications`, nunca código.
-- Isolamento: todas as tabelas de conteúdo têm publication_id e RLS FORCE; a aplicação liga-se com um
-- papel sem privilégios (editorial_app) e cada transacção declara quem actua:
--   app.publication_id  uuid da publicação
--   app.user_id         uuid do utilizador (vazio para agente, sistema e público)
--   app.role            papel na publicação (admin|director|editor|journalist|contributor|reviewer)
--   app.actor_kind      human | agent | system | public
-- Sem estas variáveis nenhuma linha é visível (fail-closed).

create schema if not exists editorial;
set search_path = editorial, public;

create extension if not exists pgcrypto;
create extension if not exists citext;

-- ---------------------------------------------------------------- contexto da transacção
create or replace function editorial.ctx_publication() returns uuid language sql stable as
$$ select nullif(current_setting('app.publication_id', true), '')::uuid $$;
create or replace function editorial.ctx_user() returns uuid language sql stable as
$$ select nullif(current_setting('app.user_id', true), '')::uuid $$;
create or replace function editorial.ctx_role() returns text language sql stable as
$$ select coalesce(nullif(current_setting('app.role', true), ''), '') $$;
create or replace function editorial.ctx_kind() returns text language sql stable as
$$ select coalesce(nullif(current_setting('app.actor_kind', true), ''), '') $$;
create or replace function editorial.is_staff() returns boolean language sql stable as
$$ select editorial.ctx_kind() = 'human' and editorial.ctx_role() <> '' $$;
create or replace function editorial.is_lead() returns boolean language sql stable as
$$ select editorial.ctx_kind() = 'human' and editorial.ctx_role() in ('admin', 'director') $$;
create or replace function editorial.is_desk() returns boolean language sql stable as
$$ select editorial.ctx_kind() = 'human' and editorial.ctx_role() in ('admin', 'director', 'editor') $$;

-- ---------------------------------------------------------------- publicação (a marca é configuração)
create table publications (
  id                uuid primary key default gen_random_uuid(),
  slug              text not null unique check (slug ~ '^[a-z0-9]+(-[a-z0-9]+)*$'),
  name              text not null,
  tagline           text not null default '',
  description       text not null default '',
  logo_url          text,
  favicon_url       text,
  primary_color     text not null default '#16211C' check (primary_color ~ '^#[0-9A-Fa-f]{6}$'),
  secondary_color   text not null default '#F0B429' check (secondary_color ~ '^#[0-9A-Fa-f]{6}$'),
  domain            text,
  language          text not null default 'pt-PT',
  timezone          text not null default 'Europe/Lisbon',
  contact_email     text,
  contact_address   text,
  social_links      jsonb not null default '{}'::jsonb,
  legal             jsonb not null default '{}'::jsonb,   -- registo ERC, proprietário, director, NIPC
  agent_names       jsonb not null default '{}'::jsonb,   -- id técnico do agente -> nome de apresentação
  settings          jsonb not null default '{"require_second_reviewer": true}'::jsonb,
  public_launch     boolean not null default false,       -- false: site com noindex e aviso de pré-lançamento
  created_at        timestamptz not null default now(),
  updated_at        timestamptz not null default now()
);

create table users (
  id             uuid primary key default gen_random_uuid(),
  email          citext not null unique,
  name           text not null,
  password_hash  text not null,
  disabled_at    timestamptz,
  created_at     timestamptz not null default now()
);

create type member_role as enum ('admin', 'director', 'editor', 'journalist', 'contributor', 'reviewer');

create table memberships (
  publication_id uuid not null references publications on delete cascade,
  user_id        uuid not null references users on delete cascade,
  role           member_role not null,
  author_slug    text not null check (author_slug ~ '^[a-z0-9]+(-[a-z0-9]+)*$'),
  bio            text not null default '',
  avatar_url     text,
  public_profile boolean not null default true,
  created_at     timestamptz not null default now(),
  primary key (publication_id, user_id),
  unique (publication_id, author_slug)
);

create table sessions (
  token_hash     text primary key,
  user_id        uuid not null references users on delete cascade,
  publication_id uuid not null references publications on delete cascade,
  created_at     timestamptz not null default now(),
  expires_at     timestamptz not null
);
create index on sessions (user_id);

create table api_tokens (
  id             uuid primary key default gen_random_uuid(),
  publication_id uuid not null references publications on delete cascade,
  name           text not null,
  token_hash     text not null unique,
  scopes         text[] not null default '{}',
  created_by     uuid references users,
  created_at     timestamptz not null default now(),
  last_used_at   timestamptz,
  revoked_at     timestamptz
);

-- ---------------------------------------------------------------- editorias
create table sections (
  id             uuid primary key default gen_random_uuid(),
  publication_id uuid not null references publications on delete cascade,
  slug           text not null check (slug ~ '^[a-z0-9]+(-[a-z0-9]+)*$'),
  name           text not null,
  description    text not null default '',
  color          text not null default '#7A8480' check (color ~ '^#[0-9A-Fa-f]{6}$'),
  position       int not null default 0,
  active         boolean not null default true,
  unique (publication_id, slug),
  unique (publication_id, id)
);

-- ---------------------------------------------------------------- pautas e artigos (uma peça, 11 estados)
create type story_state as enum (
  'idea', 'pitch_proposed', 'pitch_approved', 'researching', 'interviewing',
  'writing', 'in_review', 'approved', 'scheduled', 'published', 'archived');

create table stories (
  id               uuid primary key default gen_random_uuid(),
  publication_id   uuid not null references publications on delete cascade,
  section_id       uuid,
  state            story_state not null default 'idea',
  priority         smallint not null default 2 check (priority between 1 and 3),  -- 1 = alta
  format           text not null default 'reportagem',
  origin           text not null default 'human' check (origin in ('human', 'agent', 'radar')),
  -- pauta
  title            text not null check (length(btrim(title)) > 0),
  angle            text not null default '',
  to_confirm       text not null default '',
  interview_questions text[] not null default '{}',
  due_date         date,
  assignee_id      uuid references users,
  created_by       uuid references users,
  -- artigo
  slug             text check (slug is null or slug ~ '^[a-z0-9]+(-[a-z0-9]+)*$'),
  subtitle         text not null default '',
  summary          text not null default '',
  body             text not null default '',
  author_id        uuid references users,
  hero_image_url   text,
  hero_caption     text not null default '',
  hero_credit      text not null default '',
  tags             text[] not null default '{}',
  seo_title        text not null default '',
  meta_description text not null default '',
  kind             text not null default 'news' check (kind in ('news', 'opinion', 'interview', 'sponsored')),
  -- publicação
  scheduled_at     timestamptz,
  scheduled_by     uuid references users,
  approved_by      uuid references users,
  approved_at      timestamptz,
  published_at     timestamptz,
  version          int not null default 1,
  created_at       timestamptz not null default now(),
  updated_at       timestamptz not null default now(),
  search           tsvector generated always as (
    setweight(to_tsvector('portuguese', coalesce(title, '')), 'A') ||
    setweight(to_tsvector('portuguese', coalesce(subtitle, '') || ' ' || coalesce(summary, '')), 'B') ||
    setweight(to_tsvector('portuguese', coalesce(body, '')), 'C')) stored,
  foreign key (publication_id, section_id) references sections (publication_id, id),
  unique (publication_id, id)
);
create unique index stories_slug_uq on stories (publication_id, slug) where slug is not null;
create index stories_state_idx on stories (publication_id, state, updated_at desc);
create index stories_published_idx on stories (publication_id, published_at desc) where state = 'published';
create index stories_search_idx on stories using gin (search);

create table story_events (
  id             bigint generated always as identity primary key,
  publication_id uuid not null references publications on delete cascade,
  story_id       uuid not null,
  type           text not null,          -- state_change | edit | assignment | comment | agent_output | correction
  from_state     story_state,
  to_state       story_state,
  actor_kind     text not null,
  actor_user_id  uuid references users,
  actor_label    text not null default '',
  note           text not null default '',
  payload        jsonb not null default '{}'::jsonb,
  at             timestamptz not null default now(),
  foreign key (publication_id, story_id) references stories (publication_id, id) on delete cascade
);
create index on story_events (publication_id, story_id, at);
create index on story_events (publication_id, at desc);

create table story_versions (
  id             bigint generated always as identity primary key,
  publication_id uuid not null references publications on delete cascade,
  story_id       uuid not null,
  version        int not null,
  title          text not null,
  subtitle       text not null,
  summary        text not null,
  body           text not null,
  saved_by       uuid references users,
  saved_kind     text not null,
  note           text not null default '',
  saved_at       timestamptz not null default now(),
  unique (story_id, version),
  foreign key (publication_id, story_id) references stories (publication_id, id) on delete cascade
);

create table comments (
  id             uuid primary key default gen_random_uuid(),
  publication_id uuid not null references publications on delete cascade,
  story_id       uuid not null,
  author_id      uuid references users,
  author_kind    text not null default 'human',
  author_label   text not null default '',
  body           text not null check (length(btrim(body)) > 0),
  kind           text not null default 'comment' check (kind in ('comment', 'review', 'agent_note')),
  resolved_at    timestamptz,
  created_at     timestamptz not null default now(),
  foreign key (publication_id, story_id) references stories (publication_id, id) on delete cascade
);
create index on comments (publication_id, story_id, created_at);

-- ---------------------------------------------------------------- fontes jornalísticas (confidenciais)
create table sources (
  id              uuid primary key default gen_random_uuid(),
  publication_id  uuid not null references publications on delete cascade,
  name            text not null,
  organization    text not null default '',
  kind            text not null default 'person' check (kind in ('person', 'institution', 'document')),
  contact         text not null default '',
  notes           text not null default '',
  confidentiality text not null default 'internal' check (confidentiality in ('public', 'internal', 'protected')),
  owner_id        uuid not null references users,
  created_at      timestamptz not null default now(),
  unique (publication_id, id)
);

create table story_sources (
  publication_id uuid not null references publications on delete cascade,
  story_id       uuid not null,
  source_id      uuid not null,
  usage          text not null default 'on_record' check (usage in ('on_record', 'background', 'off_record')),
  note           text not null default '',
  primary key (story_id, source_id),
  foreign key (publication_id, story_id) references stories (publication_id, id) on delete cascade,
  foreign key (publication_id, source_id) references sources (publication_id, id) on delete cascade
);

-- referências públicas e anexos (documentos, fotografias, vídeo, áudio) por ligação
create table story_refs (
  id             uuid primary key default gen_random_uuid(),
  publication_id uuid not null references publications on delete cascade,
  story_id       uuid not null,
  kind           text not null default 'document' check (kind in ('document', 'data', 'article', 'photo', 'video', 'audio')),
  url            text not null check (url ~ '^https?://'),
  title          text not null default '',
  credit         text not null default '',
  note           text not null default '',
  added_by       uuid references users,
  added_kind     text not null default 'human',
  created_at     timestamptz not null default now(),
  foreign key (publication_id, story_id) references stories (publication_id, id) on delete cascade
);

-- ---------------------------------------------------------------- afirmações e verificação
-- Os quatro tipos estão no contrato de dados, não só nas instruções dos agentes:
--   fact        facto documentado: só fica `verified` com evidência e um verificador humano
--   statement   declaração: obriga a dizer quem declarou
--   inference   inferência: apresenta-se como hipótese
--   unconfirmed informação não confirmada: não pode ir no artigo
create table claims (
  id             uuid primary key default gen_random_uuid(),
  publication_id uuid not null references publications on delete cascade,
  story_id       uuid not null,
  text           text not null check (length(btrim(text)) > 0),
  kind           text not null check (kind in ('fact', 'statement', 'inference', 'unconfirmed')),
  attributed_to  text not null default '',
  evidence       jsonb not null default '[]'::jsonb,   -- [{url, title, quote, accessed_at}]
  verification   text not null default 'pending' check (verification in ('pending', 'verified', 'disputed', 'unsupported')),
  in_article     boolean not null default true,
  origin         text not null default 'human' check (origin in ('human', 'agent')),
  verified_by    uuid references users,
  verified_at    timestamptz,
  created_at     timestamptz not null default now(),
  foreign key (publication_id, story_id) references stories (publication_id, id) on delete cascade,
  check (kind <> 'statement' or length(btrim(attributed_to)) > 0),
  check (verification <> 'verified' or (verified_by is not null and verified_at is not null
                                        and jsonb_typeof(evidence) = 'array' and jsonb_array_length(evidence) > 0))
);
create index on claims (publication_id, story_id);

-- ---------------------------------------------------------------- trabalho dos agentes (propostas, nunca decisões)
create table agent_outputs (
  id             uuid primary key default gen_random_uuid(),
  publication_id uuid not null references publications on delete cascade,
  story_id       uuid,
  agent_id       text not null,          -- id técnico neutro, ex.: editorial.research
  kind           text not null check (kind in ('story_suggestions', 'research_dossier', 'factcheck_report', 'edit_review', 'distribution_pack')),
  run_id         text not null default '',
  payload        jsonb not null,
  cost           jsonb not null default '{}'::jsonb,
  status         text not null default 'proposed' check (status in ('proposed', 'accepted', 'dismissed')),
  reviewed_by    uuid references users,
  reviewed_at    timestamptz,
  created_at     timestamptz not null default now(),
  foreign key (publication_id, story_id) references stories (publication_id, id) on delete cascade
);
create index on agent_outputs (publication_id, status, created_at desc);

-- ---------------------------------------------------------------- radar (fontes públicas, só metadados)
create table feed_sources (
  id                 uuid primary key default gen_random_uuid(),
  publication_id     uuid not null references publications on delete cascade,
  name               text not null,
  feed_url           text not null check (feed_url ~ '^https://'),
  site_url           text,
  tier               text not null default 'media' check (tier in ('primary', 'institutional', 'media')),
  category           text not null default '',
  scope              text not null default 'local' check (scope in ('local', 'national', 'international')),
  interval_minutes   int not null default 60 check (interval_minutes between 15 and 10080),
  active             boolean not null default true,
  last_fetched_at    timestamptz,
  last_status        text not null default 'never' check (last_status in ('never', 'ok', 'not_modified', 'error', 'blocked')),
  last_error         text not null default '',
  etag               text,
  last_modified      text,
  created_at         timestamptz not null default now(),
  unique (publication_id, feed_url),
  unique (publication_id, id)
);

create table feed_items (
  id             uuid primary key default gen_random_uuid(),
  publication_id uuid not null references publications on delete cascade,
  feed_source_id uuid not null,
  url            text not null,
  url_key        text not null,           -- URL normalizado (sem parâmetros de seguimento)
  title          text not null,
  title_key      text not null,           -- título normalizado para apanhar a mesma notícia noutros meios
  excerpt        text not null default '' check (length(excerpt) <= 320),  -- nunca o artigo inteiro
  published_at   timestamptz,
  fetched_at     timestamptz not null default now(),
  duplicate_of   uuid references feed_items on delete set null,
  relevance      smallint not null default 0,
  topics         text[] not null default '{}',
  status         text not null default 'new' check (status in ('new', 'dismissed', 'linked')),
  story_id       uuid,
  unique (publication_id, url_key),
  foreign key (publication_id, feed_source_id) references feed_sources (publication_id, id) on delete cascade,
  foreign key (publication_id, story_id) references stories (publication_id, id) on delete set null
);
create index on feed_items (publication_id, status, relevance desc, fetched_at desc);
create index on feed_items (publication_id, title_key);

-- ---------------------------------------------------------------- distribuição (sempre com aprovação humana)
create table distribution_items (
  id             uuid primary key default gen_random_uuid(),
  publication_id uuid not null references publications on delete cascade,
  story_id       uuid not null,
  channel        text not null check (channel in ('instagram', 'youtube', 'podcast', 'newsletter', 'other')),
  kind           text not null default 'post',
  content        jsonb not null default '{}'::jsonb,
  state          text not null default 'draft' check (state in ('draft', 'in_review', 'approved', 'handed_off', 'published', 'discarded')),
  prepared_kind  text not null default 'human',
  prepared_label text not null default '',
  approved_by    uuid references users,
  approved_at    timestamptz,
  external_ref   text not null default '',
  created_at     timestamptz not null default now(),
  updated_at     timestamptz not null default now(),
  foreign key (publication_id, story_id) references stories (publication_id, id) on delete cascade,
  check (state not in ('approved', 'handed_off', 'published') or (approved_by is not null and approved_at is not null))
);

-- ---------------------------------------------------------------- páginas institucionais e correcções
create table pages (
  id             uuid primary key default gen_random_uuid(),
  publication_id uuid not null references publications on delete cascade,
  slug           text not null check (slug ~ '^[a-z0-9]+(-[a-z0-9]+)*$'),
  title          text not null,
  body           text not null default '',
  published      boolean not null default false,
  updated_by     uuid references users,
  updated_at     timestamptz not null default now(),
  unique (publication_id, slug)
);

create table corrections (
  id             uuid primary key default gen_random_uuid(),
  publication_id uuid not null references publications on delete cascade,
  story_id       uuid not null,
  text           text not null check (length(btrim(text)) > 0),
  created_by     uuid references users,
  created_at     timestamptz not null default now(),
  foreign key (publication_id, story_id) references stories (publication_id, id) on delete cascade
);

-- ---------------------------------------------------------------- auditoria geral
create table audit_log (
  id             bigint generated always as identity primary key,
  publication_id uuid references publications on delete cascade,
  actor_kind     text not null,
  actor_user_id  uuid,
  actor_label    text not null default '',
  action         text not null,
  entity         text not null default '',
  entity_id      text not null default '',
  payload        jsonb not null default '{}'::jsonb,
  at             timestamptz not null default now()
);
create index on audit_log (publication_id, at desc);
