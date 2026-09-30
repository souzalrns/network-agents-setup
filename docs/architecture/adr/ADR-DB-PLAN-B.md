# ADR-DB-PLAN-B — Plano B de base de dados (saída do Supabase free)

| Campo | Valor |
|---|---|
| **ID** | ADR-DB-PLAN-B |
| **Estado** | Aceite (contingência; **não activada**) |
| **Data** | 2026-09-30 |
| **Decisores** | Dev; decisão fechada pelo Grok; redigido pelo Claude |
| **Relacionados** | D3 (L4 sobre Supabase, [DECISAO-3](../../audit/DECISAO-3-memoria.md)), J1/AU-47 (keep-alive), RAG canónico = `knowledge_chunks`, [ADR-META-AGENTS](./ADR-META-AGENTS.md) (checkpoints duráveis) |

## 1. Contexto

Tudo o que é persistente (RAG, L4 futura, filas, inventário) vive num projecto Supabase **free**. Limites do plano free, segundo o brief:
- pausa após 7 dias sem actividade;
- ~500 MB de base de dados;
- sem backups utilizáveis;
- o plano seguinte (Pro) custa US$ 25/mês.

Os valores exactos **NÃO foram verificados** contra a página de preços nesta sessão.

**Medido em 2026-09-30** (leitura SQL, projecto `agent-network-memory`):
- base com **17 MB**, ~3% do limite;
- extensões `vector 0.8.2` e `pg_cron 1.6.4`;
- maiores tabelas:

  | Tabela | Tamanho |
  |---|---|
  | `knowledge_chunks` | 1,2 MB |
  | `knowledge_chunks_t6` | 1,2 MB |
  | `pendencias_negocio` | 328 kB |
  | `transcripts` | 304 kB |

**A pausa não é teórica.** O segundo projecto da mesma organização (`vianna-gestao`) está `INACTIVE`. O keep-alive deste repo está morto: 5/5 runs falharam (AU-47, `.github/workflows/keep-alive.yml`).

## 2. Decisão

- **Agora:** ficar no Supabase free. Conserta-se primeiro o keep-alive (J1).
- **Plano B managed:** **Neon** (Postgres serverless com `pgvector`, sem a pausa de 7 dias que apaga o acesso).
- **Plano B local-first:** **Postgres + pgvector em Docker na VM Oracle** (imagem `pgvector/pgvector`, a mesma que o CI já usa: `.github/workflows/ci.yml:30`).
- **Não** se faz self-host do Supabase completo na Oracle (12 GB): é pesado demais para o que se usa. Ver "REJEITAR" em `docs/audit/PLANO-DE-ACAO.md`.

## 3. Gatilhos de saída do Supabase free (basta 1)

| # | Gatilho | Como medir |
|---|---|---|
| G1 | Base > **350 MB** (70% de 500 MB) | `select pg_database_size(current_database())` |
| G2 | **2 pausas** do projecto em 30 dias, apesar do keep-alive | Estado do projecto na consola / `list_projects` |
| G3 | Perda de dados, ou necessidade de restaurar sem backup disponível | Incidente registado |
| G4 | Precisar de uma funcionalidade fora do free (ex.: mais ligações, PITR, *compute* dedicado) para uma entrega concreta | Item no STATUS bloqueado por isso |

**Escolha entre B managed e B local-first**, quando um gatilho disparar:
- **A — Neon.** Custo: US$ 0 no tier free da Neon (limites **NÃO VERIFICADOS**). Consequência: continua managed, sem operar servidor.
- **B — Postgres na Oracle.** Custo: US$ 0 (VM já existente). Consequência: tu operas backups, updates e segurança.
- **C — Supabase Pro.** Custo: US$ 25/mês. Consequência: zero migração.
- **RECOMENDADA: A.** Não obriga a operar servidor e a VM Oracle ainda tem a chave antiga no `pm2` (S20/J2). Se o Dev não responder em 7 dias após um gatilho disparar, executa-se A.

## 4. Checklist de capacidade da VM Oracle (antes do local-first)

