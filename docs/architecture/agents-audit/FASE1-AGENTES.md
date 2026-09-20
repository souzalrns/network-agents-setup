> **⚠️ ERRATA (2026-09-19):** a secção 1a abaixo, e a secção 4, afirmam que `orchestrator/Orchestrator.ts` é MOCK e que Router/Planner/Executor estão "reais mas desligados". **Isto está errado** — confirmado por leitura completa do ficheiro em `orchestration-audit/AUDIT-ORCHESTRATION.md`: `Orchestrator.ts` liga as três peças de facto, num pipeline real de 14 passos, e há um entry point real (`apps/api/src/index.ts`) que o instancia por completo. O erro veio de citar `CORE-MAPPING.md` sem reverificar. Ver `orchestration-audit/AUDIT-ORCHESTRATION.md` secção 0 para a cadeia completa do erro. O texto original fica abaixo, sem alteração, para preservar o registo do que foi dito e quando.

# Auditoria de Agentes — Fase 1: Agent Frameworks, Multi-Agent Architectures, Runtime/Execution, Planning

Primeira fase da auditoria profunda do ecossistema de agentes, com a mesma disciplina das auditorias de governança (`governance/audit/GOV-FASE1.md`) e memória (`memory/FASE1-MEMORIA.md`): **README serve para descoberta, código é a evidência**. Nenhuma alegação de maturidade, arquitetura ou capacidade foi aceite sem verificação directa — de código-fonte deste repo, de código-fonte dos projectos externos, de issues reais, ou de GitHub API.

## 0. Escopo desta fase e o que já existia

Antes de pesquisar qualquer framework externo, esta fase auditou primeiro **o próprio repositório** (secção 1) — exactamente como `GOV-FASE1.md` mapeou `packages/core/`+`packages/mcp/` antes de avaliar AGT/ContextForge, e como `FASE1-MEMORIA.md` mapeou as 7 camadas de memória antes de avaliar Graphiti/Cognee. Só depois disso é que os 6 frameworks novos (secção 2) foram comparados contra essa base real, não contra uma descrição abstracta de "o nosso runtime Plan-Execute".

`docs/architecture/patterns-from-orchestrators/` já cobre, com o mesmo rigor, 8 frameworks (LangGraph, Agno, Timbal, CrewAI, PydanticAI, Mastra, AG2, Haystack), 18 padrões extraídos (O01–O18). **Não foi refeito.** O que faltava, contra o espectro pedido (secções 2.1–2.4 da auditoria: Agent Frameworks, Multi-Agent Architectures, Runtime/Execution Engine, Planning), eram os frameworks mais recentes que ninguém tinha auditado: Microsoft Agent Framework, Google ADK, OpenAI Agents SDK, LlamaIndex, DSPy, smolagents. Letta/Mem0/Zep/Graphiti/Cognee/LightRAG/Hindsight/MELD/Stigmem ficam fora — já cobertos na auditoria de Memória.

## 1. Achado prévio, decisivo para tudo o resto: o que este repo já tem, verificado por código

Este repo **não tem um runtime de agentes** — tem **dois**, em stacks diferentes, com maturidades e paradigmas de planeamento opostos, e nenhum documento produzido até agora (`ECOSYSTEM.md`, `ADR-001`, `CORE-MAPPING.md`) os descreve lado a lado como a mesma responsabilidade. Isto é o equivalente, no domínio de Agentes, ao achado da Fase 1 de Governança sobre `packages/mcp/` vs `mcp/plan_runner/policy.py` — a mesma classe de duplicação estrutural, desta vez entre **planeamento+execução**, não entre **autorização de tools**.

### 1a. TypeScript — `packages/core/src/orchestrator/` + `agents/`

Classificação confirmada em `CORE-MAPPING.md` (produzido 2026-09-18, reconfirmado por leitura directa nesta fase):

