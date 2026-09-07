# Identidade e binding

## Subject

Entidade canónica que possui scopes de memória e permissões.

```text
subject {
  id
  kind: user | service | agent_system
  org_id?
  status
}
```

## Channel identity

```text
channel_identity {
  platform
  external_id
  display_name?
  subject_id?     # null até bind
}
```

## Bind

- Explícito (login, código, admin).  
- Auditado em L2 ou log de segurança.  
- Unbind / revoke sem apagar L2 histórico.

## Agent identity

```text
agent_role {
  id              # seo_worker, orchestrator, …
  tools_allowed[]
  kb_allowlist[]
  model_tier?
}
```

O mesmo `agent_role` corre atrás de **qualquer** plataforma.
