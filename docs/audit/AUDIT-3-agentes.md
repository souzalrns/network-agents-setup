# AUDIT-3 — Agentes: instanciado vs. desenhado vs. em falta + delegação

> **Base:** commit `3dc3b25`. **Data:** 2026-09-29.
> **Método:** leitura de `config/agents.config.ts`, `agents/**`, `skills/**`, dos 12 templates `*.plan.yaml` e dos docs de desenho. A resolução agente↔skill dos templates foi verificada com um script que aplica **a mesma regra** de `runner/plan_runner/skills.py:14-21`. Para os agentes de produção, leitura read-only de `agent-network-mcp/docs/generated/AGENTS.md`.

## Resumo

"Agente" significa três coisas diferentes neste repo, e nenhuma delas corre sozinha:

1. **24 entradas em `config/agents.config.ts`.** São instanciadas no runtime TS, mas o pedido nunca chega a elas (Q1, Fase 2). Só 2 têm `systemPrompt`, nenhuma tem `tools`, e 8 não têm `domain`, por isso **nunca são selecionáveis**.
2. **35 ficheiros `agents/**/*.agent.md`.** O runtime Python entrega-os a um worker externo; só **12** são alcançáveis a partir dos templates existentes.
3. **27 agentes de marketing desenhados em `docs/marketing-agency-agents.md`.** Estão documentados; o número "23" do brief não aparece em nenhum doc.

O maestro que existe (Router por palavras-chave → Planner LLM) reconhece 6 domínios. O domínio `software`, para onde vão "jogo" e "game", tem **0 agentes**. **Financeiro/trader e segurança não existem como área.**

---

## 3.1 O que `config/agents.config.ts` instancia `[PEDIDO]`

Registados em `apps/api/src/index.ts:61` via `AgentFactory.registerAgent` (`AgentFactory.ts:5-24`). Lista completa (id | camada | visibilidade | domínio | linha):

| # | id | camada | visib. | domínio | linha | prompt próprio? |
|---|---|---|---|---|---|---|
| 1 | `orchestrator-general` | meta | public | — | 5 | não |
| 2 | `domain-router` | meta | public | — | 11 | não |
| 3 | `context-manager` | meta | public | — | 17 | não |
| 4 | `task-planner` | meta | public | — | 23 | não |
| 5 | `research-agent` | horizontal | public | — | 30 | não |
| 6 | `critic-validator` | horizontal | public | — | 36 | não |
| 7 | `documentation-agent` | horizontal | public | — | 42 | não |
| 8 | `methodology-legal` | horizontal | public | — | 48 | não |
| 9 | `lead-qualifier` | vertical | private | business | 55 | não |
| 10 | `proposal-agent` | vertical | private | business | 62 | não |
| 11 | `financial-analyst` | vertical | private | business | 69 | não |
| 12 | `clinical-orchestrator` | vertical | private | medical | 77 | não |
| 13 | `triage-agent` | vertical | private | medical | 84 | não |
| 14 | `cardiologist-agent` | vertical | private | medical | 91 | não |
| 15 | `marketing-orchestrator` | vertical | private | marketing | 99 | não |
| 16 | `copywriter-agent` | vertical | private | marketing | 106 | não |
| 17 | `geo-agent` | vertical | private | marketing | 113 | não |
| 18 | `construction-orchestrator` | vertical | private | construction | 121 | não |
| 19 | `architect-agent` | vertical | private | construction | 128 | não |
| 20 | `civil-engineer` | vertical | private | construction | 135 | não |
| 21 | `legal-orchestrator` | vertical | private | legal | 143 | não |
| 22 | `civil-law-br` | vertical | private | legal | 155 | sim (template, `:160`) |
| 23 | `civil-law-pt` | vertical | private | legal | 164 | sim (template, `:169`) |
| 24 | `legal-research` | horizontal | public | legal | 173 | não |

**Achados sobre a config:**

