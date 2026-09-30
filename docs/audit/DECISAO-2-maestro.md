# DECISÃO 2 — O maestro (base para ADR)

> **Base:** commit `3dc3b25` + AUDIT-3 (agentes) + DECISAO-1. **Data:** 2026-09-29.
> **Evidência nova:**
> - frontmatter dos 35 `agents/**/*.agent.md`: 30 com `vertical:`, **0** com `description:`, 35 com `action:`;
> - leitura de `packages/scripts/src/validate/check-consistency.ts`;
> - medição do prompt do router de produção (`agent-network-mcp/lib/agentRuntime.js:62-75`) sobre uma cópia read-only de `lib/agents.js` (`origin/main` `024e0ee`).

## Resumo

Hoje existem **três "maestros" parciais** e nenhum completo:

| Maestro | O que faz | Problema |
|---|---|---|
| TS | Router por palavras-chave + Planner LLM | Bloqueado (Q1) e deixa agentes inalcançáveis |
| Python | Nenhum: um humano escolhe o template | Sem delegação dinâmica |
| Produção (MCP) | Router LLM real sobre 33 agentes numa lista plana | Um agente por pedido, sem noção de área, ~1,5k tokens de prompt por pedido, a crescer ~44 tokens por agente |

Para servir a visão, o maestro precisa de **áreas como entidade de primeira classe**, de **alcançabilidade garantida por validação** e de **routing barato e com confiança**.

**Recomendação provisória:** router **hierárquico híbrido** (área primeiro por palavras-chave/embeddings, agente depois por LLM só dentro da área), sobre um **registo de áreas versionado e validado em CI**, no runtime escolhido na Decisão 1.

---

## 2.1 O que o maestro É hoje `[PEDIDO]`

### TypeScript (`apps/api` → `Orchestrator`)

| Peça | O que faz de facto | Evidência | Problema |
|---|---|---|---|
| `Router.route` | Palavras-chave por domínio, **primeiro match ganha**, omissão `business` | `Router.ts:2-18` | Sem confiança nem fallback; `routeWithConfidence` (`:19-33`) existe mas **não é usado** |
| Domínios conhecidos | `business, software, medical, marketing, construction, legal` | `Router.ts:3-8` | `software` (onde caem "jogo"/"game") tem **0 agentes** → `throw` (`Orchestrator.ts:298-300`) |
| `domain` do pedido | O body pode forçar o domínio, passando por cima do router | `Orchestrator.ts:242` | — |
| `AgentFactory` | `Map` de agentes; `getAgentsByDomain` filtra por `a.domain === domain` | `AgentFactory.ts:3,31-33` | Os **8 agentes sem `domain`** (4 meta, 4 horizontais) **nunca são candidatos** |
| `Planner.plan` | Recebe só os agentes do domínio e pede ao LLM passos em JSON; valida os ids; se falhar, fallback para o 1.º agente | `Planner.ts:14-101` | Manda "incluir o Research Agent", que não está na lista (`:31`), o que provoca o fallback |
| Deliberação antes do Planner | Bloqueia todos os pedidos (Q1) | AUDIT-2 | O maestro TS **não delega nada hoje** |
| Agentes na config | 24 (15 verticais em 5 domínios, 5 horizontais, 4 meta); 2 com `systemPrompt`; 0 com `tools` | `config/agents.config.ts` | Marketing: **3** na config vs **27** desenhados vs **17** `.agent.md` (AUDIT-3 §3.2) |

### Python (`plan_runner`)

| Peça | O que faz | Evidência |
|---|---|---|
| Selecção de plano | **Humana**: `plan_runner run <plan.yaml>` | `cli.py:15-17` |
| Resolução step → agente | Por nome: `agents/<vertical>/<action>.agent.md` (+ `skills/<vertical>/<action>/SKILL.md`) | `skills.py:14-21` |
| Meta-agente de descoberta | `using_agent_skills` devolve um "skill invocation map" e um template, mas **não executa** | `agents/meta/using_agent_skills.agent.md:9-11` |
| Metadados disponíveis | `vertical:` em 30/35; **`description:` em 0/35**; `skill:` ignorado pelo runner | grep frontmatter; AUDIT-3 A8 |

### `[ACRESCENTADO PELO AUDITOR]` Produção (`agent-network-mcp`)

| Peça | O que faz | Evidência |
|---|---|---|
| `routeRequest` | LLM (Gemini) recebe **todas** as descrições dos 33 agentes e devolve `{agent\|null, reason}` | `lib/agentRuntime.js:62-84` |
| Custo | Prompt ≈ **6 060 caracteres ≈ 1 515 tokens** de entrada por pedido; média de 175 caracteres (~44 tokens) por agente → **cresce linearmente** com o número de agentes | Medição sobre `lib/agents.js` (heurística chars/4, **NÃO medido com tokenizer**) |
| Granularidade | **Um agente por pedido**; sem plano multi-passo, sem áreas | `route.js:55` → `runAgent` |
| Confiança | Nenhuma: só `reason`; `null` se nenhum servir | `agentRuntime.js:69-71` |

