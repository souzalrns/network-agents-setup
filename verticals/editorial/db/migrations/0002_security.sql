-- Vertical editorial: papel da aplicação, RLS por publicação e regras impostas pela base de dados.
-- O que um agente, o sistema ou o público podem fazer está aqui, não nas instruções de ninguém.
set search_path = editorial, public;

do $$ begin
  if not exists (select from pg_roles where rolname = 'editorial_app') then
    create role editorial_app nologin;
  end if;
end $$;

grant usage on schema editorial to editorial_app;

alter table memberships add column if not exists display_name text not null default '';

-- ================================================================ RLS: ligado e forçado em tudo
do $$ declare t text; begin
  foreach t in array array['publications','users','memberships','sessions','api_tokens','sections','stories',
    'story_events','story_versions','comments','sources','story_sources','story_refs','claims','agent_outputs',
    'feed_sources','feed_items','distribution_items','pages','corrections','audit_log'] loop
    execute format('alter table editorial.%I enable row level security', t);
    execute format('alter table editorial.%I force row level security', t);
  end loop;
end $$;

-- helper: a linha é da publicação da transacção
create or replace function editorial.mine(p uuid) returns boolean language sql stable as
$$ select p is not null and p = editorial.ctx_publication() $$;
create or replace function editorial.can_write() returns boolean language sql stable as
$$ select editorial.ctx_kind() = 'human' and editorial.ctx_role() in ('admin','director','editor','journalist','contributor') $$;

-- ---------------------------------------------------------------- publicação e equipa
grant select, update on publications to editorial_app;
create policy pub_read on publications for select to editorial_app using (mine(id));
create policy pub_write on publications for update to editorial_app using (mine(id) and is_lead()) with check (mine(id) and is_lead());

grant select (id, name, email, disabled_at, created_at) on users to editorial_app;
create policy users_read on users for select to editorial_app using (
  is_staff() and exists (select 1 from memberships m where m.user_id = users.id and m.publication_id = ctx_publication()));

grant select, insert, update, delete on memberships to editorial_app;
create policy mem_read on memberships for select to editorial_app using (
  mine(publication_id) and (ctx_kind() in ('human','agent','system') or (ctx_kind() = 'public' and public_profile)));
create policy mem_insert on memberships for insert to editorial_app with check (
  mine(publication_id) and is_lead() and (role <> 'admin' or ctx_role() = 'admin'));
create policy mem_update on memberships for update to editorial_app
  using (mine(publication_id) and (is_lead() or user_id = ctx_user()))
  with check (mine(publication_id) and (is_lead() or user_id = ctx_user()));
create policy mem_delete on memberships for delete to editorial_app using (
  mine(publication_id) and is_lead() and (role <> 'admin' or ctx_role() = 'admin') and user_id <> ctx_user());

-- só um administrador muda papéis; ninguém muda o próprio papel; um director não cria administradores
create or replace function editorial.memberships_guard() returns trigger language plpgsql as $$
begin
  if new.role is distinct from old.role then
    if ctx_kind() <> 'human' or not is_lead() then raise exception 'só a direcção altera permissões'; end if;
    if new.user_id = ctx_user() then raise exception 'ninguém altera o próprio papel'; end if;
    if (new.role = 'admin' or old.role = 'admin') and ctx_role() <> 'admin' then
      raise exception 'só um administrador concede ou retira o papel de administrador';
    end if;
  end if;
  if new.publication_id <> old.publication_id or new.user_id <> old.user_id then
    raise exception 'uma pertença não muda de publicação nem de pessoa';
  end if;
  return new;
end $$;
create trigger memberships_guard before update on memberships for each row execute function memberships_guard();

grant select, insert, update on api_tokens to editorial_app;
create policy tok_all on api_tokens for all to editorial_app
  using (mine(publication_id) and ctx_kind() = 'human' and ctx_role() = 'admin')
  with check (mine(publication_id) and ctx_kind() = 'human' and ctx_role() = 'admin');

-- ---------------------------------------------------------------- editorias
grant select, insert, update, delete on sections to editorial_app;
create policy sec_read on sections for select to editorial_app using (mine(publication_id) and ctx_kind() <> '');
create policy sec_write on sections for all to editorial_app using (mine(publication_id) and is_lead()) with check (mine(publication_id) and is_lead());

