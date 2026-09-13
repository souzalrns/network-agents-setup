# Patterns from MCP governance / auth projects

**Nota:** `pontifex-mcp` (chris-dare) **não** foi encontrado como pacote público verificável no momento da ingestão. Ingerimos **padrões**, não dependência fantasma.

## Fontes de padrão

| Ideia | Origem conceptual |
|-------|-------------------|
| Scopes `namespace:resource:action` | governação tipo Pontifex |
| Pipeline I/O → auth → rate → sanitize → validate | chassis MCP |
| PRM + 401 + OAuth 2.1 PKCE | spec MCP + exemplos Cognito |
| Auto low-risk / human high-risk | CI/CD governado |
| stdio lab / HTTP produção | spec MCP transport |

## O que implementámos neste repo

Ver `mcp/plan_runner/`:

- Tools: `run_plan`, `resume_plan`, `get_status`, `list_templates`
- Scopes + perfis `permissive` / `moderate` / `strict`
- Audit JSONL por chamada
- Path sanitize (anti traversal)
- stdio only (HTTP+OAuth = fase futura documentada)

---

## Ficheiros deste pacote

| Ficheiro | Conteúdo |
|----------|----------|
| `README.md` | Este índice: fontes de padrão + o que implementámos |
| `auth-and-scopes.md` | Transport, scope model, pipeline em 6 passos, HTTP futuro |
| `tools-catalog.md` | As 4 tools: purpose, scope, params, returns, errors, exemplo |
| `governance-pipeline.md` | Os 6 passos do pipeline com código real + mini-ADRs |

**Framework de referência:** arc42 (secções 3, 5, 6, 9) para estrutura; modelo Nygard para ADRs.
Ctrl+S. Depois corre a verificação:

powershell
cd C:\Users\souza\Downloads\network-agents-setup

Get-ChildItem docs\architecture\patterns-from-mcp -File | Select-Object Name,Length

Write-Host ""
Write-Host "tools (esperado 4):" -ForegroundColor Cyan
(Select-String -Path docs\architecture\patterns-from-mcp\tools-catalog.md -Pattern '^## `').Count

Write-Host "steps (esperado 6):" -ForegroundColor Cyan
(Select-String -Path docs\architecture\patterns-from-mcp\governance-pipeline.md -Pattern '^## Step ').Count

Write-Host "README seccao (esperado 1):" -ForegroundColor Cyan
(Select-String -Path docs\architecture\patterns-from-mcp\README.md -Pattern 'Ficheiros deste pacote').Count

Write-Host ""
git status --short