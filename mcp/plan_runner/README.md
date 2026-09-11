# MCP — plan_runner (governado)

Expõe o lab `plan_runner` a clientes MCP (Cursor, Claude Desktop) via **stdio**.

## Tools

| Tool | Scope | Descrição |
|------|-------|-----------|
| `list_templates` | `runner:template:list` | Lista YAMLs em `docs/orchestration/**/templates` |
| `get_status` | `runner:plan:read` | Lê `status.json` de um run |
| `run_plan` | `runner:plan:execute` | `run` dry-run/stub/external |
| `resume_plan` | `runner:plan:resume` | Resume com decision |

## Segurança

- Perfis: `PLAN_RUNNER_MCP_PROFILE=permissive\|moderate\|strict` (default `moderate`)
- Key: `PLAN_RUNNER_MCP_KEY` (obrigatória para mutate em moderate/strict)
- Raiz do repo: `PLAN_RUNNER_REPO_ROOT` ou auto-detect (dois níveis acima de `mcp/plan_runner`)
- Audit: `mcp/plan_runner/audit/audit.jsonl`

## Cursor / Claude

```json
{
  "mcpServers": {
    "plan-runner": {
      "command": "python",
      "args": ["-m", "mcp_plan_runner"],
      "cwd": "C:/Users/YOU/Downloads/network-agents-setup/mcp/plan_runner",
      "env": {
        "PLAN_RUNNER_REPO_ROOT": "C:/Users/YOU/Downloads/network-agents-setup",
        "PLAN_RUNNER_MCP_PROFILE": "moderate",
        "PLAN_RUNNER_MCP_KEY": "sk_lab_change_me"
      }
    }
  }
}
```

## Run manual

```powershell
cd $env:USERPROFILE\Downloads\network-agents-setup
git pull
cd mcp\plan_runner
python -m pip install -r requirements.txt
$env:PLAN_RUNNER_REPO_ROOT = (Resolve-Path ..\..).Path
$env:PLAN_RUNNER_MCP_KEY = "sk_lab_change_me"
python -m mcp_plan_runner
```

Depende de `mcp` (SDK oficial) quando disponível; fallback JSON-RPC mínimo para list/call tools em smoke sem SDK completo.