-- ---------------------------------------------------------------- peças
grant select, insert, update, delete on stories to editorial_app;
create policy st_read on stories for select to editorial_app using (
  mine(publication_id) and (ctx_kind() in ('human','agent','system') and (ctx_kind() <> 'human' or is_staff())
                            or (ctx_kind() = 'public' and state = 'published')));
create policy st_insert on stories for insert to editorial_app with check (
  mine(publication_id) and (
    (can_write() and state in ('idea','pitch_proposed') and origin = 'human' and created_by = ctx_user())
    or (ctx_kind() = 'agent' and state = 'idea' and origin = 'agent' and created_by is null
        and assignee_id is null and author_id is null)
    or (ctx_kind() = 'system' and state = 'idea' and origin = 'radar' and created_by is null)));
create policy st_update on stories for update to editorial_app
  using (mine(publication_id) and (
    is_desk()
    or (can_write() and ctx_user() in (assignee_id, author_id, created_by))
    or (can_write() and state = 'idea' and created_by is null and assignee_id is null)
    or (ctx_kind() = 'system' and state = 'scheduled')))
  with check (mine(publication_id));
create policy st_delete on stories for delete to editorial_app using (mine(publication_id) and is_lead() and state <> 'published');

create or replace function editorial.stories_guard() returns trigger language plpgsql as $$
declare
  k text := ctx_kind();
  second_reviewer boolean;
begin
  if k not in ('human', 'system') then raise exception 'só pessoas da redacção alteram uma peça'; end if;
  if new.publication_id <> old.publication_id then raise exception 'uma peça não muda de publicação'; end if;

  if k = 'system' then
    -- o sistema só executa o que uma pessoa agendou: scheduled -> published, à hora marcada, sem tocar no conteúdo
    if not (old.state = 'scheduled' and new.state = 'published' and old.scheduled_by is not null
            and old.scheduled_at is not null and old.scheduled_at <= now()
            and new.title = old.title and new.body = old.body and new.subtitle = old.subtitle
            and new.summary = old.summary and new.slug is not distinct from old.slug) then
      raise exception 'o sistema só publica uma peça agendada por uma pessoa, à hora marcada';
    end if;
  end if;

  if new.state is distinct from old.state then
    if new.state in ('pitch_approved', 'approved', 'scheduled', 'published', 'archived') and k = 'human' and not is_desk() then
      raise exception 'esta mudança de estado é da edição ou da direcção';
    end if;
    if new.state = 'approved' then
      if old.state = 'scheduled' then
        -- cancelar o agendamento: a aprovação mantém-se, a data sai
        new.scheduled_at := null; new.scheduled_by := null;
        new.updated_at := now();
        return new;
      end if;
      if old.state <> 'in_review' then raise exception 'só se aprova uma peça que está em revisão'; end if;
      select coalesce((settings->>'require_second_reviewer')::boolean, true) into second_reviewer
        from publications where id = new.publication_id;
      if second_reviewer and new.author_id is not null and new.author_id = ctx_user() then
        raise exception 'quem escreveu a peça não a aprova: pede a aprovação a outra pessoa da edição';
      end if;
      if exists (select 1 from claims c where c.story_id = new.id and c.in_article
                 and (c.kind = 'unconfirmed' or (c.kind = 'fact' and c.verification <> 'verified'))) then
        raise exception 'há afirmações por verificar no artigo: verifica-as ou retira-as antes de aprovar';
      end if;
      if length(btrim(new.body)) = 0 or new.section_id is null or new.author_id is null or new.slug is null then
        raise exception 'falta texto, editoria, autor ou endereço para aprovar a peça';
      end if;
      new.approved_by := ctx_user();
      new.approved_at := now();
    end if;
    if new.state = 'scheduled' then
      if old.state <> 'approved' then raise exception 'só se agenda uma peça aprovada'; end if;
      if new.scheduled_at is null or new.scheduled_at <= now() then raise exception 'a data de publicação tem de ser futura'; end if;
      new.scheduled_by := ctx_user();
    end if;
    if new.state = 'published' then
      if old.state not in ('approved', 'scheduled', 'archived') then raise exception 'só se publica uma peça aprovada'; end if;
      if old.approved_by is null then raise exception 'a peça nunca foi aprovada por uma pessoa'; end if;
      new.published_at := coalesce(old.published_at, now());
    end if;
    if old.state in ('approved', 'scheduled') and new.state in ('writing', 'in_review') then
      new.approved_by := null; new.approved_at := null; new.scheduled_at := null; new.scheduled_by := null;
    end if;
  end if;

  if k = 'human' and old.state in ('approved', 'scheduled', 'published') and not is_desk()
     and (new.title, new.subtitle, new.summary, new.body) is distinct from (old.title, old.subtitle, old.summary, old.body) then
    raise exception 'uma peça aprovada só é alterada pela edição';
  end if;
  -- alterar o texto de uma peça aprovada ou agendada retira a aprovação (o que foi aprovado era outro texto)
  if old.state in ('approved', 'scheduled') and new.state = old.state
     and (new.title, new.subtitle, new.summary, new.body) is distinct from (old.title, old.subtitle, old.summary, old.body) then
    new.state := 'in_review';
    new.approved_by := null; new.approved_at := null; new.scheduled_at := null; new.scheduled_by := null;
  end if;

  if (new.title, new.subtitle, new.summary, new.body) is distinct from (old.title, old.subtitle, old.summary, old.body) then
    new.version := old.version + 1;
  end if;
  new.updated_at := now();
  return new;
