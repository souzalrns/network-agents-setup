# Rubrica — creative review (genérico)

Usar na action `creative_review` / critic criativo.

## Dimensões (1–5)

1. **On-brief** — responde ao objective e audience  
2. **Clareza** — mensagem principal óbvia em menos de 5s  
3. **Canal-fit** — formato adequado ao canal  
4. **Brand** — tom/claims compatíveis com brand kit (se existir)  
5. **Risco** — claims verificáveis; sem ToS/legal óbvio  
6. **Item 13** (se conteúdo discoverable) — estrutura, entidades, citabilidade  

## Saída

```json
{
  "scores": {},
  "blockers": [],
  "suggestions": [],
  "publish_ready": false
}
```

`publish_ready` só true se blockers vazio e média ≥ 4 (ajustável por project).
