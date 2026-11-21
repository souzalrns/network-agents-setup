-- Vertical editorial: o que seguiu para o agendador (Postiz) não volta atrás (revisão de código, 2026-11-21).
--
-- Antes: um conteúdo «enviado» podia voltar a rascunho ou revisão (a aprovação era apagada), ser reescrito,
-- reaprovado e enviado outra vez, criando um segundo post diferente para o mesmo item.
-- Agora: de «enviado» só se passa a «publicado» (o agendador publicou); de «publicado» não se sai. Para corrigir
-- uma publicação nas redes, cria-se uma adaptação nova (fica registada à parte).
set search_path = editorial, public;

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
  -- o que já seguiu para o agendador fica como foi: só «enviado» -> «publicado»
  if moving and old.state in ('handed_off', 'published')
     and not (old.state = 'handed_off' and new.state = 'published') then
    raise exception 'este conteúdo já seguiu para o agendador e não volta atrás: cria uma nova adaptação';
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
