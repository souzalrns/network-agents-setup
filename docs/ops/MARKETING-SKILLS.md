# Skills de marketing (coreyhaines31/marketingskills)

> Pedido do maestro (2026-10-12): "veja o marketing skills no git e incorpore tudo que não temos". Decisões, por
> perguntas sim/não: instalar as 50 no Claude Code (`agent-network-mcp/.claude/skills`); de `tools/`, entra tudo
> menos o que chama APIs e os parceiros pagos; e incorporar no runner o que não tínhamos.

## Origem e licença

[coreyhaines31/marketingskills](https://github.com/coreyhaines31/marketingskills), **MIT**, auditado no commit
`1efedbc5148b54b2f0f6c6c9fe0be62e151c7fff`: 50 skills no formato Agent Skills (`SKILL.md` + `references/`). Cópia
limpa em `vendor/marketingskills/` (com `LICENSE` e `PROVENANCE.md`).

## Duas camadas, um script

`scripts/vendor_marketingskills.py --src <checkout> --commit <sha>` gera tudo e falha se o upstream mudar de forma
inesperada:

| Camada | O que entra | Onde |
|---|---|---|
| **Claude Code** (interactivo) | as **50** skills limpas | `vendor/marketingskills/skills/` → instaladas pelo maestro no `agent-network-mcp/.claude/skills` com o `skill-scout` (`scripts/install-marketing-skills.sh`) |
| **Runner** (pipeline) | as **39** que não tínhamos: skill (contrato PT + conhecimento upstream), agente, capability `partial`, agente na área `marketing` | `skills/marketing/<action>/`, `agents/marketing/<action>.agent.md`, `config/marketing-capabilities.yaml` (bloco gerado), `config/areas.yaml` |
| Catálogo de ferramentas | `tools/REGISTRY.md` sem parceiros, sem CLIs e sem guias de API | `vendor/marketingskills/tools-registry.md` (fora de `docs/knowledge/`, para não entrar no RAG de produção sem decisão) |

A capability `performance_analysis` (estava `planned`, sem agente) passa a usar a skill `attribution`.

## O que ficou de fora (e porquê)

- **Tudo o que chama APIs:** `tools/clis/` (67 CLIs com chaves de GA4, Meta Ads, Google Ads…), `tools/integrations/`
  (102 guias de API), `tools/composio/`, `tools/SETUP.md`. Nas skills, as ligações para esses guias ficam só com o
  texto e as 2 chamadas a CLIs (ad-creative e prospecting) saem; a secção "Tool Integrations" do ad-creative sai inteira.
- **Parceiros pagos:** Converly e Ploy (marcas ◆, "Verified Partner"), em 6 ficheiros de referência.
- `evals/` (testes do próprio repo) e o `.pyc` e as credenciais falsas de teste que o scan apontou (estão fora de `skills/`).

## Segurança (skill-scout)

- Repo inteiro no commit auditado: `dangerous`, mas **só fora de `skills/`**: um `.pyc` commitado, credenciais falsas
  nos testes dos CLIs, um `curl | sh` no guia do Ploy e um symlink. Nada disso entra.
- As 50 skills, no upstream e depois de limpas: **`safe`, 0 achados** (motor `asm` 1.0.4).
- Instalação: o `skill-scout` **recusa aprovações de um agente de IA**. O maestro corre o script no seu terminal e
  aprova o conteúdo pelos hashes (gerados pelo próprio `skill-scout` a partir de `oss/skill-scout`; se o vendor mudar
  sem regenerar, o hash não bate e nada é instalado).

## Conformidade (no contrato do runner)

`cold_email`, `prospecting`, `sms`, `emails`, `referrals` e `marketing_loops` levam uma nota obrigatória:
- RGPD + ePrivacy (PT: Lei 41/2004) e LGPD (BR);
- sem listas compradas de pessoas, sem identificação de visitantes a nível de pessoa (GOV-IMPACT-1, P-65);
- opt-in e opt-out;
- o envio é sempre humano.

O domínio continua `act_in_production: forbidden`.

## Custo

- **Claude Code:** as 50 descrições somam ~9,5k tokens por sessão do `agent-network-mcp` (com cache, baixo).
- **Runner:** cada skill entra no prompt só quando a action corre. O conhecimento está em inglês; a peça sai na língua do pedido.

## Mapa

As 11 que o runner já cobria em parte (vão só para o Claude Code):

| upstream | no runner |
|---|---|
| `ad-creative` | ad_creative |
| `ads` | media_plan |
| `ai-seo` | seo_brief |
| `seo-audit` | skills/meta/seo-tech-checklist |
| `copywriting` | copy_answer_first |
| `copy-editing` | critic / creative_review |
| `customer-research` | research |
| `social` | copy_social / trend_hunter |
| `video` | video_edit_plan |
| `influencer-marketing` | influencer_brief / ugc_brief |
| `content-strategy` | internal_brief / seo_brief |

As 39 novas no runner:

| upstream | action | capability | descrição |
|---|---|---|---|
| `ab-testing` | `ab_testing` | `ab_testing` | Desenha testes A/B e programas de experimentação: hipótese, métrica, tamanho de amostra e leitura do resultado. |
| `analytics` | `analytics` | `analytics_tracking` | Plano de medição e tracking (eventos, UTMs, GA4/GTM, dashboards); prepara a especificação, não mexe nas contas. |
| `aso` | `aso` | `app_store_optimization` | Auditoria e optimização de fichas na App Store e Google Play (título, keywords, screenshots, reviews). |
| `attribution` | `attribution` | `performance_analysis` | Lê resultados de campanha e atribuição (modelos, incrementalidade, MMM leve) para decidir o próximo ciclo. |
| `churn-prevention` | `churn_prevention` | `churn_prevention` | Reduz churn: fluxos de cancelamento, ofertas de retenção, recuperação de pagamentos falhados. |
| `co-marketing` | `co_marketing` | `co_marketing` | Encontra parceiros de co-marketing e planeia campanhas conjuntas. |
| `cold-email` | `cold_email` | `cold_outbound` | Rascunhos de outbound B2B (emails frios e follow-ups) dentro do RGPD/LGPD; nunca envia. |
| `community-marketing` | `community_marketing` | `community_marketing` | Estratégia de comunidade (fóruns, Discord, grupos) para crescimento e lealdade. |
| `competitor-profiling` | `competitor_profiling` | `competitor_profiling` | Perfis de concorrentes a partir dos sites deles: posicionamento, preços, mensagens, lacunas. |
| `competitors` | `competitors` | `comparison_pages` | Páginas de comparação e de alternativas (vs/alternativas) para SEO e para quem compra. |
| `cro` | `cro` | `conversion_optimization` | Optimização de conversão de páginas e formulários: diagnóstico, hipóteses e alterações priorizadas. |
| `directory-submissions` | `directory_submissions` | `directory_submissions` | Lista e textos para submeter o produto em directórios e sites de reviews; o envio é humano. |
| `emails` | `emails` | `email_sequences` | Sequências de email (boas-vindas, nurture, lifecycle, reactivação) com copy e calendário. |
| `events` | `events` | `events_marketing` | Planeia webinars, conferências e eventos (organizar, patrocinar, falar) com metas de pipeline. |
| `free-tools` | `free_tools` | `free_tools` | Planeia e avalia ferramentas grátis de marketing (calculadoras, geradores) para leads e SEO. |
| `image` | `image` | `marketing_images` | Briefs e prompts de imagens de marketing (heróis de blog, gráficos sociais, OG) e a sua optimização. |
| `launch` | `launch` | `launch_plan` | Plano de lançamento de produto ou funcionalidade: fases, canais, mensagens e checklist. |
| `lead-magnets` | `lead_magnets` | `lead_magnets` | Cria e optimiza lead magnets (guias, templates, checklists) para captar emails. |
| `marketing-council` | `marketing_council` | `marketing_council` | Painel simulado de especialistas que discute uma questão de marketing e converge numa recomendação. |
| `marketing-ideas` | `marketing_ideas` | `marketing_ideas` | Ideias e estratégias de marketing filtradas pelo estágio, canal e orçamento do negócio. |
| `marketing-loops` | `marketing_loops` | `marketing_loops` | Desenha loops recorrentes de marketing que um agente prepara; publicar ou enviar continua humano. |
| `marketing-plan` | `marketing_plan` | `marketing_plan` | Plano de marketing completo (objectivos, públicos, canais, orçamento, calendário, métricas). |
| `marketing-psychology` | `marketing_psychology` | `marketing_psychology` | Aplica princípios de psicologia e economia comportamental à mensagem, oferta e página, sem manipulação. |
| `offers` | `offers` | `offer_design` | Desenha ou melhora a oferta (o que se vende): valor, bónus, garantias, escassez honesta. |
| `onboarding` | `onboarding` | `onboarding_activation` | Onboarding e activação pós-registo: primeiro uso, tempo até ao valor, emails e checklists. |
| `paywalls` | `paywalls` | `paywalls_upgrades` | Paywalls, ecrãs de upgrade e feature gates dentro do produto. |
| `popups` | `popups` | `popups_overlays` | Popups, modais e banners de conversão: gatilhos, oferta, copy e regras de frequência. |
| `pricing` | `pricing` | `pricing_strategy` | Decisões de preço, planos e monetização, com hipóteses a validar. |
| `product-marketing` | `product_marketing` | `product_marketing_context` | Documento de contexto de product marketing (produto, público, posicionamento) que as outras skills leem primeiro. |
| `programmatic-seo` | `programmatic_seo` | `programmatic_seo` | Páginas SEO em escala a partir de templates e dados, com controlo de qualidade e de canibalização. |
| `prospecting` | `prospecting` | `prospecting_lists` | Define e qualifica listas de prospects B2B (empresas e cargos) dentro do RGPD/LGPD; sem identificação de pessoas. |
| `public-relations` | `public_relations` | `public_relations` | Relações públicas: ângulos, comunicados, pitch a jornalistas e comunicação de crise. |
| `referrals` | `referrals` | `referral_programs` | Programas de referência e afiliados: incentivo, mecânica, regras e medição. |
| `revops` | `revops` | `revenue_operations` | RevOps: ciclo de vida do lead, scoring, routing e passagem marketing → vendas. |
| `sales-enablement` | `sales_enablement` | `sales_enablement` | Material de vendas: one-pagers, decks, objecções e guiões de demo. |
| `schema` | `schema` | `schema_markup` | Schema markup e dados estruturados (JSON-LD) para páginas e rich results. |
| `signup` | `signup` | `signup_flow` | Optimiza registo, criação de conta e activação do trial. |
| `site-architecture` | `site_architecture` | `site_architecture` | Arquitectura do site: hierarquia de páginas, navegação, URLs e linkagem interna. |
| `sms` | `sms` | `sms_whatsapp` | Marketing por SMS e WhatsApp com opt-in explícito (RGPD/LGPD): fluxos, copy e frequência. |

## Actualizar

```bash
git clone https://github.com/coreyhaines31/marketingskills /tmp/marketingskills && git -C /tmp/marketingskills checkout <novo sha>
skill-scout scan coreyhaines31/marketingskills --ref <novo sha>      # rever antes
python scripts/vendor_marketingskills.py --src /tmp/marketingskills --commit <novo sha>
```

O teste `runner/tests/test_marketingskills_vendor.py` falha se algum parceiro ou chamada a API voltar a entrar.
