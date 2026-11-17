-- Vertical editorial: rascunhos no servidor (D4).
-- O autosave grava um rascunho por peça, sem criar versões. As versões nascem em momentos controlados
-- (Guardar versão), com verificação de que ninguém gravou entretanto (base_version). Cada gravação do
-- rascunho leva o número da revisão que o browser conhece (rev): se outra pessoa gravou no meio, é conflito.
set search_path = editorial, public;

create table if not exists story_drafts (
  story_id       uuid primary key,
  publication_id uuid not null references publications on delete cascade,
  base_version   int not null,                     -- versão da peça sobre a qual o rascunho foi começado
  rev            int not null default 1,           -- sobe a cada gravação
  fields         jsonb not null,                   -- campos do artigo em edição
  updated_by     uuid references users,
  updated_at     timestamptz not null default now(),
  lease_user     uuid references users,            -- quem está a editar (aviso, não bloqueio)
  lease_until    timestamptz,
  foreign key (publication_id, story_id) references stories (publication_id, id) on delete cascade
);

alter table story_drafts enable row level security;
alter table story_drafts force row level security;

-- quem pode alterar a peça pode ter rascunho dela; a equipa lê (para saber que há trabalho por guardar)
create or replace function editorial.can_edit_story(p_story uuid) returns boolean language sql stable as $$
  select exists (select 1 from stories s where s.id = p_story and (
    is_desk() or (can_write() and ctx_user() in (s.assignee_id, s.author_id, s.created_by)
                  and s.state not in ('approved', 'scheduled', 'published')))
    and s.state <> 'archived')
$$;

grant select, insert, update, delete on story_drafts to editorial_app;
create policy dr_read on story_drafts for select to editorial_app using (mine(publication_id) and is_staff());
create policy dr_insert on story_drafts for insert to editorial_app
  with check (mine(publication_id) and can_edit_story(story_id) and updated_by = ctx_user());
create policy dr_update on story_drafts for update to editorial_app
  using (mine(publication_id) and can_edit_story(story_id))
  with check (mine(publication_id) and updated_by = ctx_user());
create policy dr_delete on story_drafts for delete to editorial_app using (mine(publication_id) and can_edit_story(story_id));

create or replace function editorial.drafts_guard() returns trigger language plpgsql as $$
begin
  if ctx_kind() <> 'human' then raise exception 'só pessoas da redacção têm rascunhos'; end if;
  if tg_op = 'UPDATE' then
    if new.story_id <> old.story_id or new.publication_id <> old.publication_id then raise exception 'um rascunho não muda de peça'; end if;
    new.rev := old.rev + 1;
  else
    new.rev := 1;
  end if;
  new.updated_by := ctx_user();
  new.updated_at := now();
  return new;
end $$;
drop trigger if exists drafts_guard on story_drafts;
create trigger drafts_guard before insert or update on story_drafts for each row execute function drafts_guard();

create index if not exists story_events_pub_at on story_events (publication_id, at desc);

grant execute on all functions in schema editorial to editorial_app;
