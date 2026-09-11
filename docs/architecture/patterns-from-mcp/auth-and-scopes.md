# MCP auth & scopes (lab → prod)

## Transport

| Mode | Auth |
|------|------|
| stdio | env / process trust; API key opcional `PLAN_RUNNER_MCP_KEY` |
| HTTP remoto | OAuth 2.1 resource server (fase 2) |

## Scope model

```text
runner:plan:read
runner:plan:execute
runner:plan:resume
runner:template:list
```

Mutations (`execute`, `resume`) em perfil `strict` exigem key válida.

## Pipeline (ordem)

1. Path allowlist / sanitize
2. Auth (key se perfil ≥ moderate e tool mutante)
3. Rate limit simples in-process
4. Scope check
5. Executar tool
6. Audit log

## HTTP futuro (não implementado)

- PRM `/.well-known/oauth-protected-resource`
- 401 + WWW-Authenticate
- AS externo (Supabase Auth / WorkOS / Cognito)
- Token Bearer em cada request