| Ficheiro | Estado | O que faz de facto |
|---|---|---|
| `orchestrator/Router.ts` | **REAL** | Classificador de domínio por palavra-chave, autocontido |
| `orchestrator/Planner.ts` | **REAL** | Chama `LLMService.chat()` de facto — prompt pede ao LLM para escolher agentes de uma lista, decompor em passos com `agentId`+`prompt`+`requiresApproval`+`critical`, devolver JSON; `validatePlan()` rejeita `agentId` fora da lista disponível; `fallbackPlan()` determinístico (1 passo, agente por omissão) se o parse falhar |
| `orchestrator/Executor.ts` | **REAL** | Não guarda estado próprio — delega a `MemoryManager`, `LLMService`, `HitlManager` injectados |
| `orchestrator/Orchestrator.ts` | **MOCK** | É a peça que devia ligar Router→Planner→Executor — **não o faz**. As 3 peças reais existem isoladas, sem o componente de topo que as coordena estar implementado |
| `orchestrator/DeliberationOrchestrator.ts` | INCOMPLETO | Resultados em `Map` (não persiste); usa o `DeliberationEngine` (REAL) por baixo |
| `orchestrator/ReflectionEngine.ts` | INCOMPLETO | Reflexões pós-execução em `Map` — existe a *noção* de reflexão/replaneamento, mas sem persistência nem gatilho automático confirmado |
| `agents/AgentFactory.ts` | INCOMPLETO | Regista/filtra agentes num `Map` único, sem persistência |
| `agents/HorizontalAgents.ts` | **MOCK** | — |

**O que isto significa, sem meias palavras:** há um planeador que chama LLM de verdade e escolhe agentes por conta própria (`Planner.ts`) — exactamente o tipo de "planning explícito" que se foi procurar nos 6 frameworks externos desta fase — mas **não há nada que o invoque em produção**, porque o `Orchestrator.ts` que devia chamar Router→Planner→Executor em sequência é MOCK. É uma peça de motor real, desligada da transmissão.

### 1b. Python — `runner/plan_runner/` (o "Lab Plan-Execute runner", confirmado no próprio `--help` da CLI)

Lido directamente (`models.py`, `graph.py`, `engine.py`, `executor.py`, `cli.py`, `langgraph_engine.py`, `hitl.py`) — não inferido de documentação:

| Capacidade | Estado real | Evidência |
|---|---|---|
| Definição de plano | `Plan`/`Step` dataclasses, `depends_on`, `tools_allowed`, `output_schema`, `human_gate` por passo | `models.py` |
| Geração do plano | **Não há LLM aqui** — o plano é um `plan.yaml` escrito externamente (por humano ou por uma sessão Claude) e só depois carregado | `engine.py:load_plan` |
| Ordenação/paralelismo (motor "native", por omissão) | Topological sort simples, execução **sequencial mesmo quando os passos são independentes** | `graph.py:topo_order` — não agrupa por "waves" |
| Ordenação/paralelismo (motor "langgraph", opt-in via `--engine langgraph`) | **Execução em ondas paralelas real** (`parallel_groups`) + fallback sem LangGraph instalado | `langgraph_engine.py`, `langgraph_compile.py` |
| Checkpoint | **Ausente no motor "native"** (só `status.json` + `events.jsonl`); **real no motor "langgraph"** via `SqliteSaver` do próprio LangGraph (`checkpoints.db`) — é o padrão O03 de `patterns-from-orchestrators/README.md` **já implementado em código real**, não só "a estudar" | `langgraph_engine.py:213-216` |
| Budget de passos | `budget_max_steps` — **imposto de facto**, aborta o run com `plan_aborted`/`aborted_budget` | `engine.py:113-117` |
| Budget de replaneamento | `budget_max_replans` **existe no schema do plano e nunca é lido em nenhum motor** — campo morto, sem nenhuma lógica de replaneamento em lado nenhum do `runner/plan_runner/` | Confirmado por busca: zero ocorrências de `budget_max_replans` fora de `models.py` |
| HITL — approve/reject | Implementado nos dois motores | `engine.py:resume_run`, `langgraph_engine.py:resume_plan_langgraph` |
| HITL — **edit** | **Aceite mas sem efeito real no motor "native"** (`edit` cai no mesmo ramo que `approve`, sem aplicar nenhum payload); **implementado de facto só no motor "langgraph"**, via `--payload-file` (`resume_value = {"decision": "edit", "payload": ...}`, escreve o `output_artifact` com o conteúdo editado) | `engine.py:218-243` vs `langgraph_engine.py:591-595` |
| Execução de um passo ("stub") | Escreve um artefacto placeholder, nunca chama LLM/agente nenhum | `executor.py:execute_stub` |
| Execução de um passo ("external") | **Não é execução automática** — escreve `request.json` (com `agent_path`+`skill_path` resolvidos) numa pasta `pending_steps/<step_id>/` e **espera que apareça um `result.json`** escrito por outro processo (humano ou outra sessão Claude a "carregar o agente e a skill e executar manualmente") | `executor.py:execute_external_request` |
| HITL — contrato partilhado com o lado Node | `hitl-requests.jsonl`/`hitl-decisions.jsonl`, schema `hitl-request-v1.json`, aditivo (não substitui `status.json`/`events.jsonl`) | `hitl.py` |
| Multi-agente / handoff / delegação entre agentes | **Ausente por completo** — não há nenhuma noção de um agente invocar outro; a "execução" de um passo é sempre um humano/Claude a resolver `pending_steps/` manualmente | Confirmado por leitura de `executor.py`/`engine.py`/`langgraph_engine.py` inteiros |

