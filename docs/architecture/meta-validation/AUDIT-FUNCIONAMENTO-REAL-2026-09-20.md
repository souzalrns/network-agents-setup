# Auditoria de Funcionamento Real — 2026-09-20

**Pergunta que motivou esta auditoria:** dos 3 objectivos originais do setup (memória entre sessões, reconhecimento de agentes, reconhecimento de tools/skills), nenhum funciona na prática — confirmar ou refutar com evidência de código, não de documentação.

**Método:** toda afirmação abaixo tem `ficheiro:linha` real, confirmado por leitura directa ou grep exaustivo nesta sessão (não por citação de documentação anterior). Cruzamentos com `agents-audit/FASE1-AGENTES.md`, `AGENTS.md` (raiz), `docs/architecture/memory/{layers,contracts}.md` assinalados onde aplicável.

---

## PARTE 1 — Memória

### L2 (episodic) — `events.jsonl`

**Quem escreve:** `runner/plan_runner/events.py:14-32` (`EventLog.append()`) — 57 linhas, ficheiro lido por inteiro. Chamado por:
- `engine.py` — 15 sítios (linhas 100,115,125,134,169,180,187,196,221,231,262,271,275,307,312,317)
- `langgraph_engine.py` — 25 sítios (linhas 65,74,81,109,153,157,160,245,268,303,307,331,336,379,393,435,450,486,536,544,556,641,671)
- `knowledge_wiring.py` — 4 sítios (linhas 70,105,118,126)

**Quem lê:** `EventLog.has_event()` (`events.py:34-56`, parse linear letra-a-letra do JSONL, usado internamente pelo próprio `langgraph_engine.py` para evitar duplicar eventos no resume) e `session_search.py` (ver abaixo).

**Como é consultado:** `session_search.py` (novo nesta sessão, item B11/M1) constrói um índice **FTS5 SQLite real** (`build_index()`, não é grep nem parse linear) — mas **grep exaustivo em todo `runner/` confirma zero chamadas a `build_index`/`search` fora do próprio módulo e do seu ficheiro de teste** (`runner/tests/test_session_search.py:7`). Não é importado por `engine.py`, `langgraph_engine.py`, nem `cli.py`.

**Achado adicional (escopo, não só ligação):** mesmo que fosse ligado, `events.jsonl` é **por-run** (`out/events.jsonl`, um ficheiro por execução de plano — `engine.py:99`, `engine.py:213`) — não é um log global partilhado entre sessões/runs. "Pesquisar sessões" com `session_search.py` pesquisa dentro de UM run_dir, não através de todos os runs já feitos.

**B11 (session_search.py) está ligado a algo? Não.** É uma ferramenta CLI standalone (`python -m plan_runner.session_search <run_dir>`), nunca invocada pelo motor.

### L4 (semantic) — contrato `remember`/`recall`/`forget`

Grep exaustivo por `remember|recall|forget` em `runner/` e `packages/`: **zero implementação.** Único hit (`packages/core/src/security/SecurityManager.ts:284`) é uma regex de detecção de prompt injection (`/forget all previous/i`) — não relacionado.

**Existe só como JSON Schema** em `docs/architecture/memory/contracts.md:7-68` (155 linhas, ficheiro lido por inteiro) — `memory.remember`/`memory.recall`/`memory.forget`, puramente conceptual. Nenhum ficheiro `.py`/`.ts` do repo importa, valida contra, ou implementa qualquer destes 3 schemas.

### L5 (knowledge) — RAG

**Está ligado e funciona — com escopo estreito.** `runner/plan_runner/knowledge.py` (124 linhas, lido por inteiro): `retrieve_knowledge()` é **read-only** (protocolo `KnowledgeBackend.retrieve()`), backend por omissão `NullKnowledge` (no-op). `knowledge_wiring.py` (131 linhas, lido por inteiro) usa `McpKnowledge()` como backend real (linha 81) e está genuinamente ligado: `inject_knowledge_context()` é chamado por `engine.py` (linhas 131, 272) e `langgraph_engine.py` (linhas 75, 304, 444) — confirmado por grep, 7 sítios reais de chamada.