end $$;
create trigger stories_guard before update on stories for each row execute function stories_guard();

-- cada mudança de estado e cada versão ficam registadas pela base de dados
create or replace function editorial.stories_log() returns trigger language plpgsql as $$
declare label text := coalesce(nullif(current_setting('app.actor_label', true), ''), ctx_kind());
        note text := coalesce(nullif(current_setting('app.note', true), ''), '');
begin
  if tg_op = 'INSERT' then
    insert into story_events (publication_id, story_id, type, from_state, to_state, actor_kind, actor_user_id, actor_label, note)
      values (new.publication_id, new.id, 'state_change', null, new.state, ctx_kind(), ctx_user(), label, note);
    insert into story_versions (publication_id, story_id, version, title, subtitle, summary, body, saved_by, saved_kind)
      values (new.publication_id, new.id, new.version, new.title, new.subtitle, new.summary, new.body, ctx_user(), ctx_kind());
    return new;
  end if;
  if new.state is distinct from old.state then
    insert into story_events (publication_id, story_id, type, from_state, to_state, actor_kind, actor_user_id, actor_label, note)
      values (new.publication_id, new.id, 'state_change', old.state, new.state, ctx_kind(), ctx_user(), label, note);
  end if;
  if new.version <> old.version then
    insert into story_versions (publication_id, story_id, version, title, subtitle, summary, body, saved_by, saved_kind, note)
      values (new.publication_id, new.id, new.version, new.title, new.subtitle, new.summary, new.body, ctx_user(), ctx_kind(), note);
  end if;
  if new.assignee_id is distinct from old.assignee_id then
    insert into story_events (publication_id, story_id, type, actor_kind, actor_user_id, actor_label, payload)
      values (new.publication_id, new.id, 'assignment', ctx_kind(), ctx_user(), label,
              jsonb_build_object('from', old.assignee_id, 'to', new.assignee_id));
  end if;
  return new;
end $$;
create trigger stories_log after insert or update on stories for each row execute function stories_log();

-- histórico: só se acrescenta e lê
grant select, insert on story_events, story_versions, audit_log to editorial_app;
create policy ev_read on story_events for select to editorial_app using (mine(publication_id) and is_staff());
create policy ev_insert on story_events for insert to editorial_app with check (mine(publication_id) and ctx_kind() in ('human','agent','system'));
create policy ver_read on story_versions for select to editorial_app using (mine(publication_id) and is_staff());
create policy ver_insert on story_versions for insert to editorial_app with check (mine(publication_id) and ctx_kind() in ('human','agent','system'));
create policy aud_read on audit_log for select to editorial_app using (mine(publication_id) and is_lead());
create policy aud_insert on audit_log for insert to editorial_app with check (mine(publication_id) and ctx_kind() <> '');

-- ---------------------------------------------------------------- comentários
grant select, insert, update on comments to editorial_app;
create policy com_read on comments for select to editorial_app using (mine(publication_id) and is_staff());
create policy com_insert on comments for insert to editorial_app with check (
  mine(publication_id) and ((is_staff() and author_kind = 'human' and author_id = ctx_user() and kind in ('comment','review'))
                            or (ctx_kind() = 'agent' and author_kind = 'agent' and author_id is null and kind = 'agent_note')));
