# Google ADK (`google/adk-python`) — auditoria profunda

**Repositório confirmado:** `google/adk-python` (org: `google`, licença Apache 2.0). Existe também `google/adk-python-community` (extensões da comunidade, não mantido pela Google core team) e ecossistema paralelo `adk-samples`, `adk.dev` (docs). Não confirmado nesta fase se há um `adk-java` mantido pelo mesmo grupo — não investigado, tratar como não verificado.

## Tabela de evidência

| Capacidade | O que o projeto alega | Evidência verificada (link) | Validado? |
|---|---|---|---|
| Proveniência / manutenção ativa | "open-source, code-first Python toolkit" mantido pela Google | [google/adk-python](https://github.com/google/adk-python): 21,6k stars, 4,0k forks, 274 issues abertas, ~4286 commits, release **2.9.0 em 2026-09-10** (cadência semanal, ver [CHANGELOG.md](https://github.com/google/adk-python/blob/main/CHANGELOG.md)) | **Sim** — atividade real |
| Uso interno Google / Agentspace / Gemini Enterprise | Integração com plataforma empresarial Google | [Gemini Enterprise Agent Platform docs](https://docs.cloud.google.com/gemini-enterprise-agent-platform/build/adk): ADK é o caminho oficial de build para essa plataforma | **Sim** — há produto Google Cloud real a depender disto |
| Definição de agentes / tools / function calling | Agentes recebem tools, contexto, fazem raciocínio | `agents/__init__.py`: `LlmAgent` (alias `Agent`), `BaseAgent`; `tools/`: `base_tool.py`, `function_tool.py`, `_automatic_function_calling_util.py`, `tool_context.py` | **Sim** |
| Multi-agent / composição tipo "Team" | Suporta multi-agente coordenado | `agents/__init__.py`: `SequentialAgent`, `ParallelAgent`, `LoopAgent`, `ManagedAgent`; `tools/agent_tool.py` (agente-como-tool) | **Sim** — 3 padrões de composição + agente-como-ferramenta |
| Agent-to-agent remoto (A2A) | "Task API for structured agent delegation" | `src/google/adk/a2a/` com `agent/`, `converters/`, `executor/` | **Parcial** — estrutura confirmada, não o comportamento runtime linha a linha |
| Runtime/Execution Engine | Grafo com routing, fan-out/fan-in, loops, HITL | `runners.py` (`Runner.run/run_async/run_live`) + `src/google/adk/workflow/`: `_graph.py`, `_node.py`, `_join_node.py`, `_dynamic_node_scheduler.py`, `_parallel_worker.py`, `_retry_config.py` | **Sim** — DAG real com fan-in/fan-out e retry |
| Sessão persistente / resume | Sessões persistem e retomam | `sessions/`: `in_memory_session_service.py`, `sqlite_session_service.py`, `database_session_service.py`, `vertex_ai_session_service.py`; `Runner._setup_context_for_resumed_invocation()` | **Sim** |
| Cancelamento | Cancelamento gracioso | `Runner.run()`: parar de iterar cancela a task de fundo (`_cleanup_root_task()`) | **Sim** |
| Timeout/retry a nível de Runner | — | Não encontrado a nível de `Runner`; retry existe só no motor de workflow (`_retry_config.py`), por nó | **Não** (Runner) / **Sim** (nó de workflow) |
| Human-in-the-loop (approve/reject) | "Tool Confirmation flow" | `tools/tool_confirmation.py`, `tool_context.request_confirmation()` | **Sim, com ressalva grave**: [issue #7148](https://github.com/google/adk-python/issues/7148) — em v2.9.1 a recusa ("Decline") não era imposta pela framework; corrigido só por [PR #7151](https://github.com/google/adk-python/pull/7151) |
| Planning / decomposição | Mecanismo explícito | `planners/`: `base_planner.py`, `built_in_planner.py`, `plan_re_act_planner.py` | **Sim**, abstração dedicada |
| SECURITY.md | — | Ausência confirmada: não existe `SECURITY.md` na raiz nem em `.github/` | **Não validado / gap real** |
| Licença | Apache 2.0 | `LICENSE` confirmado + badge no README | **Sim** |
| Governança / CLA | Community-friendly | `CONTRIBUTING.md`: exige CLA; sem CODEOWNERS público, sem lista de mantenedores nomeados | **Parcial** |
| Operação local sem GCP | "model-agnostic", roda localmente | `in_memory_session_service.py`/`sqlite_session_service.py` não exigem GCP; extras `gcp`, `agent-identity`, `bigquery-analytics`, `oci` são opcionais (22 extras no `pyproject.toml`) | **Sim** — núcleo local, GCP é extra |
| Multi-LLM sem fricção | "optimized for Gemini" mas compatível com outros | `models/`: `lite_llm.py` (LiteLLM), `anthropic_llm.py` (Anthropic direto), `gemma_llm.py`, `google_llm.py` | **Sim** |
| Estabilidade de API | — | README expõe secção "BREAKING CHANGES FROM 1.x"; CHANGELOG mostra breaking changes em ~3 de 8 releases recentes | **Não validado como estável** — v2.x jovem, ritmo semanal |

## Padrões extraíveis

1. **Contrato `ToolConfirmation` (approve/deny com enforcement centralizado)** — `tools/tool_confirmation.py` + `tool_context.request_confirmation()`. A decisão do humano é um objeto tipado (`confirmed: bool`) interceptado pela framework **antes** de chamar a tool. Vale copiar o padrão de *enforcement no boundary*, não o código — mesmo com o bug histórico (#7148).
2. **Taxonomia Sequential/Parallel/Loop + Agent-as-Tool** — `agents/__init__.py`, `tools/agent_tool.py`. Vocabulário claro para sub-planos sequenciais/paralelos/loop e para tratar agentes delegados como tools de primeira classe.
3. **Separação Runner síncrono/assíncrono/live** — `runners.py`. Wrapper síncrono lança task de fundo e cancela-a se o chamador parar de iterar.
4. **Esquema de evento append-only com resume por `invocation_id`** — `sessions/`, `Runner._setup_context_for_resumed_invocation()`.
5. **Abstração `BasePlanner` com implementações intercambiáveis** (`BuiltInPlanner`, `PlanReActPlanner`) — interface limpa para múltiplos mecanismos de decomposição sem acoplar o motor a um único algoritmo.
6. **Motor de workflow em grafo com nós tipados** (`_node`, `_join_node`, `_retry_config`, `_dynamic_node_scheduler`) — vocabulário de tipos de nó e separação estado/política de falha.
7. **Adaptador multi-LLM direto (não via proxy único)** — `models/anthropic_llm.py` vs `models/lite_llm.py`: um adaptador nativo para o provedor principal + um genérico para o resto.

## Classificação e porquê

**EXTRACT** — não usar `adk-python` diretamente, mas extrair os padrões acima (especialmente #1 e #2 e #4).

- ADK é um framework completo e opinativo (26 dependências obrigatórias + 22 extras, motor de grafo próprio, sessões próprias, CLI própria) pensado para ser o runtime inteiro — conflita com contratos Plan-Execute próprios e MCP de produção já existentes.
- Maduro o suficiente (21,6k stars, mantido pela Google, integrado num produto Cloud real, cadência semanal) para que os padrões de desenho valham a pena estudar — resolve exatamente os mesmos problemas em aberto do `GOV-FASE1.md` (HITL incompleto, ausência de enforcement de autorização no boundary de execução).
- Não é ADOPT/ADAPT porque adotar o runtime inteiro violaria a restrição de não substituir o motor Plan-Execute/MCP, e a API ainda muda de forma quebrante (1.x→2.x).

## O que NÃO adotar

- O motor de execução inteiro (`workflow/`, `runners.py`, `sessions/`) — substituiria, não complementaria, o Plan-Execute.
- Vendor lock-in a stack Google — 22 extras (`gcp`, `bigquery-analytics`, `agent-identity`, `otel-gcp`, `toolbox`, `a2a`) empurram para Vertex AI/Cloud Run/BigQuery mesmo sendo "opcionais".
- Confiar no HITL "pronto a usar" — o bug real do `ToolConfirmation` (recusa não imposta até PR recente) é sinal de que nem a implementação de referência da Google escapou à mesma falha que o `HitlManager.ts` tem hoje.
- Ausência de `SECURITY.md` — não referenciar este projeto como precedente de maturidade de segurança.
- Complexidade desnecessária do motor em grafo completo (`_dynamic_node_scheduler.py`, `_parallel_worker.py`) — resolve escala que o Plan-Execute provavelmente não precisa hoje.
- Instabilidade de API como base de dependência direta — breaking changes documentadas em releases recentes.