| ID | Achado | Evidência |
|---|---|---|
| A1 | **8 agentes sem `domain` nunca são selecionáveis.** O Orchestrator só passa ao Planner `getAgentsByDomain(domain)` (`Orchestrator.ts:297`; `AgentFactory.ts:31-33`), e os agentes 1–8 têm `domain` indefinido. Os 4 "meta" (incluindo `orchestrator-general` e `domain-router`) são **decorativos**: o papel deles é feito por código (`Router.ts`, `Planner.ts`) | config + Orchestrator |
| A2 | **22/24 sem `systemPrompt`.** Caem no fallback `"You are ${id}, a specialist in ${description}."` (`Executor.ts:167`) | grep `systemPrompt` config: só `:160,:169` |
| A3 | **F1 (profiles) não está ligado.** `resolveAgentPrompt()` (`AgentFactory.ts:49-57`) não tem nenhum chamador fora dos testes (grep). O Executor usa `agent.systemPrompt` cru → o LLM receberia `"Direito Civil {{jurisdiction_label}}…"` literal | grep `resolveAgentPrompt` |
| A4 | **0/24 com `tools`** → nem por aqui chega `toolsAllowed` (Fase 2, 2.2) | grep `tools:` config = 0 |
| A5 | **`PUBLIC_MODE=true` deixa um único domínio servível.** Todos os verticais são `private` e são saltados (`AgentFactory.ts:6-9`); dos públicos, só `legal-research` tem `domain`. Qualquer domínio que não seja `legal` → `"No agents found for domain"` (`Orchestrator.ts:298-300`). A "demo pública" do `CLAUDE.md` não funciona no runtime TS | config + AgentFactory |
| A6 | O `Planner` manda o LLM "incluir o Research Agent" (`Planner.ts:31`), mas o `research-agent` não tem domínio e nunca está na lista; se o LLM o escolher, `validatePlan` lança e cai no `fallbackPlan` com o 1.º agente do domínio (`Planner.ts:78-101`) | Leitura |

---

## 3.2 Desenhado em `docs/` mas não instanciado `[PEDIDO]`

### Marketing — o caso pedido ("23 desenhados vs 3 que correm")

| Fonte | Agentes | Evidência |
|---|---|---|
| Desenho (`docs/marketing-agency-agents.md`) | **27** = 18 horizontais (`:19-402`: ux, ui, diretor-arte, storytelling, geo-agent, ai-visibility, seo-specialist, copywriter, social-media-manager, media-buyer, performance-analyst, editor-video, influencer-strategist, ugc-specialist, trend-hunter, research-marketing, critic-criativo, content-strategist) + 9 verticais (`:427-557`: marketing-orquestrador, estrategista-marca, brand-guard-cliente, social-instagram-cliente, social-tiktok-cliente, trafego-pago-cliente, producao-audiovisual-cliente, tiktok-shop-cliente, conteudo-calendario-cliente) | `grep "^### "` |
| Knowledge packs por papel (`docs/knowledge/*.md`) | 27 packs com nome de papel (os mesmos ids do desenho) | `ls docs/knowledge` |
| `agents/marketing/*.agent.md` (Python) | **17**, com ids **diferentes** do desenho (ex.: `copy_answer_first`, `critic_item13`, `internal_brief`) | `ls agents/marketing` |
| `config/agents.config.ts` (TS) | **3** (`marketing-orchestrator`, `copywriter-agent`, `geo-agent`), sem prompt | 3.1 |
| Alcançáveis a partir de templates Python | **11** de marketing + 1 de design (ver 3.3) | Script de resolução |

**Correcção ao brief:** o número "23" não aparece em nenhum doc do repo (grep `23 … agente`). A melhor leitura é **27 desenhados → 17 com ficheiro `.agent.md` → 11 alcançáveis por template → 3 na config TS (e 0 a correr, por Q1)**. Registado como correcção de classificação.

**Três nomenclaturas para os mesmos papéis:** desenho/knowledge (`seo-specialist`, `copywriter`), `agents/` (`seo_brief`, `copy_answer_first`) e config TS (`copywriter-agent`). Nenhum mapeamento formal as liga.

### Outros domínios desenhados (`docs/estrutura-geral-agentes.md`)

