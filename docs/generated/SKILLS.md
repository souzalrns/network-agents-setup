# SKILLS — catálogo gerado automaticamente

> **Não editar à mão.** Regenerar com:
> `pnpm --filter @network-agents/scripts docs:skills`
>
> Gerado em: 2026-10-25
> Fonte: `skills/**/SKILL.md`
> Total: **117** skills
>
> **Nota (S35):** este catálogo é só documentação — a descoberta em runtime
> continua Advisory (`skills/meta/using-agent-skills/SKILL.md`), nada aqui
> impõe o mapa de invocação em código.

## Resumo por domínio

| Domínio | Quantidade |
|---------|------------:|
| claude | 26 |
| design | 4 |
| marketing | 58 |
| meta | 24 |
| security | 2 |
| trading | 3 |

## Domínio `claude`

| Nome | Vertical/Role | Prioridade | Descrição | Ficheiro |
|------|---------------|:----------:|-----------|----------|
| `api-and-interface-design` | — | — | Guides stable API and interface design. Use when designing APIs, module boundaries, or any public interface. Use when creating REST or GraphQL endpoints, defining type contracts between modules, or establishing boundaries between frontend and backend. | `skills/claude/api-and-interface-design/SKILL.md` |
| `browser-testing-with-devtools` | — | — | Tests in real browsers via Chrome DevTools MCP. Use when building or debugging anything that runs in a browser. Use when you need to inspect the DOM, capture console errors, analyze network requests, profile performance, or verify visual output with real runtime data. Requires the chrome-devtools MCP server to be configured. | `skills/claude/browser-testing-with-devtools/SKILL.md` |
| `ci-cd-and-automation` | — | — | Automates CI/CD pipeline setup. Use when setting up or modifying build and deployment pipelines. Use when you need to automate quality gates, configure test runners in CI, or establish deployment strategies. | `skills/claude/ci-cd-and-automation/SKILL.md` |
| `code-review-and-quality` | — | — | Conducts multi-axis code review. Use before merging any change. Use when reviewing code written by yourself, another agent, or a human. Use when you need to assess code quality across multiple dimensions before it enters the main branch. | `skills/claude/code-review-and-quality/SKILL.md` |
| `code-simplification` | — | — | Simplifies code for clarity. Use when refactoring code for clarity without changing behavior. Use when code works but is harder to read, maintain, or extend than it should be. Use when reviewing code that has accumulated unnecessary complexity. | `skills/claude/code-simplification/SKILL.md` |
| `context-engineering` | — | — | Optimizes agent context setup. Use when starting a new session, when agent output quality degrades, when switching between tasks, or when you need to configure rules files and context for a project. | `skills/claude/context-engineering/SKILL.md` |
| `debugging-and-error-recovery` | — | — | Guides systematic root-cause debugging. Use when tests fail, builds break, behavior doesn't match expectations, or you encounter any unexpected error. Use when you need a systematic approach to finding and fixing the root cause rather than guessing. | `skills/claude/debugging-and-error-recovery/SKILL.md` |
| `deprecation-and-migration` | — | — | Manages deprecation and migration. Use when removing old systems, APIs, or features. Use when migrating users from one implementation to another. Use when deciding whether to maintain or sunset existing code. | `skills/claude/deprecation-and-migration/SKILL.md` |
| `documentation-and-adrs` | — | — | Records decisions and documentation. Use when making architectural decisions, changing public APIs, shipping features, or when you need to record context that future engineers and agents will need to understand the codebase. | `skills/claude/documentation-and-adrs/SKILL.md` |
| `doubt-driven-development` | — | — | Subjects every non-trivial decision to a fresh-context adversarial review before it stands. Use when correctness matters more than speed, when working in unfamiliar code, when stakes are high (production, security-sensitive logic, irreversible operations), or any time a confident output would be cheaper to verify now than to debug later. | `skills/claude/doubt-driven-development/SKILL.md` |
| `find-skills` | — | — | Helps users discover and install agent skills when they ask questions like "how do I do X", "find a skill for X", "is there a skill that can...", or express interest in extending capabilities. This skill should be used when the user is looking for functionality that might exist as an installable skill. | `skills/claude/find-skills/SKILL.md` |
| `frontend-ui-engineering` | — | — | Builds production-quality, accessible, responsive user-facing UIs. Use when building or modifying interfaces and pages, creating components, implementing layouts, meeting WCAG accessibility requirements, managing state, or when the output needs to look and feel production-quality rather than AI-generated. | `skills/claude/frontend-ui-engineering/SKILL.md` |
| `git-workflow-and-versioning` | — | — | Structures git workflow practices. Use when making any code change. Use when committing, branching, resolving conflicts, or when you need to organize work across multiple parallel streams. Use when cutting a release, choosing a semantic version bump, tagging, or writing a changelog. | `skills/claude/git-workflow-and-versioning/SKILL.md` |
| `idea-refine` | — | — | Refines raw ideas into sharp, actionable concepts through structured divergent and convergent thinking. Use when an idea is still vague, when you need to stress-test assumptions before committing to a plan, or when you want to expand options before converging on one. Triggers on "ideate", "refine this idea", or "stress-test my plan". | `skills/claude/idea-refine/SKILL.md` |
| `incremental-implementation` | — | — | Delivers changes incrementally. Use when implementing any feature or change that touches more than one file. Use when you're about to write a large amount of code at once, or when a task feels too big to land in one step. | `skills/claude/incremental-implementation/SKILL.md` |
| `interview-me` | — | — | Extracts what the user actually wants instead of what they think they should want. Achieves this through one-question-at-a-time interview until ~95% confidence about the underlying intent. Use when an ask is underspecified ("build me X" without "for whom" or "why now"), when the user explicitly invokes ("interview me", "grill me", "are we sure?", "stress-test my thinking"), or when you catch yourself silently filling in ambiguous requirements before any plan, spec, or code exists. | `skills/claude/interview-me/SKILL.md` |
| `observability-and-instrumentation` | — | — | Instruments code so production behavior is visible and diagnosable. Use when adding logging, metrics, tracing, or alerting. Use when shipping any feature that runs in production and you need evidence it works. Use when production issues are reported but you can't tell what happened from the available data. | `skills/claude/observability-and-instrumentation/SKILL.md` |
| `performance-optimization` | — | — | Optimizes application performance across frontend, backend, queries, and databases. Use when performance requirements exist, when you suspect performance regressions, when Core Web Vitals or load times need improvement, when N+1 query patterns need fixing, or when profiling reveals bottlenecks. | `skills/claude/performance-optimization/SKILL.md` |
| `planning-and-task-breakdown` | — | — | Breaks work into ordered tasks. Use when you have a spec or clear requirements and need to break work into implementable tasks. Use when a task feels too large to start, when you need to estimate scope, or when parallel work is possible. | `skills/claude/planning-and-task-breakdown/SKILL.md` |
| `ponytail` | — | — | Forces the laziest solution that actually works, simplest, shortest, most minimal. Channels a senior dev who has seen everything: question whether the task needs to exist at all (YAGNI), reach for the standard library before custom code, native platform features before dependencies, one line before fifty. Supports intensity levels: lite, full (default), ultra. Use on ANY coding task: writing, adding, refactoring, fixing, reviewing, or designing code, and choosing libraries or dependencies. Also use whenever the user says "ponytail", "be lazy", "lazy mode", "simplest solution", "minimal solution", "yagni", "do less", or "shortest path", or complains about over-engineering, bloat, boilerplate, or unnecessary dependencies. Do NOT use for non-coding requests (general knowledge, prose, translation, summaries, recipes). | `skills/claude/ponytail/SKILL.md` |
| `security-and-hardening` | — | — | Hardens code against vulnerabilities. Use when handling user input, authentication, data storage, or external integrations. Use when building any feature that accepts untrusted data, manages user sessions, or interacts with third-party services. Use when personal data or privacy compliance (GDPR, CCPA) is involved. | `skills/claude/security-and-hardening/SKILL.md` |
| `shipping-and-launch` | — | — | Prepares production launches. Use when preparing to deploy to production. Use when you need a pre-launch checklist, when setting up monitoring, when planning a staged rollout, or when you need a rollback strategy. | `skills/claude/shipping-and-launch/SKILL.md` |
| `source-driven-development` | — | — | Grounds every implementation decision in official documentation. Use when you want authoritative, source-cited code free from outdated patterns. Use when building with any framework or library where correctness matters. | `skills/claude/source-driven-development/SKILL.md` |
| `spec-driven-development` | — | — | Creates specs before coding. Use when starting a new project, feature, or significant change and no specification exists yet. Use when requirements are unclear, ambiguous, or only exist as a vague idea. Use when a single requirement spans several independently testable capabilities and needs decomposing into a capability map of modules before specifying. | `skills/claude/spec-driven-development/SKILL.md` |
| `test-driven-development` | — | — | Drives development with tests. Use when implementing any logic, fixing any bug, or changing any behavior. Use when you need to prove that code works, when a bug report arrives, or when you're about to modify existing functionality. | `skills/claude/test-driven-development/SKILL.md` |
| `using-agent-skills` | — | — | Discovers and invokes agent skills. Use when starting a session or when you need to discover which skill applies to the current task. This is the meta-skill that governs how all other skills are discovered and invoked. | `skills/claude/using-agent-skills/SKILL.md` |

