-- Vertical editorial: o que faltava para a redacção funcionar sozinha, sem serviços externos nem custos.
-- 1. Recuperar a palavra-passe sem email: a direcção gera um link de uso único (24 h) e entrega-o à pessoa.
-- 2. Biblioteca de média: imagens carregadas para a própria base (comprimidas no browser, máx. 3 MB cada).
-- 3. Newsletter: inscrições com consentimento registado (RGPD) e anulação por link; o envio fica para quando
--    houver um serviço de email (a lista exporta-se com os links de anulação).
set search_path = editorial, public;

-- ================================================================ 1. links de recuperação
create table if not exists password_resets (
  token_hash     text primary key,                    -- sha256 do token; o token só existe no link
  user_id        uuid not null references users on delete cascade,
  publication_id uuid not null references publications on delete cascade,
  created_by     uuid references users,
  created_at     timestamptz not null default now(),
  expires_at     timestamptz not null,
  used_at        timestamptz
);
alter table password_resets enable row level security;
alter table password_resets force row level security;
-- a aplicação não lê nem escreve esta tabela: só pelas duas funções abaixo

create or replace function editorial.staff_reset_link(p_user uuid, p_token_hash text)
returns timestamptz language plpgsql security definer set search_path = editorial, pg_temp as $$
declare target_role text; expires timestamptz := now() + interval '24 hours';
begin
  if ctx_kind() <> 'human' or ctx_role() not in ('admin', 'director') or ctx_publication() is null then
    raise exception 'só a direcção gera links de recuperação';
  end if;
  select role::text into target_role from memberships where user_id = p_user and publication_id = ctx_publication();
  if target_role is null then raise exception 'essa pessoa não pertence a esta publicação'; end if;
  if target_role = 'admin' and ctx_role() <> 'admin' then raise exception 'só um administrador recupera a conta de um administrador'; end if;
  if p_user = ctx_user() then raise exception 'para mudares a tua palavra-passe usa a página Conta'; end if;
  -- um link de cada vez: os anteriores desta pessoa deixam de valer
  update password_resets set used_at = now() where user_id = p_user and used_at is null;
  insert into password_resets (token_hash, user_id, publication_id, created_by, expires_at)
    values (p_token_hash, p_user, ctx_publication(), ctx_user(), expires);
  insert into audit_log (publication_id, actor_kind, actor_user_id, action, entity, entity_id)
    values (ctx_publication(), 'human', ctx_user(), 'member.reset_link', 'user', p_user::text);
  return expires;
end $$;

-- sem contexto (quem usa o link não tem sessão): valida o token e troca a palavra-passe, uma só vez
create or replace function editorial.auth_reset_password(p_token_hash text, p_password_hash text)
returns boolean language plpgsql security definer set search_path = editorial, pg_temp as $$
declare r record;
begin
  select * into r from password_resets where token_hash = p_token_hash for update;
  if r is null or r.used_at is not null or r.expires_at < now() then return false; end if;
  update users set password_hash = p_password_hash where id = r.user_id;
  update password_resets set used_at = now() where token_hash = p_token_hash;
  delete from sessions where user_id = r.user_id;
  insert into audit_log (publication_id, actor_kind, actor_user_id, action, entity, entity_id)
    values (r.publication_id, 'human', r.user_id, 'member.password_reset', 'user', r.user_id::text);
  return true;
end $$;

-- ================================================================ 2. biblioteca de média
create table if not exists media (
  id             uuid primary key default gen_random_uuid(),
  publication_id uuid not null references publications on delete cascade,
  filename       text not null default '',
  content_type   text not null check (content_type in ('image/jpeg', 'image/png', 'image/webp')),
  bytes          bytea not null,
  size           int not null check (size > 0 and size <= 3000000),
  width          int,
  height         int,
  alt            text not null default '',
  credit         text not null default '',
  uploaded_by    uuid references users,
  created_at     timestamptz not null default now()
);
create index if not exists media_pub_created on media (publication_id, created_at desc);
alter table media enable row level security;
alter table media force row level security;
grant select, insert, update, delete on media to editorial_app;
-- o público vê as imagens (os artigos usam-nas); o identificador é um uuid, não se adivinha
create policy media_read on media for select to editorial_app using (mine(publication_id) and ctx_kind() in ('human', 'public', 'agent', 'system'));
create policy media_insert on media for insert to editorial_app with check (mine(publication_id) and can_write() and uploaded_by = ctx_user());
create policy media_update on media for update to editorial_app
  using (mine(publication_id) and can_write() and (uploaded_by = ctx_user() or is_desk()))
  with check (mine(publication_id));
