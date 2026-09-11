# Handoffs UX → UI → Dev

## UX → UI

| UX entrega | UI usa |
|------------|--------|
| Fluxo e decisões | Ordem de ecrãs |
| Elementos essenciais | Hierarquia e componentes |
| Edge states | Variantes e mensagens |
| Success criteria | Critérios de revisão |

UI **não** remove passos do fluxo sem registo no critic.

## UI → Dev

| UI entrega | Dev usa |
|------------|--------|
| Nomes de tokens | CSS vars / theme |
| Matriz de estados | Implementação |
| Variantes | Props do componente |
| Notas a11y | ARIA / foco |

Dev **não** deve receber só screenshots sem tokens.

## HITL

- Fluxos legais/financeiros/saúde: humano antes de implementar.
- Pack lab interno: HITL no fim do template `design-flow`.