## Domínio `design`

| Nome | Vertical/Role | Prioridade | Descrição | Ficheiro |
|------|---------------|:----------:|-----------|----------|
| `design_critic` | design | P0 | Revê a coerência entre UX flow, UI spec e microcopy (tokens, estados, acessibilidade, UX writing) com scores de 1 a 5 e blockers em JSON. Usar depois de ui_spec (e de ux_writing, se existir) e antes do HITL. | `skills/design/design_critic/SKILL.md` |
| `ui_spec` | design | P0 | Especifica a UI a partir do UX flow: hierarquia visual por ecrã, tokens em 3 camadas, componentes com matriz de estados, baseline de acessibilidade e handoff para dev. Usar depois de ux_flow; não redefine a jornada nem gera código de produção. | `skills/design/ui_spec/SKILL.md` |
| `ux_flow` | design | P0 | Desenha a jornada antes da UI: problema, utilizador, jobs-to-be-done, fluxo principal com decisões, estados (empty, loading, error, success) e tabela de ecrãs sem visual. Usar após o brief ou research de produto; cores, tipografia e copy de marketing ficam fora. | `skills/design/ux_flow/SKILL.md` |
| `ux_writing` | design | P0 | Escreve a microcopy do produto: labels, CTAs, erros sem culpa, empty e loading states, tooltips e onboarding, com voz clara e honesta. Usar depois de ux_flow (idealmente com ui_spec); artigos, ads e posts são do vertical marketing. | `skills/design/ux_writing/SKILL.md` |