Especificação ampla com **5 camadas** (`:7`) e dezenas de agentes por domínio: Empresarial (financeiro, RH, operações, BI: `:20-24`), **Software & Games** (`:26-39`, incluindo `P-AG-019`: Gameplay, Engine Unity/Unreal/Godot, Physics & AI, Level Design, **Multiplayer/Netcode**), Médica (`:41-58`), Marketing (`:73-96`), Construção (`:99+`). **Nenhum** agente de Software/Games está instanciado em nenhum dos runtimes.

---

## 3.3 Por área: correm / desenhados / em falta `[PEDIDO]`

"Correm" = alcançável e executável hoje. **TS: 0 em todas as áreas** (Q1). **Python:** alcançável por template com `.agent.md` + `SKILL.md` resolvidos; o trabalho continua a precisar de worker externo. "Produção MCP" = agentes do `agent-network-mcp` (fora deste repo; router Gemini em produção segundo `agent-network-mcp/docs/STATUS.md:30`).

| Área | Palavra-chave no Router TS | Config TS | `agents/*.agent.md` | Skills | Templates | Alcançáveis (Py) | Produção MCP (ids) | Desenhados (docs) |
|---|---|---|---|---|---|---|---|---|
| Marketing | `marketing` (`Router.ts:6`) | 3 | 17 | 16 (`skills/marketing`) | 9 | 11 | `marketing` | 27 |
| Design/UX | — (cai em `business`/`software`) | 0 | 5 | 4 (`skills/design`) | 2 | 1 (`design_critic`) | `design` | 2 (ux, ui) + P-AG-017 |
| Engenharia/Software | `software` (`:4`) | **0** | 4 | via `skills/claude` + `skills/meta` | 0 | 0 | `revisor-codigo`, `guia-tdd`, `qualidade-dados`, `desenvolvimento` | P-AG-015..025 |
| Negócio/Gestão | `business` (`:3`, + omissão) | 3 | 2 (`gestao`) | 0 dedicadas | 0 | 0 | `gestao-empresarial`, `contabilidade` | P-AG-010..014 |
| Jurídico | `legal` (`:8`) | 4 | 0 | 0 (knowledge em `docs/knowledge/legal`) | 0 | 0 | `direito-br-pt`, `viannalegal` | — |
| Saúde | `medical` (`:5`) | 3 | 0 | 1 (`health-data-classification`) | 0 | 0 | `cardiologia`, `dermatologia`, `oftalmologia` | P-AG-030..040 |
| Construção | `construction` (`:7`) | 3 | 0 | 0 | 0 | 0 | `construtora`, `pladur`, `reformas`, `hvac`, `engenharia-civil-arquitetura`, … | secção 6 |
| Atendimento | — | 0 | 1 | 0 | 0 | 0 | `comunicacoes-atendimento` | — |
| Produto | — | 0 | 1 | várias em `skills/meta` | 0 | 0 | `produto-tech-transversal`, `apps-produto` | — |
| Meta/Orquestração | — | 4 (inalcançáveis, A1) | 5 | 21 (`skills/meta`) | — | 0 | `arquitetura-agentes`, `planejador`, `radar-ferramentas` | camada 1 |
| **Financeiro/Trader** (nicho novo) | `financeiro` → **business** | 1 (`financial-analyst`, sem prompt) | 0 | 0 | 0 | 0 | `investimentos-brasil` (análise B3/macro) | P-AG-010 (contas/conciliação: não é trading) |
| **Jogos** (nicho novo) | `game`/`jogo` → **software (0 agentes → erro)** | 0 | 0 | 0 | 0 | 0 | 0 | P-AG-015/019 |
| **Segurança** (nicho novo) | — (`segurança` → `business`) | 0 | 1 (`meta/security_auditor`) | 2 (`skills/meta/security-audit`, `skills/claude/security-and-hardening`) | 0 | **0** (ver A8) | `revisor-codigo` (parte security) | P-AG-022 (Security Reviewer) |

**Achados da resolução Python (templates):**