**Escrita:** acontece **fora do runtime dos agentes**, via pipeline de ingestão separado (`chunking.py`→`embedder.py`→`supabase_writer.py`, disparado por `ingest-knowledge.yml` no push a `main`, não durante a execução de planos).

**Leitura:** **opt-in por step** — só corre se o `step` tiver um bloco `knowledge:` explícito no `plan.yaml` (achado do B8 desta sessão: só 7 dos 12 templates têm este bloco).

### `working_memory.py`

**Ficheiro lido por inteiro (135 linhas).** Docstring da própria linha 1: *"Working memory (MEMORY.md) por cliente — leitura, sem escrita."* Linha 21: *"Sem escrita, sem LLM, sem dependências novas."* **Confirmado: zero função de escrita existe no ficheiro** — só `read_memory()`/`memory_status()`/`resolve_memory_path()`.

**Quem escreve o `MEMORY.md`:** um humano, por curadoria manual (não há código que gere ou actualize este ficheiro).

**É usado em runtime?** **Não.** Grep exaustivo em `runner/`: só `working_memory.py` (definição) e `test_working_memory.py` (teste isolado) referenciam estas funções — **zero chamadas de `engine.py`, `langgraph_engine.py` ou `cli.py`.** A própria docstring da linha 107 confirma o gap: *"Útil para o engine (S7b) decidir se injecta contexto"* — **S7b (a ligação ao engine) nunca foi feita.**

### CONCLUSÃO — Memória entre sessões

| Camada | Estado | Evidência |
|---|---|---|
| L2 (episodic) | 🟡 Escreve de facto; consulta (FTS5) construída mas **desligada** | `events.py`, `session_search.py` |
| L3 (procedural/skills) | Ver Parte 3 | — |
| L4 (semantic) | ❌ **Zero implementação** — só JSON Schema | `contracts.md` |
| L5 (RAG) | 🟡 Funciona, mas **read-only + opt-in por step**, sem escrita automática pelo agente | `knowledge_wiring.py`, `knowledge.py` |
| Working memory (`MEMORY.md`) | ❌ Código de leitura existe, **nunca chamado pelo motor** | `working_memory.py` |

**Não há nenhum mecanismo real de "memória entre sessões" no sentido em que o utilizador provavelmente pretendia** (um agente lembrar-se de factos/decisões de sessões anteriores e usá-los na sessão seguinte, automaticamente). O que existe:
- Um log de eventos por-execução, com um motor de busca construído mas nunca ligado.
- RAG (L5) real mas estreito — não é "memória", é uma base de conhecimento estática, consultada só quando pedida explicitamente por um step.
- Um ficheiro `MEMORY.md` que um humano pode escrever à mão, mas que o motor nunca lê.

**Classificação: 🟡 PARCIAL, a tender para ❌.** Existem peças reais (L2 write, L5 retrieve) mas nenhuma delas implementa "lembrar entre sessões" — e as duas peças mais próximas disso (`session_search.py`, `working_memory.py`) estão ambas desligadas do motor.

---

## PARTE 2 — Reconhecimento de agentes

**`config/agents.config.ts` — como é lido em runtime:** `packages/scripts/src/bootstrap.ts:45` chama `agentFactory.registerAgent()` por cada entrada (confirmado por grep) — carregamento acontece **uma vez, no arranque do processo**.

**`AgentFactory.ts` (57 linhas, lido por inteiro) — registry é `Map<string, Agent>` (linha 3), 100% em memória (volátil), não persistido.**

**Um agente sabe quais outros agentes existem?** Métodos `getAgent()`/`getAllAgents()`/`getAgentsByDomain()`/`getAgentsByLayer()`/`getAgentsByVisibility()` existem (linhas 25-39) — mas grep exaustivo em `packages/` confirma que só são chamados por:
- `Orchestrator.ts:297` — decide **routing antes de invocar o agente**
- `Executor.ts:154` — resolve o agente já atribuído a um step **pelo planner**, não pelo agente
- `MultiAgentGraph.ts:21,92` (pacote `langgraph`) — mesmo padrão de orquestração
- `bootstrap.ts:45`, `check-completeness.ts:34`, `ingest/index.ts:108` — scripts de build/contagem, não runtime de agente