## Domínio `marketing`

| Nome | Vertical/Role | Prioridade | Descrição | Ficheiro |
|------|---------------|:----------:|-----------|----------|
| `ab_testing` | marketing | P2 | Desenha testes A/B e programas de experimentação: hipótese, métrica, tamanho de amostra e leitura do resultado. | `skills/marketing/ab_testing/SKILL.md` |
| `ad_creative` | marketing | P1 | Cria criativos de anúncio pagos: 2 a 4 ângulos com um recomendado, primary text, headlines e CTA por plataforma e specs de formato, com claims com fonte ou marcados como assumption. Usar depois de media_plan ou research. | `skills/marketing/ad_creative/SKILL.md` |
| `analytics` | marketing | P2 | Plano de medição e tracking (eventos, UTMs, GA4/GTM, dashboards); prepara a especificação, não mexe nas contas. | `skills/marketing/analytics/SKILL.md` |
| `aso` | marketing | P2 | Auditoria e optimização de fichas na App Store e Google Play (título, keywords, screenshots, reviews). | `skills/marketing/aso/SKILL.md` |
| `attribution` | marketing | P2 | Lê resultados de campanha e atribuição (modelos, incrementalidade, MMM leve) para decidir o próximo ciclo. | `skills/marketing/attribution/SKILL.md` |
| `churn_prevention` | marketing | P2 | Reduz churn: fluxos de cancelamento, ofertas de retenção, recuperação de pagamentos falhados. | `skills/marketing/churn_prevention/SKILL.md` |
| `co_marketing` | marketing | P2 | Encontra parceiros de co-marketing e planeia campanhas conjuntas. | `skills/marketing/co_marketing/SKILL.md` |
| `cold_email` | marketing | P2 | Rascunhos de outbound B2B (emails frios e follow-ups) dentro do RGPD/LGPD; nunca envia. | `skills/marketing/cold_email/SKILL.md` |
| `community_marketing` | marketing | P2 | Estratégia de comunidade (fóruns, Discord, grupos) para crescimento e lealdade. | `skills/marketing/community_marketing/SKILL.md` |
| `competitor_profiling` | marketing | P2 | Perfis de concorrentes a partir dos sites deles: posicionamento, preços, mensagens, lacunas. | `skills/marketing/competitor_profiling/SKILL.md` |
| `competitors` | marketing | P2 | Páginas de comparação e de alternativas (vs/alternativas) para SEO e para quem compra. | `skills/marketing/competitors/SKILL.md` |
| `copy_answer_first` | marketing | P0 | Escreve a peça a partir do seo_brief com a resposta directa nas primeiras linhas, H2 com valor e FAQ citável, para humanos e para assistentes de IA (ChatGPT, Claude, Gemini, Perplexity). Usar depois de seo_brief; não inventa dados. | `skills/marketing/copy_answer_first/SKILL.md` |
| `copy_social` | marketing | P1 | Escreve variantes de copy por canal (Instagram, TikTok, LinkedIn, …) a partir de uma mensagem core, com notas de formato e CTA só se pedido. Usar depois de research ou trend_hunter; nunca publica automaticamente. | `skills/marketing/copy_social/SKILL.md` |
| `creative_review` | marketing | P0 | Avalia uma peça criativa com a rubrica de creative review (on-brief, clareza, canal-fit, …) com notas de 1 a 5, blockers e sugestões. Usar no step creative_review, antes ou entre rondas de HITL; não substitui critic_item13 em artigos SEO. | `skills/marketing/creative_review/SKILL.md` |
| `critic` | marketing | P1 | Crítica genérica de packs sociais e peças sem foco SEO completo: scores, blockers, sugestões e publish_ready em JSON, segundo a rubrica de creative review. Usar quando o plano não pede critic_item13. | `skills/marketing/critic/SKILL.md` |
| `critic_item13` | marketing | P0 | Avalia a citabilidade de uma peça por sistemas de IA (ChatGPT, Claude, Gemini, Perplexity, Copilot, AI overviews, RAG) com a checklist do Item 13, para além do SEO de SERP. Usar depois de copy ou brief em peças que devem ser encontradas. | `skills/marketing/critic_item13/SKILL.md` |
| `cro` | marketing | P2 | Optimização de conversão de páginas e formulários: diagnóstico, hipóteses e alterações priorizadas. | `skills/marketing/cro/SKILL.md` |
| `directory_submissions` | marketing | P2 | Lista e textos para submeter o produto em directórios e sites de reviews; o envio é humano. | `skills/marketing/directory_submissions/SKILL.md` |
| `emails` | marketing | P2 | Sequências de email (boas-vindas, nurture, lifecycle, reactivação) com copy e calendário. | `skills/marketing/emails/SKILL.md` |
| `events` | marketing | P2 | Planeia webinars, conferências e eventos (organizar, patrocinar, falar) com metas de pipeline. | `skills/marketing/events/SKILL.md` |
| `follow_up` | marketing | P1 | Revê propostas e negócios parados (dias sem resposta, último contacto, próximo passo combinado) e redige follow-ups com um motivo novo e uma cadência que respeita quem pede para parar. Prepara: um humano revê e envia. | `skills/marketing/follow_up/SKILL.md` |
| `free_tools` | marketing | P2 | Planeia e avalia ferramentas grátis de marketing (calculadoras, geradores) para leads e SEO. | `skills/marketing/free_tools/SKILL.md` |
| `image` | marketing | P2 | Briefs e prompts de imagens de marketing (heróis de blog, gráficos sociais, OG) e a sua optimização. | `skills/marketing/image/SKILL.md` |
| `influencer_brief` | marketing | P1 | Prepara o brief de uma parceria com creators: objectivo e KPI, critérios de fit, deliverables, mensagens-chave, disclosure legal, compensação como intervalo e timeline com aprovação humana. Usar quando o plano inclui marketing de influência; nunca inventa acordos. | `skills/marketing/influencer_brief/SKILL.md` |
| `internal_brief` | marketing | P0 | Escreve o brief interno de handoff para criação (copy, design, social): objectivo numa frase, audiência, mensagem e provas, deliverables e restrições. Usar no step internal_brief; não serve para propostas comerciais nem pede credenciais. | `skills/marketing/internal_brief/SKILL.md` |
| `launch` | marketing | P2 | Plano de lançamento de produto ou funcionalidade: fases, canais, mensagens e checklist. | `skills/marketing/launch/SKILL.md` |
| `lead_magnets` | marketing | P2 | Cria e optimiza lead magnets (guias, templates, checklists) para captar emails. | `skills/marketing/lead_magnets/SKILL.md` |
| `lead_qualification` | marketing | P1 | Qualifica pedidos que chegam (formulário, email, WhatsApp) contra os critérios do negócio — encaixe, necessidade, prazo, orçamento declarado, decisor — com evidência citada, e propõe a resposta e a próxima acção. Prepara: um humano responde. | `skills/marketing/lead_qualification/SKILL.md` |
| `marketing_council` | marketing | P2 | Painel simulado de especialistas que discute uma questão de marketing e converge numa recomendação. | `skills/marketing/marketing_council/SKILL.md` |
| `marketing_ideas` | marketing | P2 | Ideias e estratégias de marketing filtradas pelo estágio, canal e orçamento do negócio. | `skills/marketing/marketing_ideas/SKILL.md` |
| `marketing_loops` | marketing | P2 | Desenha loops recorrentes de marketing que um agente prepara; publicar ou enviar continua humano. | `skills/marketing/marketing_loops/SKILL.md` |
| `marketing_plan` | marketing | P2 | Plano de marketing completo (objectivos, públicos, canais, orçamento, calendário, métricas). | `skills/marketing/marketing_plan/SKILL.md` |
| `marketing_psychology` | marketing | P2 | Aplica princípios de psicologia e economia comportamental à mensagem, oferta e página, sem manipulação. | `skills/marketing/marketing_psychology/SKILL.md` |
| `media_plan` | marketing | P1 | Estrutura um plano de media paga: objectivo e KPI, plataforma, campanhas, ad sets e ads, bandas de budget com stop-loss, audiências, compliance e checklist de tracking. Usar no step media_plan; não executa spend nem altera contas. | `skills/marketing/media_plan/SKILL.md` |
| `offers` | marketing | P2 | Desenha ou melhora a oferta (o que se vende): valor, bónus, garantias, escassez honesta. | `skills/marketing/offers/SKILL.md` |
| `onboarding` | marketing | P2 | Onboarding e activação pós-registo: primeiro uso, tempo até ao valor, emails e checklists. | `skills/marketing/onboarding/SKILL.md` |
| `paywalls` | marketing | P2 | Paywalls, ecrãs de upgrade e feature gates dentro do produto. | `skills/marketing/paywalls/SKILL.md` |
| `popups` | marketing | P2 | Popups, modais e banners de conversão: gatilhos, oferta, copy e regras de frequência. | `skills/marketing/popups/SKILL.md` |
| `pricing` | marketing | P2 | Decisões de preço, planos e monetização, com hipóteses a validar. | `skills/marketing/pricing/SKILL.md` |
| `product_marketing` | marketing | P2 | Documento de contexto de product marketing (produto, público, posicionamento) que as outras skills leem primeiro. | `skills/marketing/product_marketing/SKILL.md` |
| `programmatic_seo` | marketing | P2 | Páginas SEO em escala a partir de templates e dados, com controlo de qualidade e de canibalização. | `skills/marketing/programmatic_seo/SKILL.md` |
| `proposal` | marketing | P1 | Transforma o brief de um cliente numa proposta comercial pronta a rever (âmbito incluído e excluído, entregáveis, prazos, preço só com dados fornecidos, condições) e no email de envio. Prepara: um humano revê, completa e envia. | `skills/marketing/proposal/SKILL.md` |
| `prospecting` | marketing | P2 | Define e qualifica listas de prospects B2B (empresas e cargos) dentro do RGPD/LGPD; sem identificação de pessoas. | `skills/marketing/prospecting/SKILL.md` |
| `public_relations` | marketing | P2 | Relações públicas: ângulos, comunicados, pitch a jornalistas e comunicação de crise. | `skills/marketing/public_relations/SKILL.md` |
| `referrals` | marketing | P2 | Programas de referência e afiliados: incentivo, mecânica, regras e medição. | `skills/marketing/referrals/SKILL.md` |
| `research` | marketing | P0 | Faz a pesquisa de partida de um pipeline de conteúdo ou marketing, separando factos com fonte de assumptions e marcando lacunas em vez de inventar. Usar no início do pipeline; a peça final e o seo_brief ficam para os steps seguintes. | `skills/marketing/research/SKILL.md` |
| `revops` | marketing | P2 | RevOps: ciclo de vida do lead, scoring, routing e passagem marketing → vendas. | `skills/marketing/revops/SKILL.md` |
| `sales_enablement` | marketing | P2 | Material de vendas: one-pagers, decks, objecções e guiões de demo. | `skills/marketing/sales_enablement/SKILL.md` |
| `schema` | marketing | P2 | Schema markup e dados estruturados (JSON-LD) para páginas e rich results. | `skills/marketing/schema/SKILL.md` |
| `seo_brief` | marketing | P0 | Prepara o brief de SEO e de Findability multi-IA (intent, queries, outline e o bloco item_13 para citabilidade em ChatGPT, Claude, Gemini, Perplexity e AI overviews). Usar antes de copy_answer_first em artigos e landing pages; não escreve o artigo. | `skills/marketing/seo_brief/SKILL.md` |
| `signup` | marketing | P2 | Optimiza registo, criação de conta e activação do trial. | `skills/marketing/signup/SKILL.md` |
| `site_architecture` | marketing | P2 | Arquitectura do site: hierarquia de páginas, navegação, URLs e linkagem interna. | `skills/marketing/site_architecture/SKILL.md` |
| `sms` | marketing | P2 | Marketing por SMS e WhatsApp com opt-in explícito (RGPD/LGPD): fluxos, copy e frequência. | `skills/marketing/sms/SKILL.md` |
| `storytelling` | marketing | P1 | Reforça o arco narrativo de um copy social ou de uma peça existente (personagem, situação, tensão, resolução) sem contradizer o research nem o brief. Usar depois do copy; nunca fabrica cases de clientes. | `skills/marketing/storytelling/SKILL.md` |
| `transcript_analysis` | marketing | P1 | Analisa um vídeo, reel ou post: dispara o pipeline de transcrição do projecto, lê o resultado e devolve um resumo com uma recomendação objectiva (implementar ou não), confirmando nomes de ferramentas antes de os citar. Usar quando o utilizador envia um link de vídeo. | `skills/marketing/transcript_analysis/SKILL.md` |
| `trend_hunter` | marketing | P1 | Procura tendências em várias superfícies (assistentes de IA, AI search, social e depois SEO clássico), separa tendência de ruído e propõe hooks com riscos de ToS e de claims. Usar antes de criar conteúdo social ou de campanha. | `skills/marketing/trend_hunter/SKILL.md` |
| `ugc_brief` | marketing | P1 | Escreve o brief de um vídeo UGC: hook de 3 segundos, problema, demo ou prova, CTA, script falado de 15 a 60 segundos, b-roll e disclosure. Usar quando o plano pede conteúdo de creators ou anúncios em formato UGC. | `skills/marketing/ugc_brief/SKILL.md` |
| `video_edit_plan` | marketing | P1 | Planeia a edição de um vídeo a partir do script ou do UGC brief: cortes com timestamps, legendas, orientação de música, specs de export e checklist de QA, marcando o que precisa de ferramenta ou humano. Usar depois de ugc_brief ou de um script. | `skills/marketing/video_edit_plan/SKILL.md` |

