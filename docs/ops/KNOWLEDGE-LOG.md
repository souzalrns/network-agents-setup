# `knowledge_log`: investigação (R-001)

> **Estado (2026-10-03):** investigação de código feita; o dono e o uso **continuam por confirmar** e precisam das queries da §3, só de leitura e corridas pelo DEV no projecto Supabase `agent-network-memory`.
> **IDs:** R-001 em `docs/initiatives/PENDENCIAS.md` (antes B12 no STATUS e E9 no OPEN-ITEMS).

## 1. O que se sabe (com evidência)

| Facto | Evidência |
|---|---|
| A tabela existe no Supabase, com 7 colunas, RLS activa e a policy `anon_deny` | `docs/initiatives/STATUS.md:107` (B12, achado do A2 a 2026-09-19); `docs/audit/AUDIT-5-itens.md:138` |
| **Nenhum código actual a lê ou escreve**, em nenhum dos 2 repos | `grep -rn knowledge_log` em `network-agents-setup` e `agent-network-mcp` (`*.py`, `*.js`, `*.ts`, `*.sql`, `*.yml`; sem `node_modules`/`.next`): a única ocorrência fora de docs é o comentário de `scripts/migrations/enable_rls_knowledge_tables.sql:2` |
| **Nenhum código a leu ou escreveu no passado** no repo MCP | `git log --all -S knowledge_log` no `agent-network-mcp`: 0 commits |
| No `network-agents-setup` só aparece como referência do padrão de RLS | `git log --all -S knowledge_log -- . ':!docs'`: 1 commit, `ba47a12` (2026-09-19, RLS das tabelas do T6) |
| Não está no DDL canónico do RAG | `scripts/rag_schema.sql` (AU-11) não a inclui; nada no ingest nem no retrieve depende dela |

## 2. O que não se sabe (NÃO VERIFICADO)

- **Quem a criou e quem escreve nela.** O projecto `agent-network-memory` é partilhado por outros repos a que esta investigação não teve acesso: o `bridge-worker` (tabela `code_tasks`), `mesaflow-api`, `vianna-gestao`, entre outros. Um deles, ou um passo manual antigo no SQL Editor, pode ser o dono.
- **Se tem dados e se recebe escritas.**
- **Se algum trigger, função ou view a usa.** Isso explicaria o nome: um log automático de escritas na `knowledge_chunks`.

## 3. Queries de controlo (SÓ LEITURA; não mostram o conteúdo das linhas)

```sql
-- 1) Colunas
SELECT column_name, data_type, column_default, is_nullable
FROM information_schema.columns
WHERE table_schema = 'public' AND table_name = 'knowledge_log'
ORDER BY ordinal_position;

-- 2) Volume e actividade (estatísticas do Postgres, sem ler linhas)
SELECT n_live_tup, n_tup_ins, n_tup_upd, n_tup_del, last_autovacuum, last_autoanalyze
FROM pg_stat_user_tables WHERE relname = 'knowledge_log';

-- 3) Triggers na própria tabela
SELECT tgname, pg_get_triggerdef(t.oid)
FROM pg_trigger t JOIN pg_class c ON c.oid = t.tgrelid
WHERE c.relname = 'knowledge_log' AND NOT t.tgisinternal;

-- 4) Funções e views que a referem (inclui triggers noutras tabelas que escrevem nela)
SELECT 'function' AS kind, p.proname AS name FROM pg_proc p WHERE p.prosrc ILIKE '%knowledge_log%'
UNION ALL
SELECT 'view', viewname FROM pg_views WHERE definition ILIKE '%knowledge_log%';

-- 5) Policies
SELECT policyname, roles, cmd FROM pg_policies WHERE tablename = 'knowledge_log';
```

## 4. Como decidir depois das queries

| Resultado | Opção | Recomendada |
|---|---|---|
| A query 4 encontra um trigger/função que escreve nela | **A:** documentar aqui o dono e o propósito; incluí-la no `scripts/rag_schema.sql` se fizer parte do RAG | **A** neste caso |
| `n_live_tup = 0`, `n_tup_ins = 0` e nada a refere | **B:** marcar como órfã e propor `DROP TABLE` num SQL versionado (escrita em produção → DEV, com backup) | **B** neste caso |
| Tem dados, mas nada a refere nos repos | **C:** perguntar aos outros repos do projecto antes de tocar; manter como está | **C** neste caso |

O R-001 fecha quando esta tabela tiver o resultado das queries e a opção escolhida.
