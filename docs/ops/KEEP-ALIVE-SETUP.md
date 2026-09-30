# Keep-alive do Supabase — setup (J1 / AU-47)

> **Estado: NÃO RESOLVIDO.** Fecha só quando o passo (d) der **1 run verde**. Tudo o que está abaixo é trabalho do **DEV** (precisa de credenciais que o Claude não tem).

## Porque falha hoje (5/5 runs)

O workflow `.github/workflows/keep-alive.yml` precisa de **duas condições**. Resolver só uma **não chega**:

1. **Secrets:** lê `secrets.SUPABASE_URL` e `secrets.SUPABASE_ANON_KEY` (`keep-alive.yml:21-22`). Se alguma estiver vazia, sai com `exit 1` (`:24-26`).
2. **Tabela:** faz `GET $SUPABASE_URL/rest/v1/keepalive?select=id&limit=1` com a chave anon (`:28-30`) e exige HTTP 200 (`:33-36`). A tabela `public.keepalive` **não existe** no projecto `mpsuurqilnhsvbnjmrpm`: `to_regclass('public.keepalive')` = `null`, verificado em 2026-09-30.

Corre por `schedule` (`cron: '0 6 */3 * *'`, de 3 em 3 dias às 06:00 UTC, `:9`) e por `workflow_dispatch` (`:10`). O ficheiro é igual na `main`.

## Passos para o DEV (por ordem)

### (a) Supabase — criar a tabela
1. Abrir o projecto **agent-network-memory** (`mpsuurqilnhsvbnjmrpm`) → **SQL Editor**.
2. Colar e correr o conteúdo de [`scripts/create_keepalive_table.sql`](../../scripts/create_keepalive_table.sql). É idempotente: pode correr-se mais de uma vez.
3. Confirmar: `select * from public.keepalive;` → 1 linha (`id = 1`).

O SQL foi testado num Postgres 16 local descartável: corre 2× sem erro, o `anon` lê a linha e o `anon` **não** consegue escrever.

### (b) GitHub — criar as 2 secrets
GitHub → repo **network-agents-setup** → **Settings → Secrets and variables → Actions → New repository secret**:

| Nome | Valor |
|---|---|
| `SUPABASE_URL` | `https://mpsuurqilnhsvbnjmrpm.supabase.co` |
| `SUPABASE_ANON_KEY` | A chave **anon** do mesmo projecto (Supabase → Project Settings → API Keys) |

**Que chave usar:** o workflow envia a chave nos headers `apikey` **e** `Authorization: Bearer` (`keep-alive.yml:30-31`).
- **Opção A** — chave anon *legacy* (JWT `eyJ…`). Custo: 0. Consequência: funciona nos dois headers.
- **Opção B** — chave *publishable* nova (`sb_publishable_…`). Custo: 0. Consequência: não é um JWT; como `Bearer` pode ser recusada (**NÃO VERIFICADO**).
- **Opção C** — `service_role`. Custo: 0. Consequência: dá acesso total a um workflow que só precisa de ler. **Não usar.**
- **RECOMENDADA: A**, porque é a única verificada como compatível com os dois headers que o workflow envia. Se não houver resposta em 7 dias, executa-se a A.

### (c) OBRIGATÓRIO — confirmar que é o MESMO projecto que o `agent-network-mcp` usa
O projecto Supabase é **partilhado**: o `agent-network-mcp` lê `process.env.SUPABASE_URL` (`agent-network-mcp/lib/memory.js:7`). Se o keep-alive pingar outro projecto, o de produção pode pausar enquanto o workflow aparece verde. **A divergência mascara o problema.**

1. Vercel → projecto do `agent-network-mcp` → **Settings → Environment Variables** → `SUPABASE_URL` tem de conter **`mpsuurqilnhsvbnjmrpm`**.
2. Se for chave *legacy*, o JWT da anon tem `"ref":"mpsuurqilnhsvbnjmrpm"` no payload (decodificar o 2.º segmento em base64, **localmente**, nunca num site externo).
3. Registar aqui a data e o resultado: `____-__-__ — mesmo projecto: SIM / NÃO`.

### (d) Correr o workflow à mão
GitHub → **Actions → keep-alive → Run workflow** (branch `main`). Esperado no log:
```
HTTP 200
keep-alive: Supabase respondeu (projeto ativo)
```
Registar aqui: `____-__-__ — run #___ — VERDE / VERMELHO`.

### (e) Se falhar
Colar o log abaixo e deixar o estado deste documento em **NÃO RESOLVIDO**.

| Mensagem no log | Causa provável |
|---|---|
| `SUPABASE_URL ou SUPABASE_ANON_KEY em falta` | Secret com nome errado ou vazia (b) |
| `HTTP 404` | Tabela não criada, ou criada fora de `public` (a) |
| `HTTP 401` / `HTTP 403` | Chave de outro projecto (c), chave *publishable* como Bearer (b), ou falta o `GRANT SELECT` (a) |

```
(colar aqui o log do run falhado)
```

## Porque é que o cron só conta na `main`
Os crons do GitHub Actions só correm no branch por omissão. O `keep-alive.yml` desta branch é igual ao da `main`, por isso não é preciso merge para o J1: basta (a), (b), (c) e (d).
