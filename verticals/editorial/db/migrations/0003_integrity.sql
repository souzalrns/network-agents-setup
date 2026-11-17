-- Vertical editorial: integridade da aprovação (revisão técnica, contornos R1–R8).
-- A aprovação fica presa ao conteúdo aprovado: uma impressão digital (sha256) de tudo o que o leitor vê.
-- Agendar e publicar exigem que o conteúdo seja exactamente o aprovado e que as afirmações do artigo
-- continuem verificadas. Mudar o conteúdo e mudar o estado são sempre operações separadas.
set search_path = editorial, public;

-- ---------------------------------------------------------------- impressão digital do conteúdo
-- Tudo o que chega ao leitor: textos, endereço, editoria, autoria, imagem, legenda, crédito, etiquetas,
-- SEO e tipo (patrocinado ou não). Muda um destes campos, muda a impressão digital.
create or replace function editorial.story_fingerprint(s editorial.stories) returns text language sql stable as $$
  select encode(sha256(convert_to(jsonb_build_array(
    s.title, s.subtitle, s.summary, s.body, s.slug, s.section_id, s.author_id, s.hero_image_url,
    s.hero_caption, s.hero_credit, s.tags, s.seo_title, s.meta_description, s.kind)::text, 'UTF8')), 'hex')
$$;

create or replace function editorial.story_snapshot(s editorial.stories) returns jsonb language sql stable as $$
  select jsonb_build_object('title', s.title, 'subtitle', s.subtitle, 'summary', s.summary, 'body', s.body,
    'slug', s.slug, 'section_id', s.section_id, 'author_id', s.author_id, 'hero_image_url', s.hero_image_url,
    'hero_caption', s.hero_caption, 'hero_credit', s.hero_credit, 'tags', s.tags, 'seo_title', s.seo_title,
    'meta_description', s.meta_description, 'kind', s.kind)
$$;

alter table stories add column if not exists approved_fingerprint text;
alter table stories add column if not exists approved_version int;
alter table story_versions add column if not exists snapshot jsonb;
alter table story_versions add column if not exists fingerprint text;

-- Afirmações que impedem aprovar, agendar ou publicar. SECURITY DEFINER porque o sistema (publicação
-- agendada) não lê afirmações: a regra tem de ver todas, seja quem for que actua.
create or replace function editorial.story_claims_block(p_story uuid) returns boolean
language sql stable security definer set search_path = editorial, pg_temp as $$
  select exists (select 1 from claims c where c.story_id = p_story and c.in_article
    and (c.kind = 'unconfirmed' or (c.kind = 'fact' and c.verification <> 'verified')
         or c.verification in ('disputed', 'unsupported')))
$$;

create or replace function editorial.four_eyes(p_publication uuid) returns boolean
language sql stable security definer set search_path = editorial, pg_temp as $$
  select coalesce((settings->>'require_second_reviewer')::boolean, true) from publications where id = p_publication
$$;

create or replace function editorial.story_author(p_story uuid) returns uuid
language sql stable security definer set search_path = editorial, pg_temp as $$
  select author_id from stories where id = p_story
$$;

-- ---------------------------------------------------------------- peças
create or replace function editorial.stories_guard() returns trigger language plpgsql as $$
declare
  k text := ctx_kind();
  fp_old text := story_fingerprint(old);
  fp_new text := story_fingerprint(new);
  changed boolean;
  moving boolean := new.state is distinct from old.state;
  note text := btrim(coalesce(current_setting('app.note', true), ''));