### Validação existente

O `validate:consistency` (corre em CI, `ci.yml:103`) verifica **só 4 agentes jurídicos** (id, layer, visibility) e compara com o `docs/STATUS.md`, que é o **ficheiro histórico congelado** em 18/08 (`docs/STATUS.md:3`). **Não verifica alcançabilidade** (`check-consistency.ts:276-340`).

---

## 2.2 O que o maestro DEVIA ser para servir a visão `[PEDIDO]`

| Requisito | Porquê (visão) | Hoje |
|---|---|---|
| R1 — **Áreas como entidade** (id, descrição, agente de entrada, especialistas, skills, tools, política HITL, orçamento) | "Maestro que delega para agentes por área" | 4 taxonomias divergentes (AU-33) |
| R2 — **Nenhum agente inalcançável**, verificado em CI | "Vários agentes terão de ser criados", e o risco cresce com o número | 8 inalcançáveis no TS; 23/35 `.md` sem template |
| R3 — **Horizontais disponíveis em todas as áreas** (research, critic, docs…) | Reuso; é o que "horizontal" significa (`ECOSYSTEM.md:22`) | Os horizontais TS não têm domínio e ficam fora |
| R4 — **Routing com confiança** e caminho explícito para a dúvida (pedir clarificação, HITL ou horizontal genérico) | Nichos com risco (trader) não podem cair na omissão `business` | Omissão silenciosa |
| R5 — **Routing barato em tokens** | Objectivo n.º 1 | O router de produção gasta ~1,5k tokens por pedido e cresce com os agentes |
| R6 — **Política por área** (orçamento, HITL obrigatório, tools permitidas) | Trader: "ordens autónomas com budget"; segurança: "responsável por todos os itens" | Não existe (`toolsAllowed` sem fonte, orçamento não aplicado) |
| R7 — **Decisão rastreável** (área, agente, confiança, motivo, tokens) em log/ledger | Auditoria + medição de tokens | O MCP guarda só `last_interaction`; o TS não regista |
| R8 — Os 3 nichos entram como **dados** (áreas + agentes), não como código novo no router | Escalar áreas sem mexer no maestro | O router TS tem os domínios fixos em código |

---

## 2.3 Opções de desenho (apresentadas, não escolhidas) `[PEDIDO]`

### (a) Como se mapeia área → agente

| Opção | Descrição | Prós | Contras | Existe hoje? |
|---|---|---|---|---|
| M1 — campo `domain` na config | Como no `agents.config.ts` | Simples | Um agente = um domínio; os horizontais ficam de fora; config TS | Sim (TS) |
| M2 — `vertical:` no frontmatter | Como no `agents/**` | Já está em 30/35; a fonte é o próprio agente | 5 sem campo; sem descrição; nome de pasta = área | Parcial (Py) |
| M3 — **registo dedicado** (`config/areas.yaml`) que referencia agentes por id | Área com descrição, entrada, especialistas, horizontais, política | Um só sítio para decidir; validável | Mais um ficheiro a manter | Não |
| M4 — tabela no Supabase (`areas`, `area_agents`) | Dinâmico, partilhável com o MCP | Sem deploy para mudar áreas | Estado fora do git; precisa de governança de escrita | Não (o MCP tem `projects`, não relido aqui — **NÃO VERIFICADO**) |

### (b) Como se garante que nenhum agente fica inalcançável

| Opção | Mecanismo | Custo |
|---|---|---|
| G1 — **Validador em CI** (estender o `validate:consistency`): cada agente pertence a ≥1 área **ou** está marcado horizontal; cada área tem ≥1 agente de entrada; cada `action` resolve para skill e agente | Falha o build | Baixo |
| G2 — Horizontais sempre incluídos na lista de candidatos do planeador | Regra no maestro | Baixo |
| G3 — Fallback explícito quando a área está vazia ou a confiança é baixa (agente genérico/horizontal, ou pergunta ao utilizador) | Regra no maestro | Baixo |
| G4 — Gerar o registo a partir do frontmatter (uma só fonte) + G1 para as lacunas | Gerador (como o `docs:agents`) | Médio |

### (c) Como o router decide com confiança