**Nenhuma chamada a estes métodos parte de dentro da execução do próprio agente (o seu `systemPrompt`/LLM não tem acesso a isto).**

**Pode "pedir" por outro em runtime?** Não há `getAgent`/`discover` chamado a partir de qualquer lógica de LLM-tool-calling. `packages/mcp` (grep exaustivo): **zero tool `list_agents`.**

**O MCP expõe "list agents"?** Existe `GET /agents`, `GET /agents/:id`, `GET /agents/domain/:domain` em `apps/api/src/routes/agents.ts:7-9` (4 linhas relevantes) — mas isto é um **endpoint HTTP para um cliente externo** (dashboard/humano), gated por `authMiddleware` (API key), **não uma tool que o próprio agente chama a meio da sua execução.**

**Cross-referência (REGRA 3):** `AGENTS.md` (raiz, 46 linhas, lido por inteiro), linha 15, a própria regra do projecto: *"Personas **não** invocam outras personas; só o plan / meta-skill / humano orquestra."* — confirma que isto é **desenho deliberado**, não uma falha esquecida.

### CONCLUSÃO — Reconhecimento de agentes

**Um agente NÃO pode descobrir outros agentes em runtime.** Só o Orchestrator (uma camada acima, fora do próprio agente) tem essa visibilidade, e usa-a **antes** de invocar um agente para decidir routing — nunca como algo que o agente em execução possa consultar. Isto é uma decisão de arquitectura explícita (documentada em `AGENTS.md`), não um bug — mas significa que "reconhecimento de agentes" no sentido de auto-descoberta entre pares **não existe e nunca foi suposto existir**, segundo a própria documentação do repo.

**Classificação: ❌ NÃO FUNCIONA** (como auto-descoberta pelo agente) — o registry em si funciona bem para o propósito interno do Orchestrator, mas isso é um mecanismo de *orquestração centralizada*, não de *reconhecimento entre agentes*.

---

## PARTE 3 — Reconhecimento de tools e skills

### Tools

**`ToolRegistry.ts` (43 linhas, lido por inteiro):** `Map<string, MCPTool>` em memória (linha 17). `getToolsForLLM()` (linha 33-42) converte para o formato de function-calling da OpenAI — **mecanismo real**, mas só é útil se for de facto passado a uma chamada de LLM.

**Descoberta em runtime ou hardcoded?** `MCPServer.getToolsForLLM()` (linha 29-30) re-expõe o método — mas **`MCPServer` nunca é montado em `apps/api` nem em lado nenhum** (confirmado na sessão anterior, achado A8/S11: grep repo-wide, único resultado é a própria definição). Grep exaustivo em `Executor.ts` por `ToolRegistry|ToolExecutor|MCPServer|MCPClient|chatWithTools`: **zero resultados.**

**`LLMService.chatWithTools()` existe** (`LLMService.ts:61-70`, implementado) **mas nunca é chamado** — `Executor.ts:161` e `Planner.ts:54` chamam só `this.llm.chat({...})`, o método simples sem tools (confirmado por grep, único padrão de chamada nos dois ficheiros).

**Tool MCP "list_templates" existe?** Sim, real — `mcp/plan_runner/mcp_plan_runner/tools_impl.py:20-33` (14 linhas) — mas lista **planos** (`docs/orchestration/**/*.plan.yaml`), não tools nem skills.

**Conclusão tools:** o subsistema inteiro de tools (`ToolRegistry`/`ToolExecutor`/`MCPServer`/`MCPClient`/`ToolPolicy`, incluindo a autenticação e propagação de `caller` implementadas na tarefa anterior desta sessão, A8/S11) está **completamente desligado do pipeline real de execução de agentes** (`Orchestrator→Router→Planner→Executor`). Um agente, tal como corre hoje em produção, **não tem nenhuma tool disponível** — as 6 tools reais (`read_file`/`write_file`/`list_directory`/`http_request`/`scrape_webpage`/`query_database`) existem, são testadas, mas nunca chegam a um LLM real via `chatWithTools()`.

