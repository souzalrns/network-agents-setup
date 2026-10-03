---
name: security-triage
action: security_triage
version: 1
role: security_technique
priority: P1
description: >
  Triagem defensiva de pedidos de segurança: severidade, superfícies e se a
  auditoria completa (security_audit) é necessária. Sem scanners e sem escrita.
requires: []
---

# Skill — security-triage

## Trigger

- Início de um plano na área `security`.
- Pedido ambíguo (“rever segurança”, “há risco neste PR?”).

## Regras curtas

1. Só classificar — não auditar em profundidade.
2. Não inventar CVEs nem findings.
3. Pedido ofensivo → `out_of_scope` inclui “ataque activo proibido”; não sugerir exploit.
4. Saída = **um único JSON** válido (sem markdown à volta).

## Output schema (obrigatório)

```json
{
  "severity": "critical|high|medium|low|info",
  "surfaces": ["code", "deps", "mcp", "ci", "secrets", "rag", "prompts", "infra"],
  "needs_full_audit": true,
  "rationale": "string curta",
  "out_of_scope": ["string"]
}
```

- `surfaces`: subset aplicável (array pode ser vazio só se o pedido for puramente conceptual).
- `needs_full_audit`: `true` se severity ≥ medium **ou** houver superfície code/deps/mcp/secrets/ci a verificar em repo.
- `out_of_scope`: o que explicitamente não será feito (ex.: “exploração activa”, “alterar produção”).

## Done when

- [ ] JSON válido com todas as chaves
- [ ] Nenhuma ferramenta de scan invocada
- [ ] Nenhuma acção ofensiva sugerida como passo executável por este agente
