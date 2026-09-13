# Tools catalog — plan_runner MCP server

**Fonte:** `mcp/plan_runner/mcp_plan_runner/tools_impl.py`
**Formato:** Purpose / Parameters / Returns / Errors / Example (inspirado na documentação de tools MCP da Red Hat e na spec Anthropic MCP).

As 4 tools expostas pelo servidor. Cada uma tem um scope dedicado (`policy.py`) e passa pelo mesmo pipeline de governança (ver `governance-pipeline.md`).

---

## `list_templates`

**Purpose:** listar todos os planos `*.plan.yaml` disponíveis sob `docs/orchestration/`.

**Scope:** `runner:template:list`
**Mutating:** não

**Parameters:** nenhum.

**Returns:**
```json
{
  "ok": true,
  "templates": ["docs/orchestration/marketing/templates/seo-article.plan.yaml", "..."],
  "repo_root": "/caminho/para/network-agents-setup"
}
```

**Errors:** `{ "ok": false, "error": "<reason>" }` se `authorize` falhar.

**Example (JSON-RPC):**
```json
{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"list_templates","arguments":{}}}
```

---

## `get_status`

**Purpose:** ler o `status.json` de um run (por diretório ou ficheiro direto).

**Scope:** `runner:plan:read`
**Mutating:** não

**Parameters:**

| Nome | Tipo | Obrigatório | Nota |
|------|------|-------------|------|
| `out_dir` | string | sim | path relativo ao repo root, sanitizado por `sanitize_repo_path` |

**Returns:**
```json
{
  "ok": true,
  "status": {
    "run_id": "run_...",
    "plan_id": "template-seo-article",
    "mode": "stub",
    "state": "done",
    "completed": ["copy","critic","hitl_publish_decision","research","seo_brief"],
    "current_step": null
  }
}
```

**Errors:**
- path fora do repo root → `PermissionError` (mensagem: `path outside repo root`)
- `status.json` inexistente → `FileNotFoundError`

**Example:**
```json
{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"get_status","arguments":{"out_dir":"pilots/run-seo-stub"}}}
```

---

## `run_plan`

**Purpose:** executar um plano em modo `dry-run`, `stub` ou `external`, opcionalmente gravando output num diretório.

**Scope:** `runner:plan:execute`
**Mutating:** sim

**Parameters:**

| Nome | Tipo | Obrigatório | Valores |
|------|------|-------------|---------|
| `plan` | string | sim | path relativo ao repo root |
| `mode` | string | não (default `stub`) | `dry-run` \| `stub` \| `external` |
| `out` | string | não | path relativo; criado se não existir |

**Returns:** `{ "ok": true, "result": <resultado do engine> }`

**Errors:**
- `mode` inválido → `{ "ok": false, "error": "mode must be dry-run|stub|external" }`
- auth falhada → `{ "ok": false, "error": "<reason>" }`
- path fora do repo → `PermissionError` propagado como `{ "ok": false, "error": "..." }`

**Example:**
```json
{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"run_plan","arguments":{"plan":"docs/orchestration/marketing/templates/seo-article.plan.yaml","mode":"stub","out":"pilots/run-mcp-smoke"}}}
```

---

## `resume_plan`

**Purpose:** retomar um run que ficou em `paused_at_step` após HITL, aplicando uma decisão.

**Scope:** `runner:plan:resume`
**Mutating:** sim

**Parameters:**

| Nome | Tipo | Obrigatório | Valores |
|------|------|-------------|---------|
| `out_dir` | string | sim | path do run (sanitizado) |
| `decision` | string | não (default `approve`) | `approve` \| `reject` |

**Returns:** `{ "ok": true, "result": <resultado do engine> }`

**Errors:** auth falhada, path fora do repo, run inexistente.

**Example:**
```json
{"jsonrpc":"2.0","id":4,"method":"tools/call","params":{"name":"resume_plan","arguments":{"out_dir":"pilots/run-seo-stub","decision":"approve"}}}
```

---

## Resumo

| Tool | Scope | Mutating |
|------|-------|----------|
| `list_templates` | `runner:template:list` | não |
| `get_status` | `runner:plan:read` | não |
| `run_plan` | `runner:plan:execute` | sim |
| `resume_plan` | `runner:plan:resume` | sim |

Refs: `tools_impl.py`, `policy.py`, `auth-and-scopes.md`, `governance-pipeline.md`.