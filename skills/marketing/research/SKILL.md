---
name: research
action: research
version: 1
vertical: marketing
priority: P0
---

# Skill — research

## Quando usar

- Step `action: research` em qualquer template de marketing.
- Precisas de factos, ângulos, fontes ou contexto antes de brief/SEO/copy.

## Não usar

- Para escrever a peça final (isso é `copy_*` / `storytelling`).
- Para scores de ads ou spend (isso é `performance_analyst` / `media_buyer`).

## Inputs

- `objective` do plan
- `audience` se existir
- `knowledge_refs` / brand kit se existirem
- Artefactos listados em `inputs` do step

## Tools permitidas

Só as de `tools_allowed` no step (tipicamente `read_repo_file`, `web_search`). Não inventar tools.

## Processo

1. Ler objective e audience.
2. Listar 3–7 perguntas que a peça precisa responder.
3. Recolher factos verificáveis; marcar cada um com fonte (URL, doc interno, ou "assumption").
4. Separar **factos** de **hipóteses**.
5. Propor 2–4 ângulos de mensagem; recomendar um.
6. Notar gaps (o que falta para copy/SEO seguro).

## Saída (`output_artifact`, tipicamente `artifacts/01-research.md`)

```markdown
# Research

## Objective
...

## Audience
...

## Key questions
-

## Facts (com fonte)
| Facto | Fonte |
|-------|-------|

## Assumptions
-

## Recommended angle
...

## Gaps
-
```

## done_when

- [ ] Pelo menos 3 factos ou assumptions explícitas
- [ ] Ângulo recomendado preenchido
- [ ] Gaps listados (mesmo que vazios: "none")
- [ ] Nenhuma claim de performance sem fonte

## Anti-padrões

- Prosa longa sem estrutura
- Copiar SERP sem citar
- Inventar estatísticas
- Misturar research com copy final
