# Ciclo de vida de skills (Hermes learning loop → nosso gate)

## Estados

```text
candidate  →  reviewed  →  active  →  (patched)  →  stale  →  archived
```

| Estado | Onde | Quem promove |
|--------|------|----------------|
| candidate | `skills/_candidates/` ou `pilots/.../skill-draft.md` | Ninguém automático |
| reviewed | mesmo sítio + nota de review | Humano |
| active | `skills/claude/<name>/SKILL.md` | Humano após review |
| patched | diff pequeno sobre active | Humano (preferir patch) |
| stale / archived | pasta archive ou frontmatter | Curator humano ou job opcional |

## Critérios para *propor* candidate (inspirado Hermes)

Sugestão de triggers (não obrigatórios todos):

- ≥ N tool calls com sucesso final  
- Recuperação de erro não trivial  
- Procedimento não óbvio e reutilizável  
- Utilizador/operador pediu “guarda isto como skill”  

## Nunca

- Auto-merge para `skills/claude/` ou para `agent-network-mcp`  
- Skill que codifica bypass de human_gate ou paths de produção  
- Skill com secrets  

## Formato candidate mínimo

```markdown
---
name: exemplo
status: candidate
source_plan: pilots/...
created: ISO-8601
---
# Quando usar
...
# Passos
...
# done_when / verificação
...
```
