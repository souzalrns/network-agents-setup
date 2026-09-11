# Matriz de estados — componentes

Todo controlo interactivo no `ui_spec` deve considerar:

| Estado | Obrigatório? |
|--------|----------------|
| default | sim |
| hover | desktop sim |
| focus / focus-visible | sim (a11y) |
| active / pressed | recomendado |
| disabled | se pode bloquear |
| loading | se async |
| error | inputs / submit |
| success | feedback de conclusão |

## Padrão de documentação

```text
Component: Button
Variants: primary | secondary | ghost | danger
States: default, hover, focus, disabled, loading
Tokens: component.button.*.bg → semantic.color.*
```

## Ligação ao UX

Os edge states do `ux_flow` (empty, error, permission) devem mapear para UI concreta — não ficar só no markdown de fluxo.