### 1c. O que isto muda para o resto desta auditoria

1. **"Planning explícito" já existe neste repo — do lado TypeScript (`Planner.ts`), não do Python.** Isto inverte a leitura ingénua de que "planning é uma lacuna a preencher com um framework externo": a peça já foi escrita, com o padrão certo (LLM escolhe agentes + fallback determinístico), só não está ligada a nada.
2. **Checkpoint (O03) e execução paralela por ondas já são código real** no motor `langgraph`, não hipótese de "lab futuro" como `patterns-from-orchestrators/README.md` sugeria ("Optional: um de {LangGraph, Agno, Timbal} isolado" — já deixou de ser opcional/futuro, já está escrito, só não é o motor por omissão da CLI).
3. **"Multi-agente" neste repo hoje é, na prática, um humano ou uma sessão Claude a servir de executor manual** via o padrão `pending_steps/request.json` → `result.json`. Nenhum dos 6 frameworks auditados na secção 2 resolve isto por si (todos assumem que quem chama a tool/agente é o próprio runtime, em processo) — mas vários (O20 ADK, O33 OpenAI SDK handoff, O40 LlamaIndex handoff-como-tool) mostram como formalizar essa fronteira humano↔agente↔agente de forma mais rica do que "esperar um ficheiro aparecer".
4. **`budget_max_replans` é um campo morto** — mesma classe de achado que `Competence.status: 'revoked'` sem mecanismo activo, encontrado na auditoria de governança. Se algum dia se quiser replaneamento real, o padrão mais próximo e concreto encontrado nesta fase é o **O21 (Magentic Task Ledger + Progress Ledger)** do Microsoft Agent Framework — não há nada a "ligar" aqui, é preciso construir.
5. **A dualidade TS/Python não é acidental nem recente** — é a mesma classe de achado do `GOV-FASE1.md` (`packages/mcp/` TS vs `mcp/plan_runner/` Python), agora confirmada também na camada de planeamento/execução, não só na de autorização de tools. Fica reforçada a recomendação já registada lá: decidir qual stack é "a" definitiva antes de investir mais em qualquer uma das duas, não depois.

## 2. Os 6 frameworks novos — resumo

Detalhe completo por framework (tabela de evidência linha a linha, todos os links de origem) em `deep/*.md`.

