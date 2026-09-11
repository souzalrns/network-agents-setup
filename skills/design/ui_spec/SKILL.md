---
name: ui_spec
action: ui_spec
version: 1
vertical: design
priority: P0
---

# Skill — ui_spec

## Quando usar

- Step `action: ui_spec` **depois** de `ux_flow` (ou equivalente).

## Não usar

- Redefinir jornada sem passar pelo UX.
- Gerar código de produção completo (podes esboçar tokens CSS como anexo).

## Inputs

- Artefacto UX em `inputs`
- Brand kit / constraints se existirem
- Knowledge tokens se `read_repo_file`

## Processo

1. Ler UX flow; listar desvios justificados se houver.
2. Hierarquia visual por ecrã (sem contradizer objectivos UX).
3. **Tokens 3-tier** (ver `docs/knowledge/design/tokens-three-tier.md`):
   - primitive só se fundar system
   - semantic obrigatório para intenção
   - component para controlos chave
4. Componentes: nome, variantes, **matriz de estados** (`component-states.md`).
5. A11y baseline (`a11y-baseline.md`).
6. Anti-padrões DS (`design-system-anti-patterns.md`).
7. Handoff dev: nomes de tokens estáveis, não "azul bonito".

## Saída (`artifacts/0N-ui-spec.md`)

```markdown
# UI spec — {objective}

## Source UX
(ref ao fluxo)

## Visual hierarchy (by screen)

## Tokens
### Semantic (required)
### Component (key controls)
### Primitive (only if founding)

## Components
| Component | Variants | States covered |

## Accessibility notes

## Open questions / assumptions

## Handoff → engineering
```

## done_when

- [ ] UX respeitado ou desvios justificados
- [ ] Semantic tokens nomeados
- [ ] ≥1 componente com estados além de default
- [ ] Notas a11y
- [ ] Handoff engineering preenchido

## Anti-padrões

- Hex soltos no componente sem token
- Só estado default
- Ignorar empty/error do UX
- Keyword visual stuffing / AI slop genérico