create policy com_update on comments for update to editorial_app using (mine(publication_id) and is_staff()) with check (mine(publication_id));

-- ---------------------------------------------------------------- fontes: nunca para agentes, sistema ou público
grant select, insert, update, delete on sources, story_sources to editorial_app;
create policy src_read on sources for select to editorial_app using (
  mine(publication_id) and is_staff() and (confidentiality <> 'protected' or owner_id = ctx_user() or is_lead()));
create policy src_insert on sources for insert to editorial_app with check (mine(publication_id) and can_write() and owner_id = ctx_user());
create policy src_update on sources for update to editorial_app
  using (mine(publication_id) and can_write() and (owner_id = ctx_user() or is_lead()))
  with check (mine(publication_id));
create policy src_delete on sources for delete to editorial_app using (mine(publication_id) and can_write() and (owner_id = ctx_user() or is_lead()));
create policy ss_read on story_sources for select to editorial_app using (
  mine(publication_id) and is_staff() and exists (select 1 from sources s where s.id = story_sources.source_id));
create policy ss_write on story_sources for all to editorial_app
  using (mine(publication_id) and can_write() and exists (select 1 from sources s where s.id = story_sources.source_id))
  with check (mine(publication_id) and can_write() and exists (select 1 from sources s where s.id = story_sources.source_id));

-- ---------------------------------------------------------------- referências, afirmações, propostas dos agentes
grant select, insert, update, delete on story_refs, claims to editorial_app;
create policy ref_read on story_refs for select to editorial_app using (
  mine(publication_id) and (is_staff() or ctx_kind() = 'agent'
    or (ctx_kind() = 'public' and kind in ('document','data','article')
        and exists (select 1 from stories s where s.id = story_refs.story_id and s.state = 'published'))));
create policy ref_insert on story_refs for insert to editorial_app with check (
  mine(publication_id) and ((can_write() and added_kind = 'human' and added_by = ctx_user())
                            or (ctx_kind() = 'agent' and added_kind = 'agent' and added_by is null)));
create policy ref_change on story_refs for update to editorial_app using (mine(publication_id) and can_write()) with check (mine(publication_id));
create policy ref_delete on story_refs for delete to editorial_app using (mine(publication_id) and can_write());

create policy cl_read on claims for select to editorial_app using (mine(publication_id) and (is_staff() or ctx_kind() = 'agent'));
create policy cl_insert on claims for insert to editorial_app with check (
  mine(publication_id) and ((can_write() and origin = 'human')
                            or (ctx_kind() = 'agent' and origin = 'agent' and verification = 'pending' and verified_by is null)));
create policy cl_update on claims for update to editorial_app using (mine(publication_id) and can_write()) with check (mine(publication_id));
create policy cl_delete on claims for delete to editorial_app using (mine(publication_id) and can_write());

-- uma afirmação só fica verificada por uma pessoa, e fica registado quem
create or replace function editorial.claims_guard() returns trigger language plpgsql as $$
begin
  if new.verification = 'verified' and (tg_op = 'INSERT' or old.verification <> 'verified') then
    if ctx_kind() <> 'human' then raise exception 'só uma pessoa marca uma afirmação como verificada'; end if;
    new.verified_by := ctx_user();
    new.verified_at := now();
  elsif new.verification <> 'verified' then
    new.verified_by := null; new.verified_at := null;
  end if;
  return new;
end $$;
create trigger claims_guard before insert or update on claims for each row execute function claims_guard();

grant select, insert, update on agent_outputs to editorial_app;
create policy ao_read on agent_outputs for select to editorial_app using (mine(publication_id) and (is_staff() or ctx_kind() = 'agent'));
create policy ao_insert on agent_outputs for insert to editorial_app with check (
  mine(publication_id) and ctx_kind() in ('agent','system') and status = 'proposed' and reviewed_by is null);
create policy ao_update on agent_outputs for update to editorial_app using (mine(publication_id) and can_write())
  with check (mine(publication_id) and reviewed_by = ctx_user());