| Framework | Repo | Estrelas | Última atividade | Classificação | Achado principal |
|---|---|---|---|---|---|
| [Microsoft Agent Framework](./deep/microsoft-agent-framework.md) | `microsoft/agent-framework` | 13.584 | 2026-09-18 | **EXTRACT + REFERENCE** | Sucessor real de AutoGen+Semantic Kernel (ambos em manutenção); alegação de checkpoint "durável" é falsa (sem lease/lock, crítica técnica independente confirmada) e "API 1.0 estável" contradita por commits `[BREAKING]` no próprio dia da auditoria |
| [Google ADK](./deep/google-adk.md) | `google/adk-python` | 21.600 | 2026-09-10 | **EXTRACT** | Framework completo e maduro (usado pela Gemini Enterprise Agent Platform), mas o próprio HITL de referência da Google teve um bug de enforcement (recusa não bloqueava a tool até PR recente) — mesma classe de falha que o nosso `HitlManager.ts` tem hoje |
| [OpenAI Agents SDK](./deep/openai-agents-sdk.md) | `openai/openai-agents-python` | 29.552 | 2026-09-17 | **EXTRACT** | Sucessor de produção do Swarm; handoff e guardrail-por-tool são contratos limpos e extraíveis; tracing envia para a OpenAI por omissão (opt-out, não opt-in) — risco a não copiar |
| [LlamaIndex (agentes/workflows)](./deep/llamaindex-agents.md) | `run-llama/llama_index` + `run-llama/llama-agents` | 52.214 (núcleo) / 450 (camada de deploy) | 2026-09-18 | **EXTRACT** | O projeto reposicionou-se publicamente como "document processing platform"; a camada de orquestração/deploy já mudou de nome/arquitetura 3 vezes em ~2 anos |
| [DSPy](./deep/dspy.md) | `stanfordnlp/dspy` | 38.121 | 2026-09-18 | **EXTRACT** (técnica de otimização, não o framework) | Não é orquestrador de agentes — é otimização declarativa de prompts. O valor real está no `BootstrapFewShot`/MIPROv2, aplicável directamente aos nossos próprios agentes |
| [smolagents](./deep/smolagents.md) | `huggingface/smolagents` | 29.390 | 2026-08-25 | **EXTRACT** | `CodeAgent` é real e bem desenhado, mas o próprio projeto admite por escrito que o executor local **não é fronteira de segurança** |

**Nenhum dos 6 foi classificado ADOPT ou ADAPT.** Todos são frameworks completos e opinativos, cada um pensado para ser o runtime inteiro de quem os adota — e o repo já tem dois runtimes próprios (secção 1), incompletos mas reais, com decisões de arquitetura já tomadas (Plan-Execute, MCP produção Python). O valor extraído está em padrões e contratos específicos, não nos frameworks como dependência.

## 3. Padrões unificados novos (O26–O58)

Continuando a numeração de `patterns-from-orchestrators/README.md` (O01–O18) e do Microsoft Agent Framework (O19–O25, ver `deep/microsoft-agent-framework.md`):

