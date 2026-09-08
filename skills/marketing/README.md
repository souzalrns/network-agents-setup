# Skills marketing — P0

Skills alinhadas às **actions** dos templates que o `plan_runner` já percorreu em stub.

| Pasta | action | Templates |
|-------|--------|-----------|
| [research](./research/SKILL.md) | `research` | seo_article, social_pack, internal_brief |
| [seo_brief](./seo_brief/SKILL.md) | `seo_brief` | seo_article |
| [copy_answer_first](./copy_answer_first/SKILL.md) | `copy_answer_first` | seo_article, approval revise |
| [critic_item13](./critic_item13/SKILL.md) | `critic_item13` | seo_article |
| [internal_brief](./internal_brief/SKILL.md) | `internal_brief` | internal_brief |
| [creative_review](./creative_review/SKILL.md) | `creative_review` | approval_rounds |

## Uso com o runner

- **stub:** não carrega estas skills (placeholders).
- **external / worker real:** o executor deve ler `skills/marketing/<action>/SKILL.md` quando `steps[].action` corresponder.

## P1 (ainda não neste pacote)

`trend_hunter`, `copy_social`, `storytelling`, `media_buyer`, `performance_analyst`, `ugc`, `influencer`, `editor_video`, `seo_tech_audit`, `status_report`, …

## Checklist

Marca ING C2.1–C2.4 / B2.2–B2.3 no `docs/checklists/ITEM13-MARKETING-ROADMAP.md` quando validares com um worker real (não só stub).
