---
name: research
action: research
version: 2
vertical: marketing
priority: P0
---

# Skill — research

## Quando usar

- Step `action: research` no início de pipelines de conteúdo/marketing.

## Não usar

- Escrever a peça final (`copy_*`)
- SEO brief completo (`seo_brief`)
- Inventar estatísticas ou licenças

## Grounding

Seguir `agents/_shared/grounding.directive.md`:

- Separar **Facts (com fonte)** de **Assumptions**
- Se não houver fonte no contexto / tools → gap explícito, **não** inventar

## Processo

1. Ler objective/audience do plan e inputs.
2. Listar perguntas-chave.
3. Factos só com fonte (tool, URL, artefacto, knowledge_ref).
4. Assumptions e gaps explicitados.
5. Ângulo recomendado (sem copy final).

## Saída

Markdown em `output_artifact` (ex. `artifacts/01-research.md`):

```markdown
# Research

## Objective
## Audience
## Key questions
## Facts (com fonte)
| Facto | Fonte |
## Assumptions
## Recommended angle
## Gaps
```

## done_when

- [ ] ≥1 facto com fonte **ou** gap justificado
- [ ] Assumptions separadas
- [ ] Sem números inventados
- [ ] Gaps listados se objective vazio

## Anti-padrões

- Estatísticas sem fonte
- Tratar hipótese como facto
- Completar licença/versão de memória de treino
