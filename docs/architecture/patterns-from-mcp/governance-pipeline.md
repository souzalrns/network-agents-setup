# Governance pipeline (lab → prod)

**Fonte:** `mcp/plan_runner/mcp_plan_runner/policy.py` + `tools_impl.py`

Este documento expande a lista de 6 passos em `auth-and-scopes.md` com o código real. Cada passo tem uma mini-ADR (Context / Decision / Consequences), no espírito do arc42 secção 9 (Architecture Decisions) e do modelo Nygard (ADR).

Ordem canónica: **sanitize → auth → rate → scope → execute → audit**.

---

## Step 1 — Sanitize (anti-traversal)

**Context:** o MCP client pode enviar qualquer `out_dir` ou `plan`. Sem validação, um cliente malicioso (ou um bug) poderia ler/escrever fora do repo.

**Decision:** `sanitize_repo_path(user_path, must_exist=False)` resolve o path e verifica que está dentro de `repo_root()`. Fora → `PermissionError("path outside repo root: <path>")`.

**Consequences:**
- (+) Todas as tools ficam limitadas ao repo do lab
- (+) `must_exist=True` dá erro explícito antes de tentar ler
- (−) O cliente não pode usar paths absolutos fora do repo (intencional)

---

## Step 2 — Auth (fail-closed)

**Context:** o servidor corre por stdio, sem OAuth. Mas há tools que mutam estado (`run_plan`, `resume_plan`).

**Decision:** `authorize(tool)` devolve um `AuthContext`. Se a tool não existe em `SCOPES`, devolve `authorized=False` com `reason="unknown_tool"`. Perfis:

- `permissive` → tudo autorizado
- `moderate` (default) → reads sempre; mutate se `PLAN_RUNNER_MCP_KEY` estiver definida, ou `PLAN_RUNNER_MCP_ALLOW_MUTATE=1`, ou (lab default) com `reason="moderate_lab_open"`
- `strict` → mutate **só** com `PLAN_RUNNER_MCP_KEY` não-vazia; senão `authorized=False`

**Consequences:**
- (+) Fail-closed: tool desconhecida nunca passa
- (+) `strict` é o perfil "produção segura"
- (−) `moderate` permite mutate no lab sem key (documentado como `moderate_lab_open`)

---

## Step 3 — Rate limit

**Context:** chamadas repetidas (acidentais ou maliciosas) podem saturar o engine.

**Decision:** `rate_limit(caller, limit=60, window=60.0)` — 60 chamadas por 60 segundos, por `caller` (default `mcp-client`, override com `PLAN_RUNNER_MCP_CALLER`). Estrutura `dict[str, list[float]]` protegida por `threading.Lock`.

**Consequences:**
- (+) Protege contra loops no cliente
- (+) In-process: não precisa de Redis nem infra externa
- (−) Se o servidor reiniciar, o bucket reseta (aceitável para stdio lab)

---

## Step 4 — Scope check

**Context:** cada tool tem um scope `namespace:resource:action`. É preciso garantir que o scope corresponde à ação.

**Decision:** mapa fixo `SCOPES` em `policy.py`:

| Tool | Scope |
|------|-------|
| `list_templates` | `runner:template:list` |
| `get_status` | `runner:plan:read` |
| `run_plan` | `runner:plan:execute` |
| `resume_plan` | `runner:plan:resume` |

Mutating = `{run_plan, resume_plan}`. Scope check está implícito em `authorize` (a tool tem de estar em `SCOPES`).

**Consequences:**
- (+) Um único sítio para auditar scopes
- (+) Preparado para OAuth 2.1 futuro (HTTP) — o scope passa a vir do token
- (−) Hoje o scope não é verificado contra um token real (só perfis)

---

## Step 5 — Execute

**Context:** as tools chamam o engine Python (`plan_runner.engine.run_plan`, `resume_run`). O engine vive em `runner/`, fora do pacote MCP.

**Decision:** `_ensure_runner_on_path()` insere `repo_root/runner` no `sys.path` antes de importar. Assim o MCP server pode correr de qualquer cwd, desde que `PLAN_RUNNER_REPO_ROOT` esteja correto (ou o fallback encontre `runner/plan_runner/` + `docs/`).

**Consequences:**
- (+) Desacoplamento: MCP server não reimplementa o engine
- (+) Mesmo código testado em `runner/` (72 testes) é usado via MCP
- (−) Import dinâmico dentro da função (menos óbvio para tooling estático)

---

## Step 6 — Audit

**Context:** precisamos de rasto de quem chamou o quê, quando, com que resultado — para diagnóstico e para provar que a governança corre.

**Decision:** `audit(event)` acrescenta uma linha JSON a `mcp/plan_runner/audit/audit.jsonl`, com `ts` (epoch). `ensure_ascii=False` preserva acentos. Append-only — nunca se reescreve nem trunca.

**Consequences:**
- (+) Prova auditável: cada chamada a `run_plan`/`resume_plan` deixa rasto
- (+) Formato JSONL: fácil de processar com `jq`/Python, sem dependência
- (−) Sem rotação (lab OK; produção precisará de rotação/expurgo)

---

## Resumo visual

```
MCP client (stdio)
    │
    ▼
[tool chamada]
    │
    ├── sanitize_repo_path  (rejeita paths fora do repo)
    ├── authorize           (fail-closed, perfis)
    ├── rate_limit          (60/60s por caller)
    ├── scope check         (SCOPES map)
    ├── execute             (plan_runner.engine)
    └── audit               (audit.jsonl append)
    │
    ▼
{ok: true, result: ...}
```

Refs: `policy.py`, `tools_impl.py`, `auth-and-scopes.md`, `tools-catalog.md`.