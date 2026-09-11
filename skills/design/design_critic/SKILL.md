---
name: design_critic
action: design_critic
version: 1
vertical: design
priority: P0
---

# Skill — design_critic

## Quando usar

- Após `ui_spec` (e idealmente `ux_flow`) antes de HITL.

## Processo

1. Verificar alinhamento UX ↔ UI.
2. Tokens: há salto primitive→component ilegítimo?
3. Estados cobertos vs edge states UX.
4. A11y mínima.
5. Scores 1–5 e blockers.

Dimensões:

1. flow_alignment
2. information_clarity
3. token_discipline
4. component_states
5. a11y
6. risk (claims, legal UI)

## Saída JSON

```json
{
  "publish_ready": false,
  "scores": {},
  "blockers": [],
  "suggestions": [],
  "summary": ""
}
```

`publish_ready` true só se blockers vazio e média ≥ 4.

## Anti-padrões

- Aprovar com blockers
- Reescrever o pack inteiro sem scores
- Confundir com critic de marketing/Item 13