begin
  changed := fp_new is distinct from fp_old;
  if k not in ('human', 'system') then raise exception 'só pessoas da redacção alteram uma peça'; end if;
  if new.publication_id <> old.publication_id then raise exception 'uma peça não muda de publicação'; end if;
  -- os campos da aprovação são da base de dados: ninguém os escreve directamente
  if (new.approved_by, new.approved_at, new.approved_fingerprint, new.approved_version, new.scheduled_by, new.published_at)
     is distinct from (old.approved_by, old.approved_at, old.approved_fingerprint, old.approved_version, old.scheduled_by, old.published_at) then
    raise exception 'a aprovação e a publicação só mudam pelo fluxo editorial';
  end if;

  if k = 'system' then
    -- o sistema só executa o que uma pessoa agendou: scheduled -> published, à hora marcada, sem tocar no conteúdo
    if not (old.state = 'scheduled' and new.state = 'published' and old.scheduled_by is not null
            and old.scheduled_at is not null and old.scheduled_at <= now() and not changed) then
      raise exception 'o sistema só publica uma peça agendada por uma pessoa, à hora marcada';
    end if;
  end if;

  if changed then
    if moving and new.state in ('approved', 'scheduled', 'published') then
      raise exception 'grava o texto e muda o estado em passos separados: só se aprova, agenda ou publica o que já está guardado';
    end if;
    if old.state = 'archived' then raise exception 'uma peça arquivada não se altera: reabre-a primeiro'; end if;
    if k = 'human' and old.state in ('approved', 'scheduled', 'published') and not is_desk() then
      raise exception 'uma peça aprovada só é alterada pela edição';
    end if;
  end if;

  if new.scheduled_at is distinct from old.scheduled_at and not moving and new.state = 'scheduled' then
    raise exception 'para mudar a hora, cancela o agendamento e volta a agendar';
  end if;

  if moving then
    if new.state in ('pitch_approved', 'approved', 'scheduled', 'published', 'archived') and k = 'human' and not is_desk() then
      raise exception 'esta mudança de estado é da edição ou da direcção';
    end if;
    if new.state = 'approved' and old.state = 'scheduled' then
      -- cancelar o agendamento: a aprovação mantém-se, a data sai
      new.scheduled_at := null; new.scheduled_by := null;
    elsif new.state = 'approved' then
      if old.state <> 'in_review' then raise exception 'só se aprova uma peça que está em revisão'; end if;
      if four_eyes(new.publication_id) and new.author_id is not null and new.author_id = ctx_user() then
        raise exception 'quem escreveu a peça não a aprova: pede a aprovação a outra pessoa da edição';
      end if;
      if story_claims_block(new.id) then
        raise exception 'há afirmações por verificar no artigo: verifica-as ou retira-as antes de aprovar';
      end if;
      if length(btrim(new.body)) = 0 or new.section_id is null or new.author_id is null or new.slug is null then
        raise exception 'falta texto, editoria, autor ou endereço para aprovar a peça';
      end if;
      new.approved_by := ctx_user(); new.approved_at := now();
      new.approved_fingerprint := fp_new; new.approved_version := new.version;
    end if;
    if new.state = 'scheduled' then
      if old.state <> 'approved' then raise exception 'só se agenda uma peça aprovada'; end if;
      if new.scheduled_at is null or new.scheduled_at <= now() then raise exception 'a data de publicação tem de ser futura'; end if;
      if old.approved_fingerprint is null or old.approved_fingerprint <> fp_new then
        raise exception 'o conteúdo não é o que foi aprovado: volta a pedir aprovação';
      end if;
      if story_claims_block(new.id) then
        raise exception 'há afirmações por verificar no artigo: não se agenda até estarem verificadas ou retiradas';
      end if;
      new.scheduled_by := ctx_user();
    end if;
    if new.state = 'published' then
      if old.state not in ('approved', 'scheduled', 'archived') then raise exception 'só se publica uma peça aprovada'; end if;
      if old.approved_by is null then raise exception 'a peça nunca foi aprovada por uma pessoa'; end if;
      if old.approved_fingerprint is null or old.approved_fingerprint <> fp_new then
        raise exception 'o conteúdo a publicar não é o que foi aprovado: volta a pedir aprovação';
      end if;
      if story_claims_block(new.id) then
        raise exception 'há afirmações por verificar no artigo: não se publica até estarem verificadas ou retiradas';
      end if;
      new.published_at := coalesce(old.published_at, now());
    end if;
    -- sair do circuito aprovado (devolver, reabrir) apaga a aprovação; arquivar guarda-a para poder voltar a publicar
    if new.state not in ('approved', 'scheduled', 'published', 'archived') then
      new.approved_by := null; new.approved_at := null; new.approved_fingerprint := null; new.approved_version := null;
      new.scheduled_at := null; new.scheduled_by := null;
    end if;
  end if;

  if changed and not moving then
    if old.state in ('approved', 'scheduled') then
      -- o que foi aprovado era outro conteúdo
      new.state := 'in_review';
      new.approved_by := null; new.approved_at := null; new.approved_fingerprint := null; new.approved_version := null;
      new.scheduled_at := null; new.scheduled_by := null;
    elsif old.state = 'published' then
      -- editar uma peça publicada: só a edição, com nota obrigatória, e conta como nova aprovação (D5)
      if length(note) = 0 then raise exception 'alterar uma peça publicada exige uma nota que explique a alteração'; end if;
      if four_eyes(new.publication_id) and new.author_id is not null and new.author_id = ctx_user() then
        raise exception 'quem escreveu a peça não aprova a alteração: pede-a a outra pessoa da edição';
      end if;
      if story_claims_block(new.id) then
        raise exception 'há afirmações por verificar no artigo: resolve-as antes de alterar a peça publicada';
      end if;
      new.approved_by := ctx_user(); new.approved_at := now(); new.approved_fingerprint := fp_new;
    end if;
  end if;

  if changed then new.version := old.version + 1; end if;
  if new.approved_fingerprint is not null and new.approved_fingerprint is distinct from old.approved_fingerprint then
    new.approved_version := new.version;
  end if;
  new.updated_at := now();
  return new;