| ID | Padrão | Origem | Onde no nosso setup |
|---|---|---|---|
| O26 | `ToolConfirmation` — decisão do humano como objeto tipado, interceptado no boundary antes de chamar a tool | Google ADK | `HitlManager.ts` / `ToolExecutor.executeTool()` (TS) |
| O27 | Taxonomia Sequential/Parallel/Loop + Agent-as-Tool | Google ADK | Vocabulário para sub-planos no Plan-Execute (ambos os motores) |
| O28 | Runner síncrono/assíncrono/live com cancelamento gracioso por task de fundo | Google ADK | `runner/plan_runner/` (Python) |
| O29 | Resume por `invocation_id` sobre eventos append-only | Google ADK | `events.py` já é append-only; falta o índice por invocation |
| O30 | `BasePlanner` com implementações intercambiáveis | Google ADK | Interface para o `Planner.ts` (TS) ter mais de um mecanismo de decomposição |
| O31 | Nós de grafo tipados (function/tool/join) + política de retry separada do estado | Google ADK | Vocabulário para `langgraph_compile.py` |
| O32 | Adaptador multi-LLM nativo (provider principal) + genérico para o resto | Google ADK | Camada de modelos |
| O33 | `Handoff` como objeto tipado com `input_filter` e `is_enabled` dinâmico | OpenAI Agents SDK | Formaliza o `pending_steps/request.json` → `result.json` (secção 1b) como objeto de primeira classe em vez de convenção de ficheiro |
| O34 | Guardrail com 3 comportamentos (`allow`/`reject_content`/`raise_exception`) | OpenAI Agents SDK | `ToolExecutor.executeTool()` — verificação de capacidade/scope (`GOV-FASE1.md`) |
| O35 | `RunState` serializável (turno + aprovações pendentes) para resume com HITL | OpenAI Agents SDK | Unificar `status.json`+`hitl-requests.jsonl` num único estado resumível |
| O36 | Exportador de tracing plugável com fallback console | OpenAI Agents SDK | Observability ausente em TS (`GOV-FASE1.md`) |
| O37 | Orquestração como receita de aplicação, não componente de runtime obrigatório | OpenAI Agents SDK | Confirma: não falta "motor de orquestração" — falta ligar `Orchestrator.ts` (MOCK) às 3 peças já REAL |
| O38 | `ModelRetryBackoffSettings` | OpenAI Agents SDK | `mcp/plan_runner/policy.py` |
| O39 | SECURITY.md com "Scope" + "Trust boundaries" + exclusões explícitas | OpenAI Agents SDK | Reforçar SECURITY.md próprio |
| O40 | Handoff-como-tool-dinâmica com allow-list (`can_handoff_to`) | LlamaIndex | Delegation Graph (gap de `GOV-FASE1.md`); mesmo problema de fundo do O33 |
| O41 | Checkpoint de `Context` via `to_dict()`/`from_dict()` | LlamaIndex | Segundo ponto de dados independente a favor do padrão já implementado (O03) no motor `langgraph` |
| O42 | `wait_for_event` com `waiter_id` — **e o aviso**: replay do step inteiro exige idempotência | LlamaIndex | Cuidado a aplicar ao decidir tornar o motor "native" resumível como o "langgraph" já é |
| O43 | Retry policy composable estilo `tenacity` | LlamaIndex | `packages/core/` TS |
| O44 | Routing de eventos por assinatura de tipos (fan-in/fan-out tipado) | LlamaIndex | Contratos tipados entre passos |
| O45 | SECURITY.md com âmbito de bounty nomeado e exclusões explícitas | LlamaIndex | Idem O39 |
| O46 | `Signature` — contrato tipado de I/O de prompt | DSPy | O próprio prompt de `Planner.ts` (secção 1a) é uma string livre — poderia ganhar este contrato |
| O47 | Composição de módulos por reflexão de atributos | DSPy | Descoberta de sub-componentes otimizáveis |
| O48 | **`BootstrapFewShot`** — gerar traces reais do próprio agente, filtrar por métrica, usar como few-shot | DSPy | **Candidato de maior valor desta fase** — `events.jsonl` (Python) e o histórico de decisões do `Planner.ts` (TS) já são a matéria-prima, falta só a métrica de sucesso e o filtro |
| O49 | Otimização Bayesiana de instruções com orçamento declarado (MIPROv2) | DSPy | Auto-tuning de prompts, se/quando o custo se justificar |
| O50 | Truncamento de trajetória em blocos, com nº máximo de tentativas | DSPy | Útil se `Planner.ts` vier a manter histórico de tentativas |
| O51 | Serialização seletiva de estado (separar "optimizado" de "ruído de execução") | DSPy | Formato de artefactos de configuração de agente |
| O52 | Custo de otimização declarado explicitamente antes de correr | DSPy | Qualquer processo de auto-tuning contra LLM de produção |
| O53 | Interpretador Python por AST-whitelist (não blacklist) | smolagents | Só relevante se algum passo vier a executar código gerado por LLM directamente (hoje não acontece — `execute_stub`/`execute_external_request` não avaliam código) |
| O54 | Abstração plugável de executores (local/E2B/Docker/Modal) | smolagents | Generalização possível de `execute_stub`/`execute_external_request` para um 3º modo "sandboxed" |
| O55 | `managed_agents`-como-tool | smolagents | Mesmo problema de fundo do O33/O40 — formalizar handoff |
| O56 | Planning periódico com replaneamento (`planning_interval`) | smolagents | Candidato concreto para preencher o campo morto `budget_max_replans` (secção 1b) |
| O57 | Declaração explícita de fronteira de confiança no SECURITY.md | smolagents | `packages/mcp/ToolExecutor.ts` — hoje ambíguo |
| O58 | `final_answer_checks` | smolagents | Gate barato no Plan-Execute, qualquer motor |