### Skills

**`skills.py` (27 linhas, lido por inteiro):** `resolve_skill_path(repo_root, action, vertical="marketing")` — **resolução determinística de path**, não descoberta: exige o `action` exacto já conhecido, sem pesquisa/matching algum.

**Achado crítico, não pedido explicitamente mas confirmado com evidência concreta de bug ao vivo:** `executor.py:67-68` chama `resolve_skill_path(repo_root, step.action)` **sem o 3º argumento** — logo `vertical` é **sempre** `"marketing"`, para **qualquer** step de **qualquer** plano. Confirmado que isto quebra planos reais: `design-flow-demo.plan.yaml` tem steps com `action: ux_flow`/`ui_spec`/`ux_writing`/`design_critic`, que só existem em `skills/design/*/SKILL.md` — **não** em `skills/marketing/*/SKILL.md`. Para estes planos, `resolve_skill_path()` devolve sempre `None`, `req["skill_path"]` fica `null`, e `pending_steps/<id>/SKILL.md` **nunca é escrito.** Nenhum teste apanha isto — `test_skills.py` só testa com fixtures `tmp_path` isoladas, nunca contra a árvore real de `skills/` com um vertical não-marketing.

**Como um agente sabe "qual skill usar para X"?** `skills/meta/using-agent-skills/SKILL.md` (86 linhas, lido por inteiro) é a peça mais próxima de descoberta — mas a própria skill se auto-declara **Advisory** (linha 69): *"Nada impede um agente de ignorar o mapa de invocação e activar skills directamente."* É uma convenção em Markdown para um humano/sessão Claude-no-IDE ler manualmente e decidir — **zero código a executa ou a impõe.**

**Progressive disclosure está implementada?** Não há nenhum catálogo gerado de skills (`docs/generated/` só tem `AGENTS.md` e `CODE_MAP.md`, nenhum `SKILLS.md`). A "descoberta" descrita em `using-agent-skills` (ler `frontmatter` de todas as `SKILL.md` para montar um catálogo leve antes de carregar o corpo completo) é uma instrução em prosa para um leitor humano/Claude — não há parser de frontmatter em código algum.

### CONCLUSÃO — Reconhecimento de tools e skills

**Um agente não pode descobrir qual tool/skill usar em runtime, por 2 razões distintas e sobrepostas:**
1. **Tools:** o mecanismo de function-calling existe em código mas nunca é activado (`chatWithTools()` nunca chamado).
2. **Skills:** a resolução é determinística e hardcoded a um único vertical (`"marketing"`) — quebra silenciosamente para qualquer outro domínio — e a única "descoberta" real é uma convenção Markdown para humanos, sem imposição em código.

**Classificação: ❌ NÃO FUNCIONA** (tools) / 🟡 **PARCIAL a tender para ❌** (skills — resolve por path fixo quando o `action`/vertical já é conhecido de antemão, mas não há descoberta nem generalização além de `"marketing"`).

---

## PARTE 4 — Síntese

| Objectivo | Classificação | Gap exacto |
|---|---|---|
| **1. Memória entre sessões** | 🟡 PARCIAL → ❌ | L4 (semântica) é só schema; L2 tem busca construída (`session_search.py`) mas nunca ligada; `working_memory.py` é read-only e nunca chamado pelo motor (S7b nunca feito); só L5 (RAG) funciona de facto, mas é conhecimento estático opt-in, não "memória" no sentido de recordar decisões/factos entre sessões |
| **2. Reconhecimento de agentes** | ❌ NÃO FUNCIONA | Registry existe e funciona bem — mas só para o Orchestrator decidir routing **antes** de invocar o agente. Nenhum agente, a correr, pode consultar quem mais existe. Confirmado como desenho deliberado (`AGENTS.md:15`), não descuido |
| **3. Reconhecimento de tools/skills** | ❌ NÃO FUNCIONA | Tools: mecanismo de function-calling construído, nunca activado (`Executor`/`Planner` só chamam `.chat()`, nunca `.chatWithTools()`). Skills: resolução por path fixo a um único vertical hardcoded (bug real, confirmado a quebrar `design-flow-demo.plan.yaml`); "descoberta" é só uma convenção Markdown advisory, sem imposição em código |

