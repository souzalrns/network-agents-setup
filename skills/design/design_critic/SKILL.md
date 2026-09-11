---
name: design_critic
action: design_critic
version: 2
vertical: design
priority: P0
---

# Skill — design_critic

## Quando usar

- Após `ui_spec` e, se existir no plan, após `ux_writing`, antes de HITL.

## Processo

1. Alinhamento UX ↔ UI ↔ microcopy.
2. Tokens: salto primitive→component ilegítimo?
3. Estados cobertos vs edge states UX.
4. UX writing: checklist pre-ship (erros com how, empty com CTA, sem culpa).
5. A11y mínima.
6. Scores 1–5 e blockers.

Dimensões:

1. flow_alignment
2. information_clarity
3. token_discipline
4. component_states
5. a11y
6. ux_writing_quality
7. risk

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
- Ignorar `03-ux-writing.md` quando o plan o inclui
- Confundir com critic de marketing / AI Findability
