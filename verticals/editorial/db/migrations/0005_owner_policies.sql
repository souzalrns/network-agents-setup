-- Vertical editorial: o DONO do esquema vê tudo, também quando não é superutilizador (Neon, Postgres gerido).
--
-- Porquê: as funções SECURITY DEFINER (entrar, sessões, publicação pelo domínio, criar pessoas, regras de
-- aprovação) correm com os privilégios do dono. Com RLS FORÇADO, um dono que não é superutilizador também
-- obedece às políticas e, sem contexto, deixa de ver as próprias linhas: o login falha e o site não encontra
-- a publicação. Num Postgres local o dono é superutilizador e ignora o RLS, por isso o problema não aparecia.
--
-- O que muda: uma política «tudo» para o papel que corre esta migração (o dono). A aplicação liga-se SEMPRE com
-- `editorial_app`, que não é o dono e continua sujeita a todas as políticas: o que ela pode fazer não muda.
set search_path = editorial, public;

do $$
declare
  t text;
  owner_role text := current_user;
begin
  if owner_role = 'editorial_app' then
    raise exception 'as migrações correm com o dono do esquema, nunca com editorial_app';
  end if;
  for t in select c.relname from pg_class c join pg_namespace n on n.oid = c.relnamespace
           where n.nspname = 'editorial' and c.relkind = 'r' and c.relrowsecurity loop
    execute format('drop policy if exists owner_all on editorial.%I', t);
    execute format('create policy owner_all on editorial.%I for all to %I using (true) with check (true)', t, owner_role);
  end loop;
end $$;
