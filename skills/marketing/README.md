# Skills marketing

## P0

| Pasta | action |
|-------|--------|
| [research](./research/SKILL.md) | research |
| [seo_brief](./seo_brief/SKILL.md) | seo_brief |
| [copy_answer_first](./copy_answer_first/SKILL.md) | copy_answer_first |
| [critic_item13](./critic_item13/SKILL.md) | critic_item13 |
| [internal_brief](./internal_brief/SKILL.md) | internal_brief |
| [creative_review](./creative_review/SKILL.md) | creative_review |

## P1 (social_pack e adjacentes)

| Pasta | action |
|-------|--------|
| [trend_hunter](./trend_hunter/SKILL.md) | trend_hunter |
| [copy_social](./copy_social/SKILL.md) | copy_social |
| [storytelling](./storytelling/SKILL.md) | storytelling |
| [critic](./critic/SKILL.md) | critic |
| [transcript_analysis](./transcript_analysis/SKILL.md) | transcript_analysis |

Ainda em falta (P1+): media_buyer, performance_analyst, ugc, influencer, editor_video, seo_tech_audit, status_report.

## P2 (incorporadas de marketingskills, 2026-10-12)

39 skills de [coreyhaines31/marketingskills](https://github.com/coreyhaines31/marketingskills) (MIT) que o runner
ainda não tinha: 28 como skill própria (tabela abaixo) e 11 como modos de um herdeiro (M-006, tabela seguinte). Geradas por `scripts/vendor_marketingskills.py` (não editar à mão): contrato do runner em PT +
conhecimento upstream (inglês), sem parceiros pagos nem chamadas a APIs. Capabilities em `status: partial`
(ligadas; `implemented` só com um plano que as use). Ver `docs/ops/MARKETING-SKILLS.md`.

| Pasta | action | upstream |
|-------|--------|----------|
| [ab_testing](./ab_testing/SKILL.md) | ab_testing | `ab-testing` |
| [analytics](./analytics/SKILL.md) | analytics | `analytics` |
| [aso](./aso/SKILL.md) | aso | `aso` |
| [attribution](./attribution/SKILL.md) | attribution | `attribution` |
| [churn_prevention](./churn_prevention/SKILL.md) | churn_prevention | `churn-prevention` |
| [cold_email](./cold_email/SKILL.md) | cold_email | `cold-email` |
| [community_marketing](./community_marketing/SKILL.md) | community_marketing | `community-marketing` |
| [competitor_profiling](./competitor_profiling/SKILL.md) | competitor_profiling | `competitor-profiling` |
| [cro](./cro/SKILL.md) | cro | `cro` |
| [directory_submissions](./directory_submissions/SKILL.md) | directory_submissions | `directory-submissions` |
| [emails](./emails/SKILL.md) | emails | `emails` |
| [image](./image/SKILL.md) | image | `image` |
| [lead_magnets](./lead_magnets/SKILL.md) | lead_magnets | `lead-magnets` |
| [marketing_plan](./marketing_plan/SKILL.md) | marketing_plan | `marketing-plan` |
| [marketing_psychology](./marketing_psychology/SKILL.md) | marketing_psychology | `marketing-psychology` |
| [offers](./offers/SKILL.md) | offers | `offers` |
| [onboarding](./onboarding/SKILL.md) | onboarding | `onboarding` |
| [paywalls](./paywalls/SKILL.md) | paywalls | `paywalls` |
| [product_marketing](./product_marketing/SKILL.md) | product_marketing | `product-marketing` |
| [programmatic_seo](./programmatic_seo/SKILL.md) | programmatic_seo | `programmatic-seo` |
| [prospecting](./prospecting/SKILL.md) | prospecting | `prospecting` |
| [public_relations](./public_relations/SKILL.md) | public_relations | `public-relations` |
| [referrals](./referrals/SKILL.md) | referrals | `referrals` |
| [sales_enablement](./sales_enablement/SKILL.md) | sales_enablement | `sales-enablement` |
| [schema](./schema/SKILL.md) | schema | `schema` |
| [signup](./signup/SKILL.md) | signup | `signup` |
| [site_architecture](./site_architecture/SKILL.md) | site_architecture | `site-architecture` |
| [sms](./sms/SKILL.md) | sms | `sms` |

### Modos de herdeiros (M-006, P-89 = A)

A função de 11 agentes fundidos vive como `modes/<modo>.md` da skill do herdeiro e só entra no passo com
`mode: <modo>` ([ESTRUTURA-AREAS.md](../../docs/orchestration/marketing/ESTRUTURA-AREAS.md) §4).

| Modo | Passo do plano | upstream | Substitui |
|------|----------------|----------|-----------|
| [referrals/modes/co_marketing](./referrals/modes/co_marketing.md) | `referrals` + `mode: co_marketing` | `co-marketing` | `marketing.co_marketing` |
| [seo_brief/modes/competitors](./seo_brief/modes/competitors.md) | `seo_brief` + `mode: competitors` | `competitors` | `marketing.competitors` |
| [community_marketing/modes/events](./community_marketing/modes/events.md) | `community_marketing` + `mode: events` | `events` | `marketing.events` |
| [lead_magnets/modes/free_tools](./lead_magnets/modes/free_tools.md) | `lead_magnets` + `mode: free_tools` | `free-tools` | `marketing.free_tools` |
| [marketing_plan/modes/launch](./marketing_plan/modes/launch.md) | `marketing_plan` + `mode: launch` | `launch` | `marketing.launch` |
| [marketing_plan/modes/council](./marketing_plan/modes/council.md) | `marketing_plan` + `mode: council` | `marketing-council` | `marketing.marketing_council` |
| [marketing_plan/modes/ideas](./marketing_plan/modes/ideas.md) | `marketing_plan` + `mode: ideas` | `marketing-ideas` | `marketing.marketing_ideas` |
| [marketing_plan/modes/loops](./marketing_plan/modes/loops.md) | `marketing_plan` + `mode: loops` | `marketing-loops` | `marketing.marketing_loops` |
| [cro/modes/popups](./cro/modes/popups.md) | `cro` + `mode: popups` | `popups` | `marketing.popups` |
| [offers/modes/pricing](./offers/modes/pricing.md) | `offers` + `mode: pricing` | `pricing` | `marketing.pricing` |
| [lead_qualification/modes/revops](./lead_qualification/modes/revops.md) | `lead_qualification` + `mode: revops` | `revops` | `marketing.revops` |

## Runner

`external` resolve `skills/marketing/<action>/SKILL.md` e `agents/marketing/<action>.agent.md`.