**O padrão transversal (o mesmo desta sessão inteira, repetido pela 6ª ou 7ª vez em auditorias diferentes): peças bem construídas, algumas até testadas, que nunca foram ligadas ao pipeline real de execução.** Não é falta de código — é falta de fiação (wiring) entre subsistemas que foram claramente desenhados para se encaixar (os nomes/comentários no código citam-se uns aos outros: `knowledge_wiring.py` cita S9/S10, `working_memory.py` cita S7b, `ToolRegistry.getToolsForLLM()` foi claramente pensado para `LLMService.chatWithTools()`) mas cujo último passo — a chamada real, no sítio real — nunca foi dado.

---

## Sobre a proposta do DeepSeek Harness (DSH) / `dsh-long-memory`

Pergunta levantada a meio desta auditoria: já que esta auditoria confirma o gap de L4, porque não adoptar a infra do DSH (via Oracle Free Tier) para resolver tudo de uma vez?

**Esta auditoria não investigou o DSH** (fora do âmbito pedido — só código deste repo). Mas com o gap agora confirmado com evidência directa, a pergunta é legítima e a `FASE4-SINTESE.md` já tinha uma posição registada: *"`dsh-long-memory` é um plugin do DeepSeek Harness, não uma biblioteca instalável aqui — adoptar significaria reescrever o padrão em Python, não `npm install`."* As 3 opções já foram esboçadas (A: adoptar o DSH inteiro; B: extrair só os padrões para Python; C: DSH só como servidor de memória via MCP) — nenhuma foi executada nesta sessão, por ser uma decisão de arquitectura fora do escopo de "investigar e reportar" pedido aqui.

**Recomendação, dado o que esta auditoria confirmou:** antes de decidir entre A/B/C, vale considerar uma 4ª opção mais barata — **fechar os gaps de fiação já identificados nesta auditoria** (S30, S31, S33, S34 abaixo) primeiro, porque nenhum deles precisa de infra nova nem do DSH. Isso já resolveria uma fatia real dos 3 objectivos (L2 pesquisável, `MEMORY.md` a ser lido de facto, tools acessíveis a um agente, skills a resolver correctamente fora de marketing) sem gastar os 1-3 dias de qualquer opção do DSH. **A decisão sobre L4 completo (semântica, o que o DSH resolveria melhor) é a única peça que continua a justificar a Oracle/DSH — o resto é wiring, não infra.**

---

## Itens novos registados (ver `STATUS.md`)

- **S29** — L4 (memória semântica) sem implementação — só schema em `contracts.md`
- **S30** — `working_memory.py` nunca ligado ao motor (S7b nunca feito) — read-only, código pronto, falta a chamada
- **S31** — `session_search.py` (B11/M1) nunca ligado ao motor nem a nenhuma tool MCP — CLI standalone órfã
- **S32** — Reconhecimento de agentes entre pares não existe, por desenho (`AGENTS.md:15`) — registado como decisão a confirmar/reconsiderar, não bug
- **S33** — Tools (`ToolRegistry`/`ToolExecutor`) nunca chegam a um LLM real — `chatWithTools()` nunca chamado por `Executor.ts`/`Planner.ts`
- **S34** — **Bug real confirmado:** `resolve_skill_path()` chamado sempre com `vertical="marketing"` hardcoded em `executor.py:67` — quebra silenciosamente a resolução de skills para `design-flow-demo.plan.yaml` e qualquer outro plano fora do vertical marketing
- **S35** — Nenhum catálogo de skills gerado (`docs/generated/SKILLS.md` não existe) — descoberta de skills é só uma convenção Markdown advisory (`using-agent-skills`), sem imposição em código