## Domínio `meta`

| Nome | Vertical/Role | Prioridade | Descrição | Ficheiro |
|------|---------------|:----------:|-----------|----------|
| `ai-code-review-checklist` | meta_technique | P0 | Checklist vivo de erros recorrentes ja cometidos por IA em codigo gerado (RLS, IDOR, segredos hardcoded, onboarding de registo). Activar antes de aprovar qualquer PR ou mudanca gerada por IA. | `skills/meta/ai-code-review-checklist/SKILL.md` |
| `article-writing` | meta_technique | P1 | Escrita de artigos -- comecar pelo concreto, frases directas, nunca inventar factos ou casos. Activar ao escrever conteudo editorial. | `skills/meta/article-writing/SKILL.md` |
| `cheap-entity-extraction` | meta_technique | P1 | Decide quando extrair entidades ou classificar texto com um modelo pequeno local (GLiNER2) em vez de gastar uma chamada a um agente LLM completo. Activar para reconhecimento de padrao simples -- extraccao de nomes/datas, classificacao em categorias fixas, estruturacao de dados soltos. | `skills/meta/cheap-entity-extraction/SKILL.md` |
| `deploy-discipline` | meta_technique | P1 | Confirmar health checks e o projecto/ambiente certo antes de confiar num deploy automatico. Activar antes de qualquer deploy ou edicao de env vars de producao. | `skills/meta/deploy-discipline/SKILL.md` |
| `dispatching-parallel-agents` | meta_technique | P1 | Quando ha 2+ problemas independentes (sem estado partilhado nem dependencias), despachar um subagente por dominio, em paralelo, com um prompt focado e auto-suficiente; depois rever, verificar conflitos e correr a suite completa. Activar perante varias falhas ou tarefas independentes. | `skills/meta/dispatching-parallel-agents/SKILL.md` |
| `error-handling` | meta_technique | P1 | Tratamento de erros -- falhar rapido, erros tipados, separar mensagem de utilizador de mensagem de developer. Activar ao escrever ou rever blocos try/catch. | `skills/meta/error-handling/SKILL.md` |
| `frontend-a11y` | meta_technique | P1 | Acessibilidade basica de frontend -- labels, role/teclado em elementos custom, dimensoes de imagem. Activar ao escrever ou rever markup/componentes. | `skills/meta/frontend-a11y/SKILL.md` |
| `github-actions-ops` | meta_technique | P1 | Diagnostico de falhas de workflow do GitHub Actions -- distinguir falha transitoria de erro de logica. Activar ao investigar um run que falhou. | `skills/meta/github-actions-ops/SKILL.md` |
| `health-data-classification` | meta_technique | P1 | Classificar dado de saude sensivel antes de decidir onde/como guardar, mesmo em apps local-first. Activar em qualquer app que trate sintomas, diagnosticos ou medicacao. | `skills/meta/health-data-classification/SKILL.md` |
| `mcp-patterns` | meta_technique | P1 | Boas praticas para tools de servidor MCP -- schema de input validado, erros estruturados, idempotencia. Activar ao construir ou alterar um servidor MCP. | `skills/meta/mcp-patterns/SKILL.md` |
| `meta-workflow` | meta_technique | P0 | Disciplina de processo (Objetivo->Plano->Teste->Execucao->Revisao->Evidencia) para qualquer tarefa nao-trivial de codigo. Activar antes de tocar em qualquer ficheiro. | `skills/meta/meta-workflow/SKILL.md` |
| `nestjs-modules` | meta_technique | P1 | Onde colocar codigo novo num projecto NestJS -- modulos por dominio, logica transversal em common/, configuracao validada. Activar ao decidir estrutura de pastas NestJS. | `skills/meta/nestjs-modules/SKILL.md` |
| `prisma-patterns` | meta_technique | P1 | Armadilhas conhecidas do Prisma sobre PostgreSQL directo (sem Supabase) -- updateMany, transaccoes, migrations, soft-delete, connection pooling. Activar ao escrever ou rever codigo Prisma. | `skills/meta/prisma-patterns/SKILL.md` |
| `python-patterns` | meta_technique | P1 | Codigo Python legivel, com type hints e docstrings em calculo de dominio. Activar ao escrever codigo Python, sobretudo com calculo de engenharia. | `skills/meta/python-patterns/SKILL.md` |
| `react-native-expo` | meta_technique | P1 | Padroes Expo Router e separacao de estado num app React Native. Activar ao trabalhar num app com Expo Router. | `skills/meta/react-native-expo/SKILL.md` |
| `react-patterns` | meta_technique | P1 | Padroes React para estado derivado, waterfalls, listas longas e acessibilidade basica. Activar ao escrever ou rever componentes React web. | `skills/meta/react-patterns/SKILL.md` |
| `receiving-code-review` | meta_technique | P1 | Como responder a feedback de code review (humano, bot ou outra IA): verificar contra o codigo antes de implementar, pedir clarificacao do que nao se percebe, contestar com razoes tecnicas, sem concordancia performativa. Activar ao receber comentarios de review num PR. | `skills/meta/receiving-code-review/SKILL.md` |
| `rest-api-design` | meta_technique | P1 | Convencoes de desenho de API REST -- recursos no plural, sub-recursos, versionamento. Activar ao desenhar ou rever endpoints. | `skills/meta/rest-api-design/SKILL.md` |
| `security-audit` | meta_technique | P0 | Auditoria de seguranca defensiva de codigo, infra, skills e configs MCP -- cobre os 10 riscos do OWASP LLM Top 10 2026, mapeado a NIST AI RMF, MITRE ATLAS e MAESTRO. Activar antes de aprovar mudancas de infra/skills/MCP, ou periodicamente como auditoria. | `skills/meta/security-audit/SKILL.md` |
| `seo-tech-checklist` | meta_technique | P1 | Checklist de SEO tecnico -- rastreabilidade, indexabilidade, intencao de pesquisa por pagina. Activar ao rever ou planear SEO de um site. | `skills/meta/seo-tech-checklist/SKILL.md` |
| `skill-self-optimization` | meta_technique | P2 | Usa um optimizador automatico (SkillOpt) para validar e melhorar o texto de SKILL.md com base em execucoes reais, em vez de reescrever skills manualmente as cegas. Activar quando ha skills instaladas cujo texto nunca foi validado na pratica. | `skills/meta/skill-self-optimization/SKILL.md` |
| `subagent-driven-development` | meta_technique | P1 | Executar um plano com tarefas independentes despachando um subagente novo por tarefa, com review de cada tarefa (cumpre a spec + qualidade) e um review final do branch inteiro. Activar quando ha um plano aprovado e uma ferramenta de subagentes disponivel. | `skills/meta/subagent-driven-development/SKILL.md` |
| `using-agent-skills` | orchestrator_meta | P0 | Meta-skill de descoberta: inventaria e selecciona as skills certas para uma tarefa (modo B, sessao livre) ou valida a action ja fixada num plan.yaml (modo A). Nao executa a tarefa, so devolve o mapa de invocacao. Activar como primeiro passo sempre que nao ha action ja decidida. | `skills/meta/using-agent-skills/SKILL.md` |
| `vite-env-vars` | meta_technique | P2 | Regra do prefixo VITE_ para variaveis de ambiente expostas ao cliente. Activar ao adicionar ou rever env vars num projecto Vite. | `skills/meta/vite-env-vars/SKILL.md` |

