# OpenAI Agents SDK (`openai-agents-python`) — auditoria profunda

Auditado no commit `fdf21db` (2026-09-17), versão do pacote `0.22.3`. Metodologia: leitura direta de código-fonte (pyproject.toml, módulos `src/agents/*`, exemplos, SECURITY.md, README).

## 1. Tabela de capacidades

| Capacidade | O que o projeto alega | Evidência verificada (link) | Validado? |
|---|---|---|---|
| Sucessor do Swarm, produção | "production-ready evolution of Swarm" | [swarm/README.md](https://github.com/openai/swarm/blob/main/README.md) | **Sim** |
| Versão JS/TS oficial existe | Aponta para `openai-agents-js` | [openai/openai-agents-js](https://github.com/openai/openai-agents-js): 3.832 estrelas, push em 2026-09-18 | **Sim** |
| Agentes com instructions/tools/guardrails/handoffs | "LLMs configured with instructions, tools, guardrails, and handoffs" | `src/agents/agent.py`: classe `Agent` importa `InputGuardrail`/`OutputGuardrail`, `Handoff`, `Tool`, `Prompt` | **Sim** |
| Tools = function calling + MCP + hosted | "Various Tools let agents take actions" | `FunctionTool`, `MCPUtil`, diretório `mcp/`; `mcp>=1.19.0` dependência declarada | **Sim** |
| Multi-agent via "handoff" | "Delegating to other agents for specific tasks" | `src/agents/handoffs/__init__.py`: `Handoff` devolve um novo `Agent` — é passagem de controlo completa (o agente atual termina o turno) | **Sim, com precisão** |
| Alternativa "agents-as-tools" (com retorno) | Padrão distinto de handoff | `examples/agent_patterns/agents_as_tools.py`: `spanish_agent.as_tool(...)` — aqui há retorno ao agente chamador | **Sim** — confirma as duas semânticas |
| Orquestrador central vs peer handoff | Não há "orchestrator" obrigatório na arquitetura core | Nos exemplos, o "orquestrador" é só um `Agent` normal com mais tools/handoffs — convenção de uso, não componente distinto | **Parcial** |
| Runtime reativo (loop de tool-calling) | Não alegado como grafo/planning | `src/agents/run.py` linha 979: `while True:` com `current_turn` e `MaxTurnsExceeded` — loop de turnos, não state machine declarativa | **Sim** |
| Checkpoint/resume de execução | Página de docs "human_in_the_loop" | `src/agents/run_state.py`: `RunState` serializa `ToolApprovalItem`, `McpApprovalRequest`, estado de agentes por `weakref`/id | **Sim** |
| Timeout/retry | Não é destaque de marketing | `src/agents/retry.py`: `ModelRetryBackoffSettings` (delay inicial, max delay, multiplier, jitter) — retry a nível de chamada ao modelo, não de qualquer step | **Sim, escopo limitado** |
| Human-in-the-loop (approve/reject/edit) | "Built-in mechanisms for involving humans" | `RunState` + `ToolApprovalItem`/`McpApprovalRequest` + exemplos `human_in_the_loop*.py` | **Sim** |
| Guardrails de input/output | "Configurable safety checks" | `src/agents/guardrail.py`: `InputGuardrail`/`OutputGuardrail` reais, `tripwire_triggered` interrompe execução | **Sim** |
| Guardrails por tool | Não destacado no README top-level | `src/agents/tool_guardrails.py`: `ToolInputGuardrail`/`ToolOutputGuardrail` com 3 comportamentos (`allow`, `reject_content`, `raise_exception`) | **Sim** (achado extra) |
| Planning / task decomposition explícito | Não alegado | Nenhuma classe `Planner`/`Plan`; `agent_patterns/deterministic.py` mostra decomposição feita à mão pelo developer | **Confirma ausência** — ReAct-like reativo |
| Maturidade | — | GitHub API: 29.552 estrelas, 4.765 forks, ~382 contribuidores, 232 subscribers, criado 2025-03-11 | **Sim** |
| Atividade recente | — | Último push 2026-09-17T22:19:03Z; 234 commits entre 2026-09-01 e 2026-09-17 | **Sim, muito ativo** |
| Issues abertas vs fechadas | — | 1.509 fechadas / 27 abertas; 3.410 PRs no total | **Sim, ratio saudável** |
| Agnóstico de provider ("100+ LLMs") | "provider-agnostic... 100+ other LLMs" | `src/agents/extensions/models/litellm_model.py` e `any_llm_model.py` são adaptadores reais; extras `litellm`/`any-llm` no `pyproject.toml` | **Sim, com nuance** |
| Dependência obrigatória do pacote `openai` | — | `pyproject.toml`: `openai>=3.0.0,<4` é dependência **obrigatória** mesmo quando o modelo é Anthropic/Gemini via LiteLLM | **Parcial** — agnóstico de modelo, não de dependência |
| SECURITY.md real | — | Cobre escopo explícito (execução de agentes, tools, MCP, sessions, tracing, Realtime/Voice, sandbox); define trust boundaries e o que NÃO conta como falha do SDK | **Sim**, substantivo |
| Licença MIT | — | API GitHub: `license.spdx_id: "MIT"` | **Sim** |
| Corre localmente | — | `Runner.run_sync()` corre em processo local; única chamada de rede obrigatória é para o provider LLM | **Sim** |
| Sessões persistentes | "Automatic conversation history management" | `src/agents/memory/`: `SQLiteSession`, `openai_conversations_session.py`, extras `redis`/`sqlalchemy` | **Sim** |
| Tracing nativo, envia para a OpenAI por omissão | "Built-in tracking of agent runs" | `src/agents/tracing/processors.py`: `BackendSpanExporter` tem endpoint fixo `https://api.openai.com/v1/traces/ingest` por omissão; `ConsoleSpanExporter` alternativo e `set_tracing_disabled()` | **Sim, opt-out, não opt-in** |
| Sandbox agents / execução com estado de workspace | "Agents preconfigured to work with a container" | `SandboxAgent`, `Manifest`, `UnixLocalSandboxClient`/`DockerSandboxClient` | **Sim** (achado extra) |

## 2. Padrões extraíveis

1. **`Handoff` como objeto de primeira classe, distinto de tool comum** — `src/agents/handoffs/__init__.py`. Tool especial que devolve um `Agent`, com `input_filter` (filtrar histórico na transição) e `is_enabled` (bool ou callable dinâmico). Útil para contrato de transição de controlo entre "agentes públicos"/"privados" em `config/agents.config.ts`.
2. **Guardrail com 3 comportamentos declarativos** (`allow`/`reject_content`/`raise_exception`) — `src/agents/tool_guardrails.py`. Aplicável diretamente à lacuna de `ToolExecutor.executeTool()` em `packages/mcp/` (zero verificação de capacidade/scope, ver `GOV-FASE1.md`).
3. **`RunState` serializável para resume com HITL** — `src/agents/run_state.py`. Serializa o estado do turno (incluindo aprovações pendentes) para JSON. Contraste directo com `HitlManager.ts` (estado em `Map`, não sobrevive a restart) — padrão concreto para tornar o HITL Python resiliente.
4. **Exportador de tracing plugável com fallback console** (`TracingExporter`: `ConsoleSpanExporter` vs `BackendSpanExporter`) — mais barato de portar que uma stack OTel completa para preencher a lacuna "Observability ausente em TS" do `GOV-FASE1.md`.
5. **Padrões de orquestração como receitas de aplicação, não componente do runtime** (`examples/agent_patterns/`: `deterministic.py`, `agents_as_tools.py`, `routing.py`, `parallelization.py`, `llm_as_a_judge.py`) — confirma que routing/paralelização não exige "motor de orquestração" importado, pode ser composição no próprio `plan_runner`.
6. **`ModelRetryBackoffSettings`** — contrato pequeno (delay inicial, delay máximo, multiplicador, jitter) portável para `mcp/plan_runner/policy.py`.
7. **Escopo do `SECURITY.md`** — modelo de escrita útil ("Scope" + "Trust boundaries" + o que NÃO conta como vulnerabilidade do SDK), relevante face ao achado do `MCPServer.createHttpHandler()` sem autenticação nenhuma.

## 3. Classificação e porquê

**EXTRACT.** Projeto maduro (quase 30k estrelas, ~380 contribuidores, cadência diária, SECURITY.md substantivo, MIT) com alegações confirmadas por código, não só README. Não se encaixa em ADOPT/ADAPT porque já existe contrato Plan-Execute próprio e MCP de produção em Python — adotar o SDK inteiro herdaria dependência obrigatória do `openai`, o modelo de execução `Runner`/`while True`, e superfície muito além do necessário (voice, realtime, sandbox). O valor está em extrair contratos específicos (handoff tipado, guardrail com 3 comportamentos, `RunState` serializável, exportador de tracing plugável).

## 4. O que NÃO adotar

- Vendor lock-in de tracing por omissão para a OpenAI (opt-out, não opt-in).
- Dependência obrigatória do pacote `openai` mesmo usando outros modelos via LiteLLM/any-llm.
- Superfície excessiva (`voice/`, `realtime/`, `sandbox/`, dezenas de dependências opcionais irrelevantes ao nosso stack).
- "Orquestrador central" não existe no runtime — é convenção de aplicação, não resolve por si só a necessidade de um contrato Plan-Execute.
- Ausência de planning/task decomposition — quem precisar de decomposição estruturada não ganha nada ao adotar o SDK nesse eixo.
- Complexidade de versão — ritmo de mudança muito rápido (234 commits em 17 dias); depender da API pública inteira como biblioteca implicaria manutenção contínua para breaking changes.

**Evidência primária:** [openai-agents-python](https://github.com/openai/openai-agents-python) (commit `fdf21db`) · [agent.py](https://github.com/openai/openai-agents-python/blob/main/src/agents/agent.py) · [handoffs/__init__.py](https://github.com/openai/openai-agents-python/blob/main/src/agents/handoffs/__init__.py) · [guardrail.py](https://github.com/openai/openai-agents-python/blob/main/src/agents/guardrail.py) · [tool_guardrails.py](https://github.com/openai/openai-agents-python/blob/main/src/agents/tool_guardrails.py) · [run_state.py](https://github.com/openai/openai-agents-python/blob/main/src/agents/run_state.py) · [run.py](https://github.com/openai/openai-agents-python/blob/main/src/agents/run.py) · [retry.py](https://github.com/openai/openai-agents-python/blob/main/src/agents/retry.py) · [tracing/processors.py](https://github.com/openai/openai-agents-python/blob/main/src/agents/tracing/processors.py) · [examples/agent_patterns](https://github.com/openai/openai-agents-python/tree/main/examples/agent_patterns) · [swarm/README.md](https://github.com/openai/swarm/blob/main/README.md) · [openai-agents-js](https://github.com/openai/openai-agents-js)
