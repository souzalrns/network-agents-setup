---
name: internal_brief
action: internal_brief
version: 1
vertical: marketing
priority: P0
---

# Skill — internal_brief

## Quando usar

- Step `action: internal_brief` (template `internal_brief`).
- Handoff para criação (copy, design, social) **dentro** da equipa/agents.

## Não usar

- Proposta comercial ao cliente (fora do MVP cognitivo; HITL humano).
- Pedir ou listar passwords / tokens de ad accounts.

## Inputs

- Context/research do step anterior
- Objective, audience, channels, constraints

## Processo

1. Objectivo em uma frase.
2. Audience e job-to-be-done.
3. Mensagem principal + provas (ou "a obter").
4. Deliverables concretos (formatos, canais).
5. Tom e o que evitar.
6. Critérios de aceite (incluindo Item 13 se a peça for pública/discoverable).
7. Prazo/prioridade só se vierem no plan (senão omitir).

## Saída (`artifacts/02-internal-brief.md`)

```markdown
# Internal brief

## Objective
## Audience
## Core message
## Deliverables
## Tone / avoid
## Acceptance criteria
## Open questions
```

## done_when

- [ ] Objective + deliverables claros
- [ ] Acceptance criteria testáveis
- [ ] Zero pedidos de credenciais

## Anti-padrões

- Brief vago ("conteúdo engajador")
- Scope infinito sem critérios de aceite
