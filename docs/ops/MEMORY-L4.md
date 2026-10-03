# Memória L4 — memória semântica persistente (D3)

> **Estado (2026-10-01):** **merged (#47, `a941147`, 8 checks verdes)**; implementada e testada localmente e no CI contra Postgres 16 + pgvector:
> - 18 testes do módulo (`runner/tests/test_memory_l4.py`);
> - 11 da integração com o worker (`runner/tests/test_memory_l4_worker.py`), incluindo o ciclo **entre runs**: o run 1 propõe, o humano aprova, o run 3 lembra.
>
> **Em produção desde 2026-10-01 (L4-1):** o maestro correu os 2 SQL no Supabase, com verificação 4/4 (secção "Pôr em produção"). Falta o teste real mínimo (passo 3, L4-1b).

Decisão: [DECISAO-3-memoria.md](../audit/DECISAO-3-memoria.md), VIA A (L4 própria, sem mem0, escrita explícita, Supabase). Contrato: [contracts.md](../architecture/memory/contracts.md), [scopes.md](../architecture/memory/scopes.md), [layers.md](../architecture/memory/layers.md) (L4).

## Peças

| Peça | Ficheiro |
|---|---|
| Tabela `memory_l4` (RLS, REVOKE, triggers) | `scripts/create_memory_l4_table.sql` |
| RPC `recall_l4` | `scripts/create_recall_l4_rpc.sql` |
| `remember` / `recall` / `forget` / `promote` + HITL de promoção + CLI | `runner/plan_runner/memory_l4.py` |
| Ligação ao worker (recall antes, remember opt-in) | `runner/plan_runner/memory_wiring.py` |

## Regras (onde estão impostas)

| Regra | Origem | Imposta em |
|---|---|---|
| `remember` sem âmbito é recusado | `scopes.md:26` | código |
| Âmbitos `global ⊂ org ⊂ project ⊂ (user \| agent) ⊂ run`. O `run` é L2 (`events.jsonl`) e não entra na L4 | `scopes.md:5`, `contracts.md:20` | código + `CHECK` na BD |
| **Ninguém eleva o âmbito**: um agente só escreve em `project`/`user`/`agent`, e só nos ids da cadeia do próprio passo; `org` e `global` só por humano | `scopes.md:23-24` | código (`AGENT_WRITABLE` + `allowed`) |
| Agente escreve `candidate`; `active` só por gate humano. Um agente que peça `active` é **recusado**, não rebaixado | `contracts.md:29,34` | código |
| **Não editar em silêncio**: `statement`, `subject` e âmbito são imutáveis. Corrigir = facto novo com `supersedes`; o antigo passa a `superseded` **quando o novo for promovido** | `layers.md:44` | trigger na BD + código |
| **Não apagar**: `forget` = tombstone (`archived`, com quem e porquê) | `contracts.md:68` | trigger na BD (DELETE proibido) |
| `recall` com `limit` em 1..50, por âmbito + `query` + `tags` | `contracts.md:36-52` | código + RPC |
| `ttl?` | `layers.md:43` | coluna `expires_at`: o recall ignora as expiradas |
| Escrita **explícita**; nada extrai factos sozinho | D3 | a L4 só grava o que um humano escreve (CLI) ou o que um passo com `remember: true` propõe; tudo `candidate` até um humano aprovar |
| `MEMORY.md` é fallback humano, não fonte de verdade | D3 | o `CLIENT_MEMORY.md` (S30) continua só de leitura; a fonte de verdade é a `memory_l4` |

**Compliance (apagamento real):** só numa sessão de admin, explícita:

```sql
BEGIN; SET LOCAL memory_l4.allow_delete = 'on'; DELETE FROM memory_l4 WHERE id = '...'; COMMIT;
```

## Estados

```
candidate ──promote (humano)──► active ──forget──► archived
    │                              │
    └──forget / reject (HITL)──► archived
active ──(um facto novo com supersedes é promovido)──► superseded
```

O `recall` devolve só `active` (e `candidate` com `include_candidates`). Nunca devolve `archived`, `superseded` ou expiradas.

## No worker (planos)

**Sem bloco `memory:` não há L4 nenhuma**: o worker nem liga à BD (teste `test_plano_sem_memory_nao_toca_na_l4`).

```yaml
memory:                        # a cadeia de âmbitos deste trabalho
  org: acme                    # opcional
  project: site-a              # recomendado
  user: maria                  # opcional
  recall: {limit: 8, tags: [], include_candidates: false}   # omissões
steps:
  - id: copy
    action: copy_social
    remember: true             # opt-in: o agente pode propor factos (candidate)
    # remember: {scope: project|user|agent, max: 5, tags: [brand]}
    # recall: false            # desliga o recall só neste passo
```

- **Recall** (antes da chamada ao Gemini):
  - a cadeia é `global:global` + `org` + `project` + `user` + `agent:<id do AGENT.md>`;
  - só memórias **active** entram no prompt, numa secção "Memória L4 (factos entre runs)", com âmbito, id e confiança, num máximo de 4 000 caracteres;
  - a query é o objectivo do plano mais a tarefa e a action do passo.
- **Remember** (`remember: true`):
  - o prompt pede até `max` factos estáveis, com fonte, num bloco à parte (`=====MEMORIA=====` em Markdown; chave `memoria` em JSON);
  - o worker tira-os do artefacto, grava-os como `candidate` no âmbito pedido (por omissão `project`, ou `agent` se o plano não tiver projecto), com `source_run_id`, `tags` (`step:<id>`) e embedding;
  - abre um pedido HITL de promoção e regista tudo em `<run>/memory_l4.jsonl`.
- **O run não pára:** a promoção é assíncrona. Os candidatos só entram nos prompts depois de aprovados.
- **Falhas** (BD em baixo, sem tabela, sem `DATABASE_URL`): o passo segue sem L4 e o motivo fica em `result.json → meta.memory`.

## Promoção por HITL

Os pedidos usam o **mesmo contrato `hitl-request-v1`** do HITL durável (validado no teste), em ficheiros próprios: `<run>/memory-requests.jsonl` e `memory-decisions.jsonl`. Não ficam em `hitl-*.jsonl`, porque o `resume` lê a última decisão desse ficheiro como decisão do gate do run, e uma decisão de memória não pode ser confundida com ela.

```bash
cd runner
python -m plan_runner.memory_l4 pending ../pilots/<run>                      # pedidos por decidir
python -m plan_runner.memory_l4 decide ../pilots/<run> <hitl_id> approve     # -> active
python -m plan_runner.memory_l4 decide ../pilots/<run> <hitl_id> reject --comment "não confirmado"   # -> archived
python -m plan_runner.memory_l4 candidates --scope project:site-a            # fila na BD, entre runs
```

## CLI humana

```bash
python -m plan_runner.memory_l4 remember --scope project:site-a --subject tom "O cliente prefere tom formal [Fonte: …]"
python -m plan_runner.memory_l4 remember --scope project:site-a --active "…"         # humano: já confirmado
python -m plan_runner.memory_l4 remember --scope project:site-a --supersedes <id> "…" # corrigir sem editar
python -m plan_runner.memory_l4 recall --scope global:global --scope project:site-a [--query "…"] [--candidates]
python -m plan_runner.memory_l4 promote <id>
python -m plan_runner.memory_l4 forget <id> --reason "…"
```

`--by <nome>` define o humano (por omissão, o utilizador do sistema). Com `GEMINI_API_KEY`, as escritas e as queries levam embedding (`gemini-embedding-001`); sem ela, o recall ordena por recência.

## Evidência (2026-10-01, BD local de demonstração, CLI)

| # | Operação | Resultado |
|---|---|---|
| 1 | `remember --scope project:site-a` | `candidate`, `human:maestro` |
| 2 | `recall` (omissão) | 0 (candidate não sai) |
| 3 | `recall --candidates` | o mesmo facto |
| 4 | `promote` | `active` por `human:maestro` |
| 5 | `recall` | o facto; `project:site-b` → 0 |
| 6 | `forget --reason …` | `archived` + motivo |
| 7 | `recall --candidates` | 0 |
| 8 | `select … from memory_l4` | a linha continua lá (`archived`) |
| 9 | `DELETE` directo | recusado pelo trigger |

## Pôr em produção (passo do DEV)

1. **Supabase → projecto `agent-network-memory` (`mpsuurqilnhsvbnjmrpm`) → SQL Editor**, por esta ordem:
   1. `scripts/create_memory_l4_table.sql`
   2. `scripts/create_recall_l4_rpc.sql`

   Os dois são idempotentes e foram testados 2× seguidas, num Postgres simples e num com os papéis do Supabase simulados.
2. **Confirmar:**
   ```sql
   select relrowsecurity from pg_class where relname = 'memory_l4';                     -- true
   select grantee, privilege_type from information_schema.role_table_grants
    where table_name = 'memory_l4' and grantee in ('anon','authenticated');              -- 0 linhas
   select has_function_privilege('anon', 'public.recall_l4(vector,text[],text[],int,text[],boolean)', 'execute');  -- false
   ```
   **Resultado (L4-1, maestro, 2026-10-01, projecto `mpsuurqilnhsvbnjmrpm`):**

   | Verificação | Resultado |
   |---|---|
   | Tabela `memory_l4` | criada (`tabela_existe = 1`) |
   | RPC `recall_l4` | criada (`rpc_existe = 1`) |
   | RLS | activa (`rls_activa = true`) |
   | `anon`/`authenticated` na tabela | 0 privilégios (`privilegios_anon = 0`) |
   | `anon` → `EXECUTE recall_l4` | sem permissão |
   | **Total** | **4/4** |

3. **Teste real mínimo (L4-1b, por fazer)**, com o `DATABASE_URL` do projecto: `remember` → `recall --candidates` → `promote` → `recall` → `forget` pela CLI acima, com um âmbito de teste (`project:teste-l4`).

## Limites

- **Sem auto-extracção:** só quando houver spike + flag (D3). O mem0 continua fora: o spike comparativo fica para depois.
- **Âmbitos sem identidade forte:** o runner é de confiança (usa o role `postgres`). As regras de âmbito estão no código e no CHECK, mas não em RLS por utilizador, que exigiria um modelo de identidade inexistente, como já está registado no `enable_rls_knowledge_tables.sql`.
- **O MCP de produção não usa a L4** (só o runner). Ligá-lo é um item à parte (ADR-M7).
- **Embeddings só com `GEMINI_API_KEY`.** Sem ela, as memórias gravam-se e o recall vai por recência.
