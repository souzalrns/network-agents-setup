# Knowledge Pack — ui

Conhecimento operacional para o agente UI Specialist. Injetar junto com o system prompt e o contexto do cliente.

---

## 1. Arquitetura de tokens (3 camadas)

Padrão consolidado (W3C DTCG 2025.10 + prática de mercado):

| Camada | O que é | Exemplo | Quem muda |
|--------|---------|---------|----------|
| **Primitive** | Valor bruto, sem intenção | `color.blue.500 = #2563EB`, `space.4 = 16px` | Raramente |
| **Semantic** | Intenção / papel | `color.action`, `color.surface`, `color.text.muted` | Temas, dark mode, rebrand |
| **Component** | Uso específico | `button.primary.bg`, `card.padding` | Por componente |

### Regras

1. Componentes **referenciam só semantic** (nunca primitive direto).
2. Semantic **referencia primitive** (alias), não valores hardcoded.
3. Pular a camada semantic quebra temas e dark mode.
4. Nomes semantic descrevem **uso** (`action`, `danger`), não aparência (`blue`, `red`).
5. AI agents leem melhor a camada semantic do que hex ou `blue-500`.

### Checklist de tokens

- [ ] Formato DTCG (`$value`, `$type`, `$description`) quando houver export formal
- [ ] Três camadas presentes ou justificativa para não ter
- [ ] Contraste documentado onde relevante (texto 4.5:1, UI não-texto 3:1)
- [ ] Sem magic numbers em componentes
- [ ] Semantic não carrega valor cru — só referência

### Anti-padrões

| Erro | Por que falha |
|------|----------------|
| Componente usa `var(--blue-500)` | Quebra tema; não expressa intenção |
| Semantic com hex embutido | Não há alias; dark mode vira reescrita |
| Só primitives, sem semantic | Design system vira lista de cores |
| Tokens sem documentação de uso | IA e devs escolhem o token errado |

---

## 2. Pipeline design → código

```
Figma Variables / Tokens Studio
        ↓ (JSON DTCG)
Style Dictionary v4
        ↓
CSS custom properties / Tailwind / tokens de app
        ↓
Storybook (componentes documentados)
```

- **Figma**: fonte de verdade de design (Variables + Dev Mode).
- **Tokens Studio**: gestão de tokens, temas, sync Git.
- **Style Dictionary v4**: suporte nativo DTCG; gera artefatos multiplataforma.
- **Storybook**: catálogo vivo no código (variants, states, edge cases).

Não exigir stack completa em todo pedido. Calibrar ao tamanho do produto.

---

## 3. Estados de componente (obrigatórios a considerar)

Para componentes interativos, documentar no mínimo:

| Estado | Quando |
|--------|--------|
| Default | Repouso |
| Hover | Ponteiro sobre |
| Focus | Teclado / foco programático |
| Active / Pressed | Clique / toque |
| Disabled | Não interativo |
| Loading | Ação em curso |
| Error | Validação falhou |

Combinações críticas (ex.: input):
- Empty / Filled
- Focus + Empty / Focus + Filled
- Error + Empty / Error + Filled
- Disabled / Read-only / Loading

### Variants vs boolean props

- **Variants** (prop `variant` / `appearance`): primary, secondary, destructive, outline…
- **Boolean props**: `disabled`, `loading`, `hasError` — quando são flags independentes
- Evitar explosão combinatória: preferir nesting de instâncias (ex.: ícone) em vez de variant por cada ícone

Nomear por **propósito**, não por aparência (`primary` > `blue-big`).

---

## 4. Acessibilidade UI (checklist operacional)

### Contraste
- Texto normal: **≥ 4.5:1** (WCAG AA)
- Texto grande: ≥ 3:1
- Componentes UI / gráficos essenciais: **≥ 3:1** (non-text contrast)
- Nunca usar só cor para status (erro/sucesso) — ícone ou texto junto

### Foco (WCAG 2.2)
- Focus **visível** sempre
- Focus **não totalmente obscurecido** por sticky header, cookie banner, chat (2.4.11 AA)
- Indicador de foco com contraste suficiente face ao estado não-focado

### Alvos e espaçamento
- Target size mínimo: **24×24 CSS px** (2.5.8 AA) ou alternativa acessível
- Text spacing: página não quebra se usuário aumentar line-height / letter-spacing

### Nome, role, value
- Todo controle interativo: nome acessível, role correto, estado programático (disabled, expanded, checked)
- Preferir HTML semântico; ARIA só quando necessário

### Outros
- Conteúdo em hover/focus: dismissível, hoverable, persistente até dismiss
- Help mechanisms em posição consistente entre páginas (3.2.6)

---

## 5. Princípios de decisão rápida

1. **Tokens semânticos antes de valores hardcoded.**
2. **Consistência antes de variedade.**
3. **Clareza antes de decoração.**
4. **Acessibilidade como requisito, não extra.**
5. **Calibrar profundidade:** landing de campanha ≠ app com design system formal.
6. **Não inventar tokens ou valores de marca** — pedir brand kit / tokens existentes.
7. **Não gerar peças finais** (Canva / export visual) — orientar especificação.

---

## 6. Formato de resposta preferido

Quando analisar ou propor UI:

1. Premissas (o que foi assumido por falta de dado)
2. Tokens / camadas relevantes (se aplicável)
3. Componentes e estados cobertos
4. Riscos de a11y
5. Recomendações priorizadas (o que fazer primeiro)

Nunca inventar métricas, hex de marca ou “design system já existente” sem evidência no contexto do cliente.
