# Design tokens — três níveis (obrigatório UI)

```text
Primitive (reference) → Semantic (system) → Component
```

| Nível | Exemplo | Quem usa |
|-------|---------|----------|
| Primitive | `blue-500`, `space-4` | só fundação do system |
| Semantic | `color.action.primary`, `bg.surface` | produto + themes |
| Component | `button.primary.bg` | implementação do controlo |

## Regras

1. Component **não** referencia primitive directamente.
2. Theme (light/dark) remapeia **semantic**, não cada componente.
3. Nomes estáveis > valores temporários no handoff.
4. Formato ideal de troca: DTCG (`$value`, `$type`, aliases `{path}`).

## Exemplo mínimo

```text
primitive.color.brand.600
  → semantic.color.action.primary
    → component.button.primary.background
```

## MCP (opcional)

Consulta read-only de tokens no IDE; no lab, este doc + `read_repo_file` bastam até existir MCP.