end $$;

-- cada mudança de estado e cada versão ficam registadas pela base de dados (agora com o conteúdo completo)
create or replace function editorial.stories_log() returns trigger language plpgsql as $$
declare label text := coalesce(nullif(current_setting('app.actor_label', true), ''), ctx_kind());
        note text := coalesce(nullif(current_setting('app.note', true), ''), '');
begin
  if tg_op = 'INSERT' then
    insert into story_events (publication_id, story_id, type, from_state, to_state, actor_kind, actor_user_id, actor_label, note)
      values (new.publication_id, new.id, 'state_change', null, new.state, ctx_kind(), ctx_user(), label, note);
    insert into story_versions (publication_id, story_id, version, title, subtitle, summary, body, saved_by, saved_kind, snapshot, fingerprint)
      values (new.publication_id, new.id, new.version, new.title, new.subtitle, new.summary, new.body, ctx_user(), ctx_kind(),
              story_snapshot(new), story_fingerprint(new));
    return new;
  end if;
  if new.state is distinct from old.state then
    insert into story_events (publication_id, story_id, type, from_state, to_state, actor_kind, actor_user_id, actor_label, note)
      values (new.publication_id, new.id, 'state_change', old.state, new.state, ctx_kind(), ctx_user(), label, note);
  end if;
  if new.version <> old.version then
    insert into story_versions (publication_id, story_id, version, title, subtitle, summary, body, saved_by, saved_kind, note, snapshot, fingerprint)
      values (new.publication_id, new.id, new.version, new.title, new.subtitle, new.summary, new.body, ctx_user(), ctx_kind(), note,
              story_snapshot(new), story_fingerprint(new));
    if old.state = 'published' and new.state = 'published' then
      insert into story_events (publication_id, story_id, type, actor_kind, actor_user_id, actor_label, note, payload)
        values (new.publication_id, new.id, 'published_edit', ctx_kind(), ctx_user(), label, note,
                jsonb_build_object('from_version', old.version, 'to_version', new.version));
    end if;
  end if;
  if new.assignee_id is distinct from old.assignee_id then
    insert into story_events (publication_id, story_id, type, actor_kind, actor_user_id, actor_label, payload)
      values (new.publication_id, new.id, 'assignment', ctx_kind(), ctx_user(), label,
              jsonb_build_object('from', old.assignee_id, 'to', new.assignee_id));
  end if;
  return new;
end $$;

-- ---------------------------------------------------------------- afirmações
alter table claims add column if not exists created_by uuid references users;

-- a revisão (fact-checking) marca a verificação; não reescreve afirmações
drop policy if exists cl_update on claims;
create policy cl_update on claims for update to editorial_app
  using (mine(publication_id) and (can_write() or (ctx_kind() = 'human' and ctx_role() = 'reviewer')))
  with check (mine(publication_id));

create or replace function editorial.claims_guard() returns trigger language plpgsql as $$
declare content_changed boolean := true;
        author uuid;
