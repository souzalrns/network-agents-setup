# Auditoria de Agentes — Fase 5: Coding/Research Agents + Agentes Especializados

Continuação de `FASE1`–`FASE4-AGENTES.md`.

## Parte A — Coding/Research Agents (2.14)

### 0. Achado crítico de metodologia: a Fase 3 da auditoria de Memória citou o repo errado

`memory/FASE3-MEMORIA.md` avaliou `OpenHands/OpenHands` (88.401★) como "de longe o mais popular de tudo o que foi avaliado nas 3 fases" — mas só ao nível de contagem de estrelas/licença. Esta fase aprofundou e encontrou algo que muda a leitura: **`OpenHands/OpenHands` já não é o runtime do agente**. Em algum momento recente o projeto separou-se em dois repositórios:

- `OpenHands/OpenHands` (88.447★) — hoje o **"Agent Canvas"**, uma aplicação Electron/TypeScript de controlo/UI. Conteúdo raiz confirmado: `electron/`, `src/`, `vite.config.ts`, `playwright.config.ts` — nenhum pacote Python de agente.
- `OpenHands/software-agent-sdk` (criado 2025-08-23, **1.134★**, 538 forks) — **o loop do agente de facto** (`conversation.py`, `state.py`, `stuck_detector.py`, `event_store.py`).

**Isto é exatamente o tipo de erro que a disciplina "código > README/estrelas" existe para prevenir**: a métrica mais visível (estrelas do repo "principal") apontava para o produto errado. Fica registado como correção, não crítica à Fase 3 — a auditoria de memória não tinha motivo para saber disto na altura, pois só precisava confirmar licença/popularidade para a decisão de sandbox, não a arquitetura do loop de agente.

### 1. OpenHands (`software-agent-sdk`) — aprofundado

| Alegação | Evidência | Validado? |
|---|---|---|
| "Sandbox Docker obrigatório" | README: *"agents can either use the local machine as their workspace, or run inside ephemeral workspaces (e.g. in Docker or Kubernetes)"* | **Refutado** — Docker é opcional |
| Checkpoint/resume de sessões longas | `event_store.py`/`state.py`/`persistence_const.py`: `base_state.json` + replay de eventos por `conversation_id` | Confirmado, com ressalva: issue `OpenHands/OpenHands#14260` — resume incompleto após restart de sandbox em modo ACP |
| Detecção de loops/stuck | `stuck_detector.py`, classe `StuckDetector.is_stuck()` — deteta ciclos ação-observação, ação-erro, "monólogo", padrões alternados [A,B,A,B]; gera nudge textual | Confirmado |
| Extensibilidade | `Agent(llm=llm, tools=[...])` + `Conversation.run()` — API Python limpa, usável sem UI | Confirmado |

**Padrões extraíveis:** (1) `StuckDetector` — detetor de ciclos repetidos com nudge textual, aplicável a `runner/plan_runner/executor.py` (hoje o file-drop pattern não deteta repetição sem progresso); (2) persistência por replay de eventos, mais robusta a crashes que o file-drop atual; (3) `DeploymentConfig` como abstração plugável de "onde corre o código".

**Classificação:** EXTRACT (padrões) — não ADOPT: projeto com apenas ~1 ano de existência, issue de resume conhecida em aberto.

### 2. SWE-agent

Confirmado repo canônico `SWE-agent/SWE-agent` (org mudou de `princeton-nlp`), 20.355★, MIT, 640 PRs mergeados, push 2026-09-14.

| Alegação | Evidência | Validado? |
|---|---|---|
| ACI é mais que bash cru | `tools/tools.py`: `ToolConfig` gere "bundles" de `Command`; `ToolFilterConfig.should_block_action()` bloqueia `vim`/`nano`/shells interativos | Confirmado |
| Editor com janela de ~100 linhas dobra o SWE-Bench score | `docs/background/aci.md` + `tools/edit_anthropic/`: `cat -n` numerado, janela ~100 linhas, edição por linha-alvo | Confirmado — é a alegação empírica central do paper NeurIPS 2024, refletida no código real |
| Retry tipado por classe de erro | `agents/agents.py`: `max_requeries` distingue `FormatError` de `BashIncorrectSyntaxError`, contagens separadas | Confirmado |

**Padrões extraíveis (maior ROI comprovado desta fase):** (1) **windowed file viewer + edição por linha-alvo** — intervenção com evidência empírica forte (2x em benchmark real), diretamente aplicável a `agents/engenharia/desenvolvimento.agent.md`; (2) blocklist de comandos perigosos antes do ambiente de execução; (3) retry tipado por causa; (4) trajetória persistida a cada passo (`save_trajectory()`).

