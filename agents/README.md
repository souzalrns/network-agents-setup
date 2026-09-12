# Agents

Definições de agent (identidade + skill + action).

| Vertical | Path |
|----------|------|
| **Marketing** P0/P1 | [marketing/](./marketing/) |
| **Design** P0 (UX + UI + writer + critic) | [design/](./design/) |
| **Shared** | [_shared/](./_shared/) — grounding obrigatório |
| Meta | [meta/](./meta/) se existir |

## Grounding

Todo agent novo deve respeitar [_shared/grounding.directive.md](./_shared/grounding.directive.md).

Integração com runner: mode `external` inclui `agent_path` e `skill_path` no `pending_steps/<id>/request.json`.