- [ ] **RAM livre** ≥ 2 GB para o Postgres (a VM tem 12 GB, segundo o brief; uso actual **NÃO VERIFICÁVEL** daqui, falta SSH, S27).
- [ ] **Disco livre** ≥ 10 GB, num volume que sobreviva a um *rebuild* da VM.
- [ ] **Docker** + `docker compose` instalados; imagem `pgvector/pgvector:pg16` ou `pg17` a arrancar.
- [ ] **Backups:** `pg_dump` diário por cron + cópia **fora** da VM (Object Storage Oracle free ou outro). Restauro testado 1× antes de migrar.
- [ ] **Rede:** porta 5432 **não** exposta à Internet; acesso por túnel/VPN ou só `localhost` + app na mesma VM.
- [ ] **Credenciais:** a chave antiga do `pm2` já rodada (S20/J2) antes de lá pôr dados.

## 5. Checklist Neon

- [ ] Conta criada; região UE (a mais próxima de `eu-central-1`).
- [ ] `CREATE EXTENSION vector;` aceite; versão ≥ 0.8.
- [ ] `pg_cron` disponível, ou os jobs passam para GitHub Actions / cron da VM.
- [ ] Limites do tier free (armazenamento, horas de *compute*, *branches*) lidos e anotados aqui.
- [ ] *Connection string* guardada **só** em secrets (`.env` local, secrets do Vercel/GitHub); nunca em commit.
- [ ] RLS: as políticas que existem no Supabase (ex.: `knowledge_chunks_t6`, A2) re-criadas, ou substituídas por um utilizador de BD com privilégios mínimos. No Neon não há `auth.uid()`.

## 6. Checklist de migração (M0–M12)

| # | Passo |
|---|---|
| M0 | Congelar escritas: parar o keep-alive, a ingestão (`ingest-knowledge.yml`) e o `bridge-worker` |
| M1 | Inventário: tabelas, RPCs (`match_knowledge`…), extensões, jobs `pg_cron`, políticas RLS |
| M2 | `pg_dump --schema-only` do Supabase; remover dependências do esquema `auth`/`storage` que não existem fora do Supabase |
| M3 | Criar o destino (Neon ou Oracle) e aplicar extensões (`vector`, `pg_cron` se houver) |
| M4 | Aplicar o esquema; corrigir erros de dependência |
| M5 | `pg_dump --data-only` + restauro; conferir contagens por tabela (origem = destino) |
| M6 | Re-criar índices vectoriais (HNSW/IVFFlat) e fazer `ANALYZE` |
| M7 | Re-criar RPCs e testar `match_knowledge` com 3 perguntas conhecidas (mesmos top-k) |
| M8 | Re-criar jobs (`pg_cron` ou equivalente externo) |
| M9 | Trocar secrets (`SUPABASE_*` → `DATABASE_URL`) no `agent-network-mcp` (Vercel), no GitHub Actions e no `.env` local |
| M10 | Testes: suíte do runner + *smoke* do MCP em produção |
| M11 | Janela de observação de 7 dias com o Supabase em só-leitura (rollback possível) |
| M12 | Desligar o Supabase antigo e actualizar STATUS, `CLAUDE.md` e este ADR (estado → "Activado") |

## 7. O que fica no Supabase até activar o Plano B

- **Tudo o que existe hoje:**
  - `knowledge_chunks` (tabela RAG canónica);
  - `knowledge_chunks_t6` (abandonada; a remover depois de migrar o que for útil);
  - `pendencias_negocio`, `system_inventory`, `transcripts`, `code_tasks`, `tool_evaluations`, etc.
- **Tudo o que vier a seguir:** a **L4 própria** (D3) nasce aqui, com SQL **Postgres puro** (sem `auth.*`, sem funções exclusivas do Supabase) para a migração ser só `pg_dump`/restauro.
- **Regra:** nenhuma funcionalidade nova pode depender de algo que só o Supabase tem (Auth, Storage, Realtime) sem um ADR a aceitar esse acoplamento.