## Domínio `security`

| Nome | Vertical/Role | Prioridade | Descrição | Ficheiro |
|------|---------------|:----------:|-----------|----------|
| `security-report` | security_technique | P1 | Consolida triage + audit defensivo num relatório estruturado (summary, findings mapeados, next_steps). Sem re-scan e sem patches. | `skills/security/reporter/SKILL.md` |
| `security-triage` | security_technique | P1 | Triagem defensiva de pedidos de segurança: severidade, superfícies e se a auditoria completa (security_audit) é necessária. Sem scanners e sem escrita. | `skills/security/triage/SKILL.md` |

## Domínio `trading`

| Nome | Vertical/Role | Prioridade | Descrição | Ficheiro |
|------|---------------|:----------:|-----------|----------|
| `market_analysis` | trading | P1 | Analisa um mercado ou activo a partir de fontes públicas permitidas (reguladores, bolsas, bancos centrais), separando factos com fonte de hipóteses e sem nunca recomendar ordens. Usar no início de um plano de trading; a revisão de risco e a decisão humana ficam para os passos seguintes. | `skills/trading/market_analysis/SKILL.md` |
| `post_trade_review` | trading | P1 | Lê o JSON do `economia-trader review` e escreve a revisão pós-trade da semana: processo avaliado à parte do resultado, resultado em R e em dinheiro, custos e um achado repetível por trade. Não reinterpreta os números nem recomenda ordens. | `skills/trading/post_trade_review/SKILL.md` |
| `risk_review` | trading | P1 | Verifica uma proposta de trade ou um ficheiro de limites contra a política de risco do economia-trader (stop obrigatório, perda no stop dentro dos limites, símbolos permitidos, sem alavancagem) e lista os bloqueios. Não aprova ordens: prepara a decisão humana. | `skills/trading/risk_review/SKILL.md` |

---
*Gerado a partir de skills/**/SKILL.md — mesmo padrão do docs:agents (F6).*