begin
  if tg_op = 'INSERT' then
    new.created_by := case when ctx_kind() = 'human' then ctx_user() end;
  else
    if new.story_id <> old.story_id or new.publication_id <> old.publication_id then
      raise exception 'uma afirmação não muda de peça';
    end if;
    new.created_by := old.created_by;
    content_changed := (new.text, new.kind, new.attributed_to, new.evidence)
      is distinct from (old.text, old.kind, old.attributed_to, old.evidence);
    if ctx_role() = 'reviewer' and (content_changed or new.in_article is distinct from old.in_article) then
      raise exception 'a revisão só marca o estado da verificação';
    end if;
    -- verificar é uma acção à parte: mudar o texto, o tipo, a atribuição ou a evidência volta a pôr a afirmação por verificar
    if content_changed and new.verification = 'verified' then new.verification := 'pending'; end if;
  end if;

  if new.verification = 'verified' and (tg_op = 'INSERT' or old.verification <> 'verified') then
    if ctx_kind() <> 'human' then raise exception 'só uma pessoa marca uma afirmação como verificada'; end if;
    author := story_author(new.story_id);
    if four_eyes(new.publication_id) and (ctx_user() = author or ctx_user() = new.created_by) then
      raise exception 'quem escreveu a peça ou registou a afirmação não a verifica: pede a verificação a outra pessoa';
    end if;
    new.verified_by := ctx_user(); new.verified_at := now();
  elsif new.verification <> 'verified' then
    new.verified_by := null; new.verified_at := null;
  else
    new.verified_by := old.verified_by; new.verified_at := old.verified_at;  -- continua verificada por quem a verificou
  end if;
  return new;
end $$;

-- ---------------------------------------------------------------- distribuição
alter table distribution_items add column if not exists approved_hash text;

create or replace function editorial.distribution_hash(p_channel text, p_content jsonb) returns text language sql immutable as
$$ select encode(sha256(convert_to(jsonb_build_array(p_channel, p_content)::text, 'UTF8')), 'hex') $$;

create or replace function editorial.distribution_guard() returns trigger language plpgsql as $$
declare
  h text := distribution_hash(new.channel, new.content);
  changed boolean := (new.channel, new.content) is distinct from (old.channel, old.content);
  moving boolean := new.state is distinct from old.state;
begin
  if ctx_kind() <> 'human' then raise exception 'só pessoas da redacção alteram um conteúdo de distribuição'; end if;
  if new.story_id <> old.story_id or new.publication_id <> old.publication_id then
    raise exception 'um conteúdo de distribuição não muda de peça';
  end if;
  if (new.approved_by, new.approved_at, new.approved_hash) is distinct from (old.approved_by, old.approved_at, old.approved_hash) then
    raise exception 'a aprovação da distribuição só muda pelo fluxo';
  end if;
  if changed then
    if moving and new.state in ('approved', 'handed_off', 'published') then
      raise exception 'grava o texto e aprova ou envia em passos separados';
    end if;
    if old.state in ('handed_off', 'published') then
      raise exception 'este conteúdo já seguiu para o agendador: cria uma nova adaptação';
    end if;
    if old.state = 'approved' then
      new.state := 'in_review'; new.approved_by := null; new.approved_at := null; new.approved_hash := null;
    end if;
  end if;
  if moving and new.state in ('approved', 'handed_off', 'published') then
    if not is_desk() then raise exception 'a aprovação da distribuição é da edição ou da direcção'; end if;
    if not exists (select 1 from stories s where s.id = new.story_id and s.state in ('approved','scheduled','published')) then
      raise exception 'só se distribui uma peça aprovada';
    end if;
    if new.state = 'approved' then
      new.approved_by := ctx_user(); new.approved_at := now(); new.approved_hash := h;
    elsif old.approved_by is null or old.approved_hash is distinct from h then
      raise exception 'o conteúdo não é o que foi aprovado por uma pessoa';
    end if;
  end if;
  if moving and new.state in ('draft', 'in_review', 'discarded') then
    new.approved_by := null; new.approved_at := null; new.approved_hash := null;
  end if;
  new.updated_at := now();
  return new;
end $$;

-- ---------------------------------------------------------------- dados existentes
-- As peças já aprovadas ficam presas ao conteúdo que têm hoje; as versões antigas ganham o retrato completo
-- possível (só o texto era guardado). Sem triggers: é a própria migração, como dono do esquema.
set local session_replication_role = replica;
update stories s set approved_fingerprint = story_fingerprint(s), approved_version = s.version
  where s.approved_by is not null and s.approved_fingerprint is null;
update distribution_items d set approved_hash = distribution_hash(d.channel, d.content)
  where d.approved_by is not null and d.approved_hash is null;
set local session_replication_role = origin;

grant execute on all functions in schema editorial to editorial_app;
revoke all on function editorial.story_claims_block(uuid), editorial.four_eyes(uuid), editorial.story_author(uuid) from public;
grant execute on function editorial.story_claims_block(uuid), editorial.four_eyes(uuid), editorial.story_author(uuid) to editorial_app;
