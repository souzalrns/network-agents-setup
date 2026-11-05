# Templates de plan — marketing

YAML de referência para o orquestrador da vertical.

| Template | Uso |
|----------|-----|
| [seo-article.plan.yaml](./seo-article.plan.yaml) | Artigo / peça SEO + Item 13 via brief/critic |
| [social-pack.plan.yaml](./social-pack.plan.yaml) | Pack social multi-canal |

### Templates de área (P-90 = B, M-006)

Um por área da agência: o líder da área decide e entrega o brief; os especialistas da área recebem-no como input; o `critic` revê e um humano aprova ([ESTRUTURA-AREAS.md](../ESTRUTURA-AREAS.md) §2).

| Template | Líder |
|----------|-------|
| [areas/estrategia.plan.yaml](./areas/estrategia.plan.yaml) | `marketing.lider_estrategia` |
| [areas/inteligencia.plan.yaml](./areas/inteligencia.plan.yaml) | `marketing.lider_inteligencia` |
| [areas/conteudo.plan.yaml](./areas/conteudo.plan.yaml) | `marketing.lider_conteudo` |
| [areas/video.plan.yaml](./areas/video.plan.yaml) | `marketing.lider_video` |
| [areas/social.plan.yaml](./areas/social.plan.yaml) | `marketing.lider_social` |
| [areas/site-seo.plan.yaml](./areas/site-seo.plan.yaml) | `marketing.lider_site_seo` |
| [areas/anuncios.plan.yaml](./areas/anuncios.plan.yaml) | `marketing.lider_anuncios` |
| [areas/crm.plan.yaml](./areas/crm.plan.yaml) | `marketing.lider_crm` |

Novos `deliverable_type`: copiar um template, ajustar steps/actions, registar em `ORCHESTRATOR.md` secção 4.

### Regras que o motor verifica (M-008)

Qualquer plano de marketing, deste diretório, de uma sessão ou do router, só arranca se cumprir
[`config/plan-policy.yaml`](../../../../config/plan-policy.yaml) (o cabeçalho explica cada regra):
`delivery: internal | external`, `budget.max_steps` declarado (até 40), um bloco `knowledge: {kb, query}`
em cada passo que não é aprovação, ferramentas que existem no motor, o líder antes dos especialistas nos
planos de área e, numa entrega `external`, a aprovação humana do `done_when` a depender directamente do
`critic` e do `compliance_check` (e do `critic_item13` em `seo_article` e `area_site_seo`). Um plano que
falhe não arranca e o erro diz qual regra falhou. Prova: `runner/tests/test_policy.py`.
