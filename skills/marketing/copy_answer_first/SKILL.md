---
name: copy_answer_first
action: copy_answer_first
version: 1
vertical: marketing
priority: P0
---

# Skill — copy_answer_first

## Quando usar

- Step `action: copy_answer_first` após `seo_brief` (ou brief equivalente).

## Não usar

- Pack só social (→ `copy_social`) salvo o plan diga explicitamente esta action.
- Decisões de publish (→ HITL).

## Inputs

- `artifacts/...-seo-brief.json` (ou path em `inputs`)
- Research se disponível
- Brand kit / constraints do plan

## Tools

Só `tools_allowed` (em geral `read_repo_file`).

## Processo

1. Ler o brief; não contradizer primary intent nem unique promise.
2. **Resposta directa** nas primeiras linhas (answer-first).
3. Desenvolver outline do brief; cada H2 deve entregar valor.
4. Incorporar FAQs Item 13 como secções ou bloco FAQ claros.
5. Claims verificáveis; se assumption, dizer.
6. CTA só se o brief/objective pedirem; sem promessas ilegais.

## Saída

Markdown (tipicamente `artifacts/03-copy.md`):

```markdown
# {título alinhado ao H1}

{resposta directa em 2–5 frases}

## ...

## FAQ
### ...
```

Se `output_schema: CopyAnswerFirst`, incluir também campos estruturados exigidos pelo schema do repo.

## done_when

- [ ] Resposta útil antes do scroll longo
- [ ] Secções batem com outline do brief (ou desvios justificados)
- [ ] FAQ ou equivalente se o brief tinha item_13.faq
- [ ] Sem inventar dados numéricos sem fonte

## Anti-padrões

- Intro "No mundo de hoje..." sem resposta
- Ignorar o brief
- Keyword stuffing
- CTA agressivo não pedido
