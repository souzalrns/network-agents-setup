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
