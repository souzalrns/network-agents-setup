---
name: ux_writing
action: ux_writing
version: 1
vertical: design
priority: P0
---

# Skill — ux_writing

## Quando usar

- Step `action: ux_writing` após `ux_flow` e idealmente após ou em paralelo conceptual com `ui_spec`.
- Labels, CTAs, erros, empty/loading, tooltips, onboarding in-app.

## Não usar

- Artigos SEO, ads, social posts → marketing.
- Decidir layout/cores → `ui_spec`.
- Inventar novos passos de jornada → `ux_flow`.

## Inputs

- `artifacts/...-ux-flow.md` e/ou `...-ui-spec.md`
- Brand voice se existir (senão: defaults da knowledge pack)

## Tools

Só `tools_allowed` (tipicamente `read_repo_file`).

## Voice & tone (default)

**Clear, concise, useful, human, honest.**

| Fazer | Evitar |
|-------|--------|
| Sentence case | ALL CAPS de ênfase |
| Acção no botão ("Guardar") | "Clique aqui" / "Submeter" vago |
| Erro sem culpa | "Você errou" / jargão técnico cru |
| Label permanente no campo | Placeholder como único label |
| Instruções por significado | "Botão verde à direita" só por cor/direcção |

## Erros — fórmula what → why → how

1. **What** — o que falhou (simples).
2. **Why** — só se ajudar (opcional, curto).
3. **How** — o que fazer a seguir.

## Processo

1. Ler fluxos/ecrãs nos inputs; listar strings necessárias por ecrã/estado.
2. Escrever copy primária (recomendação).
3. Opcional: 1–2 alternativas + razão.
4. Checklist pre-ship (abaixo).
5. Gaps (tom de marca desconhecido, legal, etc.).

Ler: `docs/knowledge/design/ux-writing-principles.md`, `ux-writing-examples.md`.

## Saída (`artifacts/0N-ux-writing.md`)

```markdown
# UX writing — {objective}

## Voice notes
(assumptions se não houver brand kit)

## By screen / state
### {Screen}
| Element | Primary copy | Alt (optional) |
|---------|--------------|----------------|
| title | | |
| primary_cta | | |
| empty | | |
| error | | |

## Error catalog
| Code/context | What | Why | How |

## Pre-ship checklist
- [ ] ...

## Gaps
```

## done_when (pre-ship checklist)

- [ ] Toda acção primária tem label de verbo claro
- [ ] Empty states com próximo passo
- [ ] Erros com how-to-fix (não só "Error")
- [ ] Sentence case; sem culpa ao utilizador
- [ ] Sem instrução só por cor ou só por direcção
- [ ] Labels não dependem só de placeholder
- [ ] Alinhado aos estados do UX flow
- [ ] Sem Lorem Ipsum
- [ ] Sem copy de marketing/SEO enfiada na UI
- [ ] Gaps listados

## Anti-padrões

- Tom de anúncio ("Descubra já!") em erros de sistema
- Passive voice excessiva ("As definições podem ser alteradas")
- "We/Our" corporativo em cada frase
- Humor forçado em falhas críticas (pagamentos, legal, saúde)