| ID | Achado | Evidência |
|---|---|---|
| A7 ✅ RESOLVIDO 2026-09-30 (`8a1daca`) | **7 skills usadas em templates sem agente correspondente**, por diferença de nome: `influencer_brief`↔`influencer`, `media_plan`↔`media_buyer`, `ugc_brief`↔`ugc`, `video_edit_plan`↔`editor_video`, `ui_spec`↔`ui`, `ux_flow`↔`ux`, `ux_writing`↔`ux_writer`. O `request.json` sai com `agent_path: null` | Script sobre os 58 steps dos 12 templates; `skills.py:19-21` |
| A8 ✅ RESOLVIDO 2026-09-30 (`8a1daca`) | **O campo `skill:` do frontmatter dos agentes é ignorado.** O runner resolve só por `skills/<vertical>/<action>/SKILL.md`. `security_auditor` declara `action: security_audit`, mas a pasta é `skills/meta/security-audit` (hífen) → nunca resolveria | `agents/meta/security_auditor.agent.md:1-8`; `skills.py:14-16` |
| A9 ✅ resolvido por efeito do A8 (`8a1daca`; verificado: os 4 steps do template resolvem agente + skill) `[ACRESCENTADO PELO AUDITOR]` | **`design-flow.plan.yaml` (o template, não o demo) continua partido.** 0 steps com `vertical:`, logo `ux_flow`/`ui_spec`/`ux_writing`/`design_critic` resolvem contra `marketing` e nenhum existe. O S34 corrigiu só o `…/examples/design-flow-demo.plan.yaml` | `grep -c vertical:` = 0 vs 4 |
| A10 | `plan_approve` (14 usos) é um gate humano sem skill, o que é esperado | — |
| A11 | **23 dos 35 `.agent.md` não são referenciados por nenhum template**: os 13 de `engenharia` (4), `gestao` (2), `atendimento` (1), `produto` (1) e `meta` (5); 4 de `design` (`identidade-visual`, `ui`, `ux`, `ux_writer`, os três últimos também por A7); 6 de `marketing` (`content_analyst`, `editor_video`, `influencer`, `marketing`, `media_buyer`, `ugc`) | Script + `ls agents` |

---

## 3.4 Lacunas de delegação `[PEDIDO]`

### O que o maestro delega hoje, exactamente

| Runtime | Mecanismo | O que delega de facto | Evidência |
|---|---|---|---|
| TS (`apps/api`) | `Router` (palavras-chave, primeiro match) → `getAgentsByDomain` → `Planner` (LLM escolhe agentes e passos) → `Executor` | **Nada.** Bloqueado na deliberação (Q1). Se Q1 fosse corrigido: só verticais do domínio; horizontais e meta nunca | `Orchestrator.ts:242,262-270,297-303` |
| Python (`plan_runner`) | Um **humano escolhe o template**; os steps e a ordem são fixos no YAML | Nada dinâmico. Cada step é entregue a um worker externo | `cli.py`; `executor.py:61-134` |
| IDE (meta-skill) | `agents/meta/using_agent_skills.agent.md` devolve um "skill invocation map" + template | Mapeia; **não executa**; depende do agente do IDE | `using_agent_skills.agent.md:9-11` |
| Produção (`agent-network-mcp`) | Router LLM (Gemini Flash Lite) sobre 33 agentes | É o único router real, e fica **fora deste repo** | `agent-network-mcp/docs/STATUS.md:30` |

### Que áreas existem e como são reconhecidas

Há **quatro taxonomias** e nenhuma é fonte de verdade:

| Taxonomia | Valores |
|---|---|
| Domínios do Router TS | `business, software, medical, marketing, construction, legal` (`Router.ts:2-9`) |
| Domínios da config TS | `business, medical, marketing, construction, legal` (sem `software`) |
| Pastas `agents/` + `skills/` (Python) | `marketing, design, meta, engenharia, gestao, atendimento, produto` (+ `claude`) |
| Ids de produção MCP | 33 ids por negócio/especialidade |

Consequências: um pedido de **jogos** é reconhecido (`game`/`jogo`) e mandado para um domínio sem agentes. Um pedido de **trading** cai em `business` pela omissão (não há palavra-chave). Um pedido de **segurança** também cai em `business`. Design, atendimento e produto não são reconhecidos. E o Router é "primeiro match": "campanha para o app" → `software`, porque `business`/`software` vêm antes de `marketing` na iteração (`Router.ts:12-15`).

### O que falta para o maestro delegar por área (necessidades, não desenho)