-- ---------------------------------------------------------------- radar
grant select, insert, update, delete on feed_sources, feed_items to editorial_app;
create policy fs_read on feed_sources for select to editorial_app using (mine(publication_id) and (is_staff() or ctx_kind() in ('agent','system')));
create policy fs_insert on feed_sources for insert to editorial_app with check (mine(publication_id) and is_desk());
create policy fs_update on feed_sources for update to editorial_app using (mine(publication_id) and (is_desk() or ctx_kind() = 'system')) with check (mine(publication_id));
create policy fs_delete on feed_sources for delete to editorial_app using (mine(publication_id) and is_desk());
create policy fi_read on feed_items for select to editorial_app using (mine(publication_id) and (is_staff() or ctx_kind() in ('agent','system')));
create policy fi_insert on feed_items for insert to editorial_app with check (mine(publication_id) and ctx_kind() = 'system');
create policy fi_update on feed_items for update to editorial_app using (mine(publication_id) and (can_write() or ctx_kind() = 'system')) with check (mine(publication_id));
create policy fi_delete on feed_items for delete to editorial_app using (mine(publication_id) and is_desk());

-- ---------------------------------------------------------------- distribuição
grant select, insert, update, delete on distribution_items to editorial_app;
create policy di_read on distribution_items for select to editorial_app using (mine(publication_id) and (is_staff() or ctx_kind() = 'agent'));
create policy di_insert on distribution_items for insert to editorial_app with check (
  mine(publication_id) and state = 'draft' and approved_by is null
  and ((can_write() and prepared_kind = 'human') or (ctx_kind() = 'agent' and prepared_kind = 'agent')));
create policy di_update on distribution_items for update to editorial_app using (mine(publication_id) and can_write()) with check (mine(publication_id));
create policy di_delete on distribution_items for delete to editorial_app using (mine(publication_id) and is_desk());

create or replace function editorial.distribution_guard() returns trigger language plpgsql as $$
begin
  if ctx_kind() <> 'human' then raise exception 'só pessoas da redacção alteram um conteúdo de distribuição'; end if;
  if new.state is distinct from old.state and new.state in ('approved', 'handed_off', 'published') then
    if not is_desk() then raise exception 'a aprovação da distribuição é da edição ou da direcção'; end if;
    if not exists (select 1 from stories s where s.id = new.story_id and s.state in ('approved','scheduled','published')) then
      raise exception 'só se distribui uma peça aprovada';
    end if;
    if new.state = 'approved' then new.approved_by := ctx_user(); new.approved_at := now(); end if;
    if new.state in ('handed_off', 'published') and old.approved_by is null then
      raise exception 'o conteúdo ainda não foi aprovado por uma pessoa';
    end if;
  end if;
  if new.content is distinct from old.content and old.state in ('approved', 'handed_off') and new.state = old.state then
    new.state := 'in_review'; new.approved_by := null; new.approved_at := null;  -- o aprovado era outro conteúdo
  end if;
  new.updated_at := now();
  return new;
end $$;
create trigger distribution_guard before update on distribution_items for each row execute function distribution_guard();

-- ---------------------------------------------------------------- páginas e correcções
grant select, insert, update, delete on pages to editorial_app;
create policy pg_read on pages for select to editorial_app using (mine(publication_id) and (is_staff() or (ctx_kind() = 'public' and published)));
create policy pg_write on pages for all to editorial_app using (mine(publication_id) and is_lead()) with check (mine(publication_id) and is_lead());
grant select, insert on corrections to editorial_app;
create policy cor_read on corrections for select to editorial_app using (
  mine(publication_id) and (is_staff() or (ctx_kind() = 'public'
    and exists (select 1 from stories s where s.id = corrections.story_id and s.state = 'published'))));
create policy cor_insert on corrections for insert to editorial_app with check (mine(publication_id) and is_desk() and created_by = ctx_user());

-- ================================================================ funções de autenticação (sem contexto ainda)
-- SECURITY DEFINER: fazem uma única coisa cada, com search_path fixo; a aplicação nunca lê estas tabelas à solta.
create or replace function editorial.auth_user_by_email(p_email text)
returns table (id uuid, name text, password_hash text) language sql security definer set search_path = editorial, pg_temp as
$$ select u.id, u.name, u.password_hash from users u where u.email = p_email::citext and u.disabled_at is null $$;

create or replace function editorial.auth_memberships(p_user uuid)
returns table (publication_id uuid, slug text, name text, role text) language sql security definer set search_path = editorial, pg_temp as
$$ select p.id, p.slug, p.name, m.role::text from memberships m join publications p on p.id = m.publication_id
   where m.user_id = p_user order by p.name $$;

