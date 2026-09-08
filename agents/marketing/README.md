# Agents marketing (P0)

Cada agent aponta para **uma action** e **uma skill**. O orchestrator despacha pelo `steps[].action`; o worker carrega o agent + skill.

| Agent file | action | skill |
|------------|--------|-------|
| [research.agent.md](./research.agent.md) | `research` | `skills/marketing/research/SKILL.md` |
| [seo_brief.agent.md](./seo_brief.agent.md) | `seo_brief` | `skills/marketing/seo_brief/SKILL.md` |
| [copy_answer_first.agent.md](./copy_answer_first.agent.md) | `copy_answer_first` | `skills/marketing/copy_answer_first/SKILL.md` |
| [critic_item13.agent.md](./critic_item13.agent.md) | `critic_item13` | `skills/marketing/critic_item13/SKILL.md` |
| [internal_brief.agent.md](./internal_brief.agent.md) | `internal_brief` | `skills/marketing/internal_brief/SKILL.md` |
| [creative_review.agent.md](./creative_review.agent.md) | `creative_review` | `skills/marketing/creative_review/SKILL.md` |

## Resolução automática

```text
steps[].action  →  agents/marketing/<action>.agent.md
                →  skill path no frontmatter
                →  skills/marketing/<action>/SKILL.md
```

O `plan_runner` em mode `external` grava no `request.json` os paths de agent + skill para o worker.