| Opção | Mecanismo | Custo em tokens por pedido | Evidência de base |
|---|---|---|---|
| C1 — Palavras-chave + limiar de confiança | `routeWithConfidence` (já existe, não usado) | ~0 | `Router.ts:19-33` |
| C2 — LLM classificador sobre a lista plana de agentes | Padrão de produção | ~1,5k (33 agentes), a crescer linearmente | `agentRuntime.js:62-75`; medição |
| C3 — **Similaridade de embeddings** (descrição da área × pedido) | Embeddings Gemini (já usados) | 1 embedding do pedido; as áreas são embebidas uma vez | `embedder.py` |
| C4 — **Hierárquico híbrido**: área por C1/C3 (barato) → agente por LLM **só dentro da área** (lista curta) → abaixo do limiar, pedir clarificação ou HITL | Combinação | ~0 + LLM com N_área agentes (ex.: 27 de marketing ≈ 1,2k; 5 de uma área nova ≈ 0,2k) | Estimativa pela média medida (~44 tokens/agente), **NÃO medido** |
| C5 — O LLM planeador escolhe área **e** passos numa só chamada (como o `Planner.ts`) | Um prompt maior | O mais caro por pedido, mas com plano completo | `Planner.ts:17-53` |

### (d) Onde vivem as áreas

| Opção | Prós | Contras |
|---|---|---|
| Código (como `Router.ts`) | — | Mudar uma área = mudar código; já provou divergir |
| **Ficheiro de config versionado** | Revisão por PR; validação em CI; lido por qualquer runtime | Precisa de gerador ou disciplina |
| Supabase | Dinâmico; partilhado com o MCP | Fora do git; exige RLS/escrita controlada |
| Frontmatter dos agentes | Uma só fonte, perto do agente | Não descreve a área em si (descrição, política) |

---

## 2.4 Perguntas para o ADR (decisão humana) `[PEDIDO]`

| # | Pergunta | Opções | Depende de |
|---|---|---|---|
| ADR-M1 | **Em que runtime vive o maestro?** | Python / TS / produção MCP | Decisão 1 (Q1–Q3) |
| ADR-M2 | **Delegação: um agente por pedido, ou plano multi-passo por área?** | Um agente (como o MCP) / plano (como o `Planner.ts` e o `plan_runner`) / ambos por tipo de pedido | Visão "delega para agentes" (plural) |
| ADR-M3 | **Qual é a lista de áreas de partida?** (as 10 da AUDIT-3 §3.3 + 3 nichos, ou um corte menor) | — | Escopo |
| ADR-M4 | **Onde vive o registo de áreas?** | Config versionada / Supabase / frontmatter | Operação |
| ADR-M5 | **O que acontece com baixa confiança?** | Pedir clarificação / HITL / horizontal genérico / recusar | Risco por área (o trader exige HITL) |
| ADR-M6 | **Orçamento e HITL são por área?** (ex.: trader com limite por ordem e aprovação obrigatória) | Sim / global | Nicho financeiro (G1.5) |
| ADR-M7 | **Os 33 agentes de produção entram no registo** (como verticais plug-in) ou ficam só no MCP? | — | `ECOSYSTEM.md:33-38` (setup ↔ MCP) |
| ADR-M8 | **Nomenclatura canónica dos agentes** (resolver as 3 de marketing, AU-36) | ids do desenho / ids de `agents/` / novos | Migração |

---

## 2.5 Recomendação fundamentada `[PEDIDO]`

| Elemento | Recomendação | Porquê (evidência) |
|---|---|---|
| Mapeamento | **M3 (registo `config/areas.yaml`)**, alimentado pelo frontmatter (`vertical:`, **acrescentando `description:`** aos 35 agentes) | 30/35 já têm área; 0/35 têm descrição, e sem descrição nenhum router semântico funciona |
| Alcançabilidade | **G1 + G2 + G3**: validador em CI (estender o `check-consistency.ts`, que hoje só verifica 4 agentes e o STATUS histórico); horizontais sempre candidatos; fallback explícito | Os 8 inalcançáveis, o `software` vazio e os 23 `.md` sem template só apareceram numa auditoria manual |
| Routing | **C4 hierárquico híbrido** | Mantém o custo por pedido baixo quando os agentes crescerem. O router plano de produção já custa ~1,5k tokens e escalaria linearmente com os 27 de marketing + nichos |
| Confiança baixa | Pedir clarificação por omissão; **HITL obrigatório** nas áreas marcadas como de risco (financeiro) | Evita a omissão silenciosa `business` (`Router.ts:17`) |
| Rastreio | Registar {área, agente, confiança, tokens} em cada decisão | Base para medir o objectivo n.º 1 (AU-16) |
| Runtime | Segue a Decisão 1. Na VIA A, portar o padrão "área → planeador" (lógica de `Planner.ts` + `Router.ts`, ~140 LOC) para Python | DECISAO-1 §1.4 |

**Não é possível fechar sem o humano:** ADR-M1 (depende da Decisão 1), ADR-M2 e ADR-M3 são escolhas de produto.

---

## Limites desta secção

- A medição de tokens usa a heurística caracteres/4. **NÃO foi usado o tokenizer do Gemini.**
- A tabela `projects` do MCP (opção M4) não foi relida nesta secção.
- As estimativas de custo de C4 assumem a média medida de 175 caracteres por descrição. Os agentes novos podem ter descrições maiores.