create or replace function editorial.auth_session_create(p_token_hash text, p_user uuid, p_publication uuid, p_expires timestamptz)
returns void language plpgsql security definer set search_path = editorial, pg_temp as $$
begin
  if not exists (select 1 from memberships where user_id = p_user and publication_id = p_publication) then
    raise exception 'sem acesso a esta publicação';
  end if;
  delete from sessions where expires_at < now();
  insert into sessions (token_hash, user_id, publication_id, expires_at) values (p_token_hash, p_user, p_publication, p_expires);
end $$;

create or replace function editorial.auth_session_get(p_token_hash text)
returns table (user_id uuid, name text, email text, publication_id uuid, role text) language sql security definer set search_path = editorial, pg_temp as
$$ select u.id, u.name, u.email::text, s.publication_id, m.role::text
   from sessions s join users u on u.id = s.user_id
   join memberships m on m.user_id = s.user_id and m.publication_id = s.publication_id
   where s.token_hash = p_token_hash and s.expires_at > now() and u.disabled_at is null $$;

create or replace function editorial.auth_session_delete(p_token_hash text)
returns void language sql security definer set search_path = editorial, pg_temp as
$$ delete from sessions where token_hash = p_token_hash $$;

create or replace function editorial.auth_api_token(p_token_hash text)
returns table (token_id uuid, publication_id uuid, name text, scopes text[]) language plpgsql security definer set search_path = editorial, pg_temp as $$
begin
  return query update api_tokens t set last_used_at = now()
    where t.token_hash = p_token_hash and t.revoked_at is null
    returning t.id, t.publication_id, t.name, t.scopes;
end $$;

create or replace function editorial.public_publication(p_host text, p_default_slug text)
returns uuid language sql security definer set search_path = editorial, pg_temp as
$$ select id from publications
   where (p_host <> '' and lower(domain) = lower(p_host)) or slug = p_default_slug
   order by (lower(coalesce(domain, '')) = lower(p_host)) desc limit 1 $$;

create or replace function editorial.system_publications()
returns table (id uuid) language sql security definer set search_path = editorial, pg_temp as
$$ select id from publications $$;

-- criar uma pessoa da equipa: só a direcção, dentro da sua publicação
create or replace function editorial.staff_create_member(p_email text, p_name text, p_password_hash text, p_role text, p_author_slug text)
returns uuid language plpgsql security definer set search_path = editorial, pg_temp as $$
declare uid uuid;
begin
  if ctx_kind() <> 'human' or ctx_role() not in ('admin', 'director') or ctx_publication() is null then
    raise exception 'só a direcção acrescenta pessoas à equipa';
  end if;
  if p_role = 'admin' and ctx_role() <> 'admin' then raise exception 'só um administrador cria administradores'; end if;
  select id into uid from users where email = p_email::citext;
  if uid is null then
    insert into users (email, name, password_hash) values (p_email, p_name, p_password_hash) returning id into uid;
  end if;
  insert into memberships (publication_id, user_id, role, author_slug, display_name)
    values (ctx_publication(), uid, p_role::member_role, p_author_slug, p_name);
  insert into audit_log (publication_id, actor_kind, actor_user_id, action, entity, entity_id, payload)
    values (ctx_publication(), 'human', ctx_user(), 'member.create', 'user', uid::text, jsonb_build_object('role', p_role));
  return uid;
end $$;

create or replace function editorial.staff_set_password(p_user uuid, p_password_hash text)
returns void language plpgsql security definer set search_path = editorial, pg_temp as $$
begin
  if ctx_kind() <> 'human' then raise exception 'operação reservada a pessoas'; end if;
  if p_user <> ctx_user() and not (ctx_role() = 'admin'
       and exists (select 1 from memberships where user_id = p_user and publication_id = ctx_publication())) then
    raise exception 'só o próprio ou um administrador muda a palavra-passe';
  end if;
  update users set password_hash = p_password_hash where id = p_user;
  delete from sessions where user_id = p_user;
  insert into audit_log (publication_id, actor_kind, actor_user_id, action, entity, entity_id)
    values (ctx_publication(), 'human', ctx_user(), 'member.password', 'user', p_user::text);
end $$;

revoke all on all functions in schema editorial from public;
grant execute on all functions in schema editorial to editorial_app;
grant usage on all sequences in schema editorial to editorial_app;
