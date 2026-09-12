# MCP — plan_runner (governado)

Expõe o lab `plan_runner` via **stdio** (Cursor / Claude Desktop).

## Tools

| Tool | Scope |
|------|--------|
| `list_templates` | `runner:template:list` |
| `get_status` | `runner:plan:read` |
| `run_plan` | `runner:plan:execute` |
| `resume_plan` | `runner:plan:resume` |

## Perfis (`PLAN_RUNNER_MCP_PROFILE`)

| Profile | Mutate (`run`/`resume`) |
|---------|-------------------------|
| `permissive` | sempre |
| `moderate` (default) | sempre no lab; com key se definida |
| `strict` | só se `PLAN_RUNNER_MCP_KEY` estiver definida |

## Smoke **sem** pacote `mcp`

```powershell
cd $env:USERPROFILE\Downloads\network-agents-setup
git pull
$env:PLAN_RUNNER_REPO_ROOT = (Resolve-Path .).Path
cd mcp\plan_runner
python -m mcp_plan_runner.smoke
```

## Server MCP (com SDK)

```powershell
cd mcp\plan_runner
python -m pip install -r requirements.txt
$env:PLAN_RUNNER_REPO_ROOT = (Resolve-Path ..\..).Path
$env:PLAN_RUNNER_MCP_PROFILE = "moderate"
python -m mcp_plan_runner
```

## Cursor config

```json
{
  "mcpServers": {
    "plan-runner": {
      "command": "python",
      "args": ["-m", "mcp_plan_runner"],
      "cwd": "C:/Users/YOU/Downloads/network-agents-setup/mcp/plan_runner",
      "env": {
        "PLAN_RUNNER_REPO_ROOT": "C:/Users/YOU/Downloads/network-agents-setup",
        "PLAN_RUNNER_MCP_PROFILE": "moderate"
      }
    }
  }
}
```

Audit: `mcp/plan_runner/audit/audit.jsonl`