**Classificação:** ADAPT — padrão isolável (script bash autocontido), evidência forte, atividade real.

### 3. Aider

Repo `Aider-AI/aider` (mudou de `paul-gauthier/aider`), 49.046★, Apache-2.0. **Achado de risco:** último push **2026-05-22** — ~4 meses sem commits à data desta auditoria, e issue da comunidade (`#4751`, jan/2026) questionando a direção futura do projeto.

| Alegação | Evidência | Validado? |
|---|---|---|
| Edição por diffs estruturados | `aider/coders/`: `editblock_coder.py`, `udiff_coder.py`, `wholefile_coder.py`, `patch_coder.py` — família de estratégias selecionáveis, não uma única | Confirmado, mais rico que a alegação |
| Auto-commit no git | `base_coder.py`: `self.auto_commit(edited)` → `repo.commit(..., aider_edits=True)`, mensagem gerada do histórico da conversa | Confirmado |
| Reflection loop via lint/testes | `reflected_message` populado por lint OU testes, `max_reflections` como teto | Confirmado |
| Repo map por identificadores mencionados | `get_repo_map()` extrai `mentioned_fnames`/`mentioned_idents` da mensagem atual | Confirmado |

**Padrões extraíveis:** família de Coders plugáveis por formato (útil se `desenvolvimento.agent.md` precisar suportar LLMs de capacidades desiguais); reflection loop tipado; auto-commit com proveniência (`aider_edits=True`) — dá um `/undo` grátis, superior ao file-drop atual sem checkpoints git.

**Classificação:** REFERENCE — ideias sólidas, mas atividade recente fraca desaconselha dependência direta.

### 4. browser-use

`browser-use/browser-use`, 115.168★, MIT, push **2026-09-18 (hoje)** — o mais ativo dos quatro.

| Alegação | Evidência | Validado? |
|---|---|---|
| Representa DOM por screenshot | **Refutado**: `dom/serializer/serializer.py`, `DOMTreeSerializer._assign_interactive_indices_and_mark_new_nodes()` — árvore de acessibilidade textual indexada ("set-of-marks": `[42]<button aria-label="Submit" />`), híbrida com screenshot complementar | Confirmado — não é screenshot puro |
| Loop observe→reason→act | `agent/service.py`: `Agent.run()` → `step()` → `_prepare_context()`/`_get_next_action()`+`_execute_actions()`/`_post_process()` | Confirmado |
| Replaneamento por estagnação | `_inject_replan_nudge()` após `consecutive_failures` exceder `max_failures` | Confirmado — análogo ao `StuckDetector` do OpenHands |
| Playwright por baixo | Não confirmado por leitura de `pyproject.toml` nesta fase | **NOT VERIFIED** |

**Padrões extraíveis:** serialização DOM em árvore indexada — referência para qualquer agente do PCU que venha a interagir com UIs web.

**Classificação:** DEFER — arquitetura excelente e projeto muito ativo, mas o PCU não tem hoje nenhum agente que precise de controlar browser.

### 5. Classificação consolidada (Coding/Research Agents)

| Ferramenta | Classificação | Porquê |
|---|---|---|
| OpenHands (app `OpenHands/OpenHands`) | **REJECT** como fonte de padrões de loop | Já não implementa o loop — é app de controlo |
| OpenHands (`software-agent-sdk`) | **EXTRACT** | Jovem (~1 ano, 1,1k★), issue de resume conhecida — extrair padrões, não a dependência |
| SWE-agent | **ADAPT** | Evidência empírica forte, código isolável, atividade real |
| Aider | **REFERENCE** | Bom desenho, mas 4 meses sem commit + pergunta pública sobre futuro do projeto |
| browser-use | **DEFER** | Sem caso de uso atual no PCU |

**O que NÃO adotar:** Docker por omissão como requisito rígido (nem OpenHands SDK nem SWE-agent impõem isso incondicionalmente); Aider como motor de edição em produção; browser-use sem necessidade demonstrada; e — o achado mais importante desta parte — **não tratar contagem de estrelas do repo "principal" como proxy de maturidade do componente que interessa**, sem verificar que o código relevante ainda vive lá.

---

## Parte B — Agentes Especializados por Domínio (2.15)

### 1. Achado interno: a lacuna Agent × Profile ainda não foi implementada

`config/agents.config.ts` foi verificado directamente nesta auditoria: **24 agentes**, numa lista plana (`layer: meta|horizontal|vertical`, `domain`, `description`) — **sem nenhum campo `profile`**. Isto confirma, em código, o diagnóstico já feito na revisão da proposta de arquitetura discutida no início desta auditoria: a recomendação central ("transformar tecnologias/especialidades/jurisdições em perfis configuráveis de um agente, em vez de multiplicar agentes") ainda não tem nenhuma implementação — nem parcial — neste repo.

