---
name: ux_flow
action: ux_flow
version: 1
vertical: design
priority: P0
---

# Skill — ux_flow

## Quando usar

- Step `action: ux_flow` após brief/research de produto (se existir).
- Precisas de jornada, ecrãs informacionais e critérios de uso **antes** da UI.

## Não usar

- Mockups, cores, tipografia final → `ui_spec`.
- Copy de marketing/SEO → vertical marketing.
- Implementação de código → coding agents.

## Inputs

- `objective`, `audience` do plan
- Constraints (plataforma, a11y legal, tempo)
- Research prévio se em `inputs`

## Tools

Só `tools_allowed` (tipicamente `read_repo_file`; `web_search` se benchmarks autorizados).

## Processo

1. Problema e contexto de uso (1–2 parágrafos).
2. Utilizador e limitações relevantes.
3. 3–7 jobs-to-be-done.
4. Fluxo principal numerado + decisões.
5. Estados: empty, loading, error, success, permission denied.
6. Tabela de ecrãs: objectivo, elementos essenciais, próximo passo (sem visual).
7. Riscos de UX (carga cognitiva, fricção, a11y funcional).
8. Success criteria testáveis.
9. Handoff → UI (preservar / UI decide / UI não deve).

Ler se disponível: `docs/knowledge/design/ux-principles.md`, `nielsen-heuristics.md`, `cognitive-load.md`.

## Saída (`artifacts/0N-ux-flow.md`)

```markdown
# UX flow — {objective}

## Problem
## User & context
## Jobs to be done
## Primary flow
## Edge states
## Screens (information only)
## Success criteria (UX)
## Open questions / assumptions
## Handoff → UI
```

## done_when

- [ ] Problema e utilizador preenchidos
- [ ] Fluxo principal com caminho feliz
- [ ] Estados de erro/vazio considerados
- [ ] Ecrãs sem especificação visual
- [ ] Handoff UI explícito
- [ ] Assumptions separadas

## Anti-padrões

- Wireframe que já é UI (cores, sombras)
- Só happy path
- Personas longas sem implicação no fluxo
- Inventar entrevistas reais
- Chamar o agent UI por iniciativa própria