create policy media_delete on media for delete to editorial_app using (mine(publication_id) and (uploaded_by = ctx_user() or is_desk()));

create or replace function editorial.media_guard() returns trigger language plpgsql as $$
begin
  if tg_op = 'UPDATE' and (new.bytes is distinct from old.bytes or new.publication_id <> old.publication_id
      or new.uploaded_by is distinct from old.uploaded_by or new.content_type <> old.content_type) then
    raise exception 'uma imagem carregada não se substitui: carrega outra';
  end if;
  if tg_op = 'INSERT' then new.size := octet_length(new.bytes); end if;
  return new;
end $$;
drop trigger if exists media_guard on media;
create trigger media_guard before insert or update on media for each row execute function media_guard();

-- ================================================================ 3. newsletter
create table if not exists subscribers (
  id                uuid primary key default gen_random_uuid(),
  publication_id    uuid not null references publications on delete cascade,
  email             citext not null,
  status            text not null default 'active' check (status in ('active', 'unsubscribed')),
  consent_text      text not null,                    -- o texto exacto que a pessoa aceitou
  consent_at        timestamptz not null default now(),
  unsubscribe_token text not null default encode(gen_random_bytes(18), 'hex'),
  unsubscribed_at   timestamptz,
  created_at        timestamptz not null default now(),
  unique (publication_id, email)
);
alter table subscribers enable row level security;
alter table subscribers force row level security;
grant select on subscribers to editorial_app;
-- só a direcção vê a lista; o público inscreve-se e anula pelas funções abaixo
create policy sub_read on subscribers for select to editorial_app using (mine(publication_id) and is_lead());

create or replace function editorial.public_subscribe(p_publication uuid, p_email text, p_consent text)
returns void language plpgsql security definer set search_path = editorial, public, pg_temp as $$
begin
  if p_email !~* '^[^@\s]+@[^@\s]+\.[^@\s]+$' or length(p_email) > 254 then raise exception 'email inválido'; end if;
  if length(btrim(p_consent)) = 0 then raise exception 'falta o consentimento'; end if;
  if not exists (select 1 from publications where id = p_publication) then raise exception 'publicação desconhecida'; end if;
  insert into subscribers (publication_id, email, consent_text)
    values (p_publication, lower(btrim(p_email)), p_consent)
    on conflict (publication_id, email) do update
      set status = 'active', consent_text = excluded.consent_text, consent_at = now(), unsubscribed_at = null;
end $$;

create or replace function editorial.public_unsubscribe(p_token text)
returns boolean language plpgsql security definer set search_path = editorial, public, pg_temp as $$
begin
  update subscribers set status = 'unsubscribed', unsubscribed_at = now()
    where unsubscribe_token = p_token and status = 'active';
  return found or exists (select 1 from subscribers where unsubscribe_token = p_token);
end $$;

-- o dono vê tudo (funções SECURITY DEFINER num Postgres gerido; ver 0005)
do $$
declare t text;
begin
  foreach t in array array['password_resets', 'media', 'subscribers'] loop
    execute format('drop policy if exists owner_all on editorial.%I', t);
    execute format('create policy owner_all on editorial.%I for all to %I using (true) with check (true)', t, current_user);
  end loop;
end $$;

revoke all on function editorial.staff_reset_link(uuid, text), editorial.auth_reset_password(text, text),
  editorial.public_subscribe(uuid, text, text), editorial.public_unsubscribe(text) from public;
grant execute on all functions in schema editorial to editorial_app;