Isto cruza directamente com `MCP-MAPPING.md` (já produzido antes desta auditoria): os 33 agentes do `agent-network-mcp` já foram categorizados por amplitude/privacidade/origem, e 17 técnicas presas dentro de agentes verticais já foram identificadas como extraíveis para 16 skills horizontais — ou seja, **o instinto certo (extrair o genérico do específico) já foi aplicado uma vez, manualmente, num exercício de migração**, mas não foi formalizado como mecanismo reutilizável (schema `AgentConfig` com `profile`).

### 2. O que os 14 frameworks/protocolos já auditados (Fases 1-4) dizem sobre isto

Vários padrões já encontrados apontam directamente para a mesma solução, de fontes independentes:

- **O27** (Google ADK): taxonomia Sequential/Parallel/Loop + Agent-as-Tool — vocabulário para compor variações sem multiplicar classes de agente.
- **Google ADK, `models/`**: um adaptador nativo (provider principal) + um genérico (LiteLLM-like) para o resto — o mesmo princípio de "um agente, várias configurações" aplicado a modelos, não a domínios, mas o mesmo padrão de desenho.
- **DSPy `Signature`** (O46): contrato tipado de I/O — se um "Backend Agent" único tiver perfis (`react`, `nextjs`, `flutter`), cada perfil poderia declarar o seu próprio `Signature` sem precisar de uma classe de agente por framework.
- **Aider, família de Coders** (Fase 5): a mesma tecnologia (edição de código) implementada como estratégias plugáveis seleccionáveis por contexto (capacidade do modelo), não como agentes separados por estratégia — é literalmente o padrão "perfil" aplicado a um problema adjacente.

Não há, em nenhum dos 14+ projectos auditados até agora, um exemplo de "1 agente por tecnologia/jurisdição/especialidade" tratado como boa prática — pelo contrário, cada framework maduro converge para composição via configuração (profiles, taxonomies, adaptadores), não para multiplicação de classes.

### 3. Recomendação, sem redesenhar a arquitetura (fora do âmbito desta auditoria)

Esta auditoria não decide a arquitetura — só descobre e classifica. O que fica registado como achado accionável, para decisão humana:

1. **`AgentConfig` (schema TS) precisaria de um campo `profile`/`profiles`** para materializar a recomendação já aceite na discussão inicial, sem o que os próximos agentes continuarão a ser adicionados 1-a-1 à lista plana de 24.
2. **O exercício já feito em `MCP-MAPPING.md`** (33→categorias→17 técnicas→16 skills) é o precedente real e local de como fazer essa extração — vale usar como método, não repetir a pesquisa externa.
3. Nenhuma ferramenta externa "resolve" isto — é uma decisão de schema interno, não uma adopção.

**Classificação:** BUILD (schema `profile` em `AgentConfig`) — não há nada para adoptar externamente aqui, o padrão já está confirmado por convergência de 4+ fontes independentes (ADK, DSPy, Aider, e a proposta de arquitetura já discutida); falta só a decisão de implementar.

> **RESOLVIDO PARCIALMENTE em 2026-09-20 (F1).** `profile?: Record<string, unknown>` adicionado a `AgentConfig`/`Agent` (`packages/shared/src/types/agent.ts`); `AgentFactory.registerAgent()` propaga-o; nova função `resolveAgentPrompt(agent, profile)` interpola placeholders `{{chave}}` do `profile` no `systemPrompt` — mesmo agente, saída diferente por perfil, confirmado por teste. **`civil-law-br`/`civil-law-pt` (o caso migrado) NÃO foram fundidos numa única entrada** — descoberta durante a Fase 1 desta execução: 4 ficheiros dependem dos 2 IDs exactos (`SpecialtyManager.ts:78`, `bootstrap.ts:86-87`, `legal-agents.ts:32-33` — que já deriva jurisdição do ID via lookup table — e `check-consistency.ts:295-296`, que valida a string literal `id: 'civil-law-br'`, corrido e confirmado 28/28 OK). Fundir exigiria alterar os 4, fora do escopo deste item. Em vez disso, os 2 IDs foram mantidos e ganharam `profile: {jurisdiction: 'BR'|'PT'}` + um `systemPrompt` template partilhado — a duplicação de free-text desapareceu, a duplicação de registo (2 entradas) fica para uma sessão que também actualize `legal-agents.ts` (poderia ler `profile.jurisdiction` em vez do lookup table). 5 testes novos em `AgentFactory.test.ts`. Ver `EXECUTION-PROMPTS.md` F1.