| # | Falta | Porquê | Tipo |
|---|---|---|---|
| D1 | **Resolver Q1** (escala dos critérios da deliberação) e a retoma pós-HITL | Sem isto, nenhuma delegação TS acontece | BUG |
| D2 | **Decidir qual é o maestro** (TS `Orchestrator`, `plan_runner` + planeador, ou reutilizar o router de produção do MCP) | Hoje há 3 metades sem ponte (Fase 1 R8) | FALTA-DECIDIR |
| D3 | **Taxonomia única de áreas** num registo, consumido pelo router, pela config e pela resolução Python | 4 taxonomias divergentes (tabela acima) | FALTA-CONSTRUIR |
| D4 | **Router que cubra as áreas-alvo**, incluindo financeiro, jogos e segurança, com confiança e fallback (o `routeWithConfidence` existe em `Router.ts:19-33` mas **não é usado**) | Palavras-chave com primeiro match e omissão silenciosa `business` | FALTA-CONSTRUIR |
| D5 | **Horizontais e meta selecionáveis entre domínios** (o Planner devia receber domínio + horizontais) | A1, A6 | BUG/DESENHO |
| D6 | **Fallback quando o domínio não tem agentes** (hoje lança erro) | `software` e jogos → erro | BUG |
| D7 | **Contrato de handoff** entre maestro e agente de área: entrada, saída, tools, orçamento | Hoje o `PlanStep` não tem orçamento nem `toolsAllowed` com fonte | FALTA-DECIDIR |
| D8 ✅ RESOLVIDO 2026-09-30 (`8a1daca`) | **Resolução agente↔skill por frontmatter** (ou normalização de nomes) | A7, A8 | BUG |
| D9 | **Worker que execute os steps Python** (LLM com custo-zero, ex. Gemini) se o maestro for o `plan_runner` | Sem worker nada corre sozinho (Fase 2, Y6) | FALTA-CONSTRUIR |

### Que agentes teriam de existir por área (necessidade, não desenho final)

| Área | Papéis necessários para a delegação funcionar | O que já existe e serve |
|---|---|---|
| Financeiro/Trader | Ingestão de dados de mercado; analista; **guardião de risco/orçamento** (limites por ordem, dia e total); executor de ordens **com HITL obrigatório** e *paper trading* por omissão; auditor/registo de ordens | `financial-analyst` (vazio); `investimentos-brasil` (MCP, só análise); `DeliberationEngine` (scoring reutilizável para gates); B3 "trading simulação only" (não iniciado) |
| Jogos | Game designer (GDD, regras, loop); programador de gameplay; **multiplayer/netcode**; pipeline de assets 2D→3D (geração e validação de imagens/modelos); QA de jogo | Só desenho (P-AG-015/019); B4 gamedev (não iniciado) |
| Segurança | Orquestrador de segurança (dono transversal de "todos os itens de segurança"); auditor de código/deps (existe `.md`); scanner de segredos/credenciais; postura de infra/cloud/CI; resposta a incidentes | `agents/meta/security_auditor.agent.md`; `skills/meta/security-audit`; `skills/claude/security-and-hardening`; auditorias em `docs/architecture/SECURITY-AUDIT*.md`; `SsrfGuard`/`ToolPolicy`/`ActionReceipt` (`packages/mcp`) |
| Marketing | Instanciar os 27 desenhados no runtime escolhido, com prompt + knowledge + skill; um só esquema de nomes | 17 `.agent.md`, 16 skills, 27 knowledge packs, 9 templates |
| Restantes (design, eng., gestão, jurídico, saúde, construção, atendimento, produto) | Pelo menos um agente de entrada por área, com prompt e skills, visível para o router | Existem peças soltas (tabela 3.3); os verticais de negócio reais vivem no MCP |

---

## Limites desta fase

- A contagem de agentes de produção vem de `agent-network-mcp/docs/generated/AGENTS.md` (gerado a 2026-08-19); não foi revalidada contra o `lib/agents.js` actual.
- "Alcançáveis (Py)" mede resolução de ficheiros, não qualidade: com um worker, o step recebe `AGENT.md` + `SKILL.md`; sem worker, fica em `waiting_external`.