## 4. Cruzamento com as lacunas já identificadas (`GOV-FASE1.md`) e achados desta fase

- **O bug de HITL do Google ADK (recusa não imposta) é o mesmo tipo de risco que o `HitlManager.ts` (TS) tem hoje** (`GOV-FASE1.md`) — mas esta fase encontrou um paralelo mais próximo ainda: o **motor "native" do `plan_runner` aceita a decisão `edit` sem lhe dar efeito real** (secção 1b). Não é um bug reportado por terceiros — é um achado directo desta auditoria, no próprio código deste repo.
- **Nenhum dos 6 frameworks resolve checkpoint distribuído/durável de verdade** (nem o Microsoft Agent Framework, cujo próprio maintainer admite que "distributed agent runtime" ainda não existe). Isto é irrelevante para o motor "langgraph" do `plan_runner` hoje — que já tem checkpoint via `SqliteSaver`, mas **local, não distribuído** (o mesmo tipo de limitação, num alcance menor).
- **O padrão de maior valor novo desta fase (O48, `BootstrapFewShot`) não veio de nenhum orquestrador** — veio do DSPy, um projeto ortogonal, e aplica-se directamente ao `events.jsonl` que já existe.
- **A maior lacuna não é técnica, é de fiação**: `Planner.ts` (REAL) + `Executor.ts` (REAL) + `Router.ts` (REAL) existem e o `Orchestrator.ts` que os liga é MOCK. Antes de decidir adotar qualquer padrão novo dos 32 acima, ligar essas 3 peças já escritas é o trabalho de maior retorno imediato — nenhum framework externo substitui esse trabalho de fiação interna.

## 5. Nota lateral — a lacuna de "direcionamento e planejamento"

No pedido que abriu esta auditoria, foi levantada uma queixa concreta: falta de um papel/agente que "entenda o que é, defina escopo, desmembre em fases e execute uma a uma" — um Project Director/PMO, não um planeador de tarefa única.

- **Já existe** `agents/meta/planejador.agent.md` — meta-agente com lógica Fast-Path vs Full Cycle, produz plano+critério de pronto+riscos a partir de uma demanda já filtrada. Real, não placeholder.
- **Já existe**, do lado técnico, `orchestrator/Planner.ts` (secção 1a) — decompõe uma tarefa em passos com agentes escolhidos por LLM. Também real, também desligado (Orchestrator.ts MOCK).
- **Nenhum dos dois cobre** decidir *quais* iniciativas existem, priorizá-las, e devolver controlo entre fases de um portfólio — o papel de PMO/Project Director da proposta de arquitetura revisada colada no início desta conversa (Nível 3 — Gerência vertical por projeto).
- O achado técnico mais próximo de uma resposta continua a ser o **O21 (Magentic Task Ledger + Progress Ledger)** — planeamento de *uma tarefa* com re-planeamento por estagnação, não gestão de *portfólio*.

**Conclusão honesta:** a peça que falta não é técnica — nem os 8 frameworks de `patterns-from-orchestrators/` nem os 6 desta fase se propõem a ser um PMO. É lacuna real de arquitetura organizacional, a decidir humanamente, não algo para "adotar" de um framework externo.

## 6. Próxima fase

Por cobrir do espectro completo da "Auditoria Profunda — Agentes": Skills (2.7 — parcialmente coberto por `patterns-from-hermes/`, verificar sobreposição antes de nova pesquisa), Tool Use (2.8), ecossistema MCP sob a perspetiva de agentes (2.9 — parcialmente coberto por `patterns-from-mcp/`/`MCP-MAPPING.md`), Agent Communication/A2A (2.10), Observability (2.11), Evaluation (2.12), Testing (2.13), Coding/Research agents — OpenHands, SWE-agent, Aider, browser-use (2.14), Agentes especializados por domínio (2.15).

Sugestão de Fase 2: verificar primeiro a sobreposição com `patterns-from-hermes/` e `patterns-from-mcp/` (o mesmo cuidado que evitou refazer `patterns-from-orchestrators/` nesta fase), depois cobrir o que sobrar de Skills/Tool Use/MCP/Communication. Deixar Coding/Research agents e Evaluation/Testing para uma Fase 3.
