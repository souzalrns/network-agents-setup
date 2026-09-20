# LlamaIndex — camada de Agentes e Workflows (auditoria profunda)

**Repositório:** [run-llama/llama_index](https://github.com/run-llama/llama_index) — foco exclusivo em `llama-index-core` (agentes) e no sub-projeto Workflows. RAG/retrieval genérico foi deliberadamente excluído (já coberto na auditoria de memória).

**Nota metodológica:** o achado mais importante desta auditoria está na própria descrição do repositório no GitHub, hoje: **"LlamaIndex is the document processing platform for AI"**. Já não se descreve como framework de agentes.

## 1. Tabela de capacidades

| Capacidade | O que o projeto alega | Evidência verificada (link) | Validado? |
|---|---|---|---|
| Abstração atual de agentes | "Agentes modernos" = `FunctionAgent`, `ReActAgent`, `AgentWorkflow`; `OpenAIAgent`/`AgentRunner`/`AgentWorker` deprecados | `OpenAIAgent` removido na [v0.13.0](https://github.com/run-llama/llama_index/releases/tag/v0.13.0); core atual = v0.14.24, Python >=3.10,<4.0, MIT | Sim |
| Function calling direto | `FunctionAgent` usa tool-calling nativo do LLM, não ReAct | `llama_index/core/agent/workflow/function_agent.py`: exige `FunctionCallingLLM`, chama `achat_with_tools()`/`astream_chat_with_tools()`, scratchpad em `ctx.store` | Sim |
| ReAct ainda existe | Thought/Action/Observation | `react_agent.py`: `ReActOutputParser` exige formato `Thought:/Action:/Action Input:` ou `Thought:/Answer:` | Sim |
| Multi-agente / handoff | `AgentWorkflow` orquestra vários agentes | `multi_agent_workflow.py`: handoff é **uma tool dinâmica** (`_get_handoff_tool()`), filtrada por `can_handoff_to`; estado em `ctx.store` | Sim |
| "Workflows" = grafo de eventos | Sistema `@step`/`Event`/`Context` | O código de `llama_index/core/workflow/*.py` é hoje **apenas um shim de import** (`from workflows.workflow import Workflow`) — implementação real vive num pacote separado, `llama-index-workflows`, no repo [run-llama/llama-agents](https://github.com/run-llama/llama-agents) | Sim, com correção: já não é código "da core" |
| Checkpoint/resume | Estado persiste entre steps | `context/context.py`: `Context.to_dict()` serializa state store, filas de eventos, buffers, broker log, flag de execução; `Context.from_dict()` reconstrói | Sim |
| Streaming de eventos | Eventos observáveis em tempo real | `ctx.write_event_to_stream()` + `ctx.stream_events()` (`AsyncGenerator[Event]`) | Sim |
| Human-in-the-loop | Pausa para input humano | `ctx.wait_for_event(HumanResponseEvent, waiter_event=InputRequiredEvent(...), waiter_id=..., timeout=2000)` — **mas a doc do próprio método avisa que faz replay do step inteiro ao retomar** | Parcial — existe, mas com limitação de design séria |
| Timeout/retry/cancel | Runtime robusto | `Workflow.run(timeout=45.0)` levanta `WorkflowTimeoutError`; `retry_policy()` estilo `tenacity` (`wait_fixed/wait_exponential/wait_random_exponential/wait_incrementing` + `stop_after_attempt/stop_after_delay`); `retry_info()` devolve tentativa/tempo/última exceção | Sim |
| Planning explícito | — | Único agente com decomposição explícita, `StructuredPlannerAgent`, pertence à linha **deprecada** `AgentRunner`/`AgentWorker` ([discussão #14412](https://github.com/run-llama/llama_index/discussions/14412), [issue #16625](https://github.com/run-llama/llama_index/issues/16625): "always defaults to single task plan"). Nos agentes atuais **não há planning upfront** | Alegação refutada para a stack atual |
| Maturidade do núcleo (RAG) | Um dos projetos mais populares | API: 52.214 estrelas, 8.168 forks, 802 issues abertas, push em 2026-09-18, 287 subscribers | Sim |
| Maturidade da camada de agentes/deploy | (alegada implicitamente) | `run-llama/llama-agents` (motor de Workflows + servidor + CLI) tem apenas **450 estrelas, 85 forks** — terceira arquitetura/nome desta camada em ~2 anos (ver cronologia) | **Não validada** — é a parte menos madura do ecossistema |
| Segurança / bug bounty | SECURITY.md com disclosure | Bounty via Huntr cobre só `llama-index`, `llama-index-core`, `llama-index-embeddings-openai`, `llama-index-llms-openai`, `llama-index-cli`. Explicitamente fora de escopo: prompt injection, SSRF, DoS por payload grande | Sim, mas âmbito estreito |
| Licença / uso comercial | MIT em todos os pacotes | `LICENSE` confirmado em `llama_index` e `llama-agents` | Sim |
| Agnóstico a LLM provider | Sim | `FunctionAgent` exige só a interface `FunctionCallingLLM`; dezenas de integrações `llama-index-llms-*` | Parcial (estrutural, não exaustivo) |
| Corre localmente | Sim | `llama-index-workflows` é biblioteca Python pura async, sem dependência de servidor | Sim |

## 2. A cronologia da camada de agentes/deploy — achado central de maturidade

```
2024-06  llama-agents v1  — arquitetura de microserviços (control plane +
                             message queue + agent services), repo próprio
2024-09  llama-deploy     — sucessor anunciado do v1, mesma ideia, nome novo
2026-04  llama_deploy     — última atividade real (push 2026-04-06),
                             hoje MARCADO COMO DEPRECADO na própria doc:
                             "to serve workflows, use llama-agents instead"
2026-xx  llama-agents v2  — o NOME é reciclado para um projeto DIFERENTE:
                             `llama-index-workflows` + `llama-agents-server` +
                             `llama-agents-client` + CLI `llamactl`
```

Confirmado via `pushed_at`/`description`/`archived` da API do GitHub para os três repos. Três nomes, duas arquiteturas distintas, em ~24 meses, para a mesma responsabilidade ("como executar/servir agentes em produção") — sinal direto de instabilidade nesta camada específica, não no núcleo de indexação/RAG.

## 3. Padrões extraíveis

1. **Handoff-como-tool-dinâmica** (`AgentWorkflow._get_handoff_tool()`) — delegação implementada como tool normal, injetada condicionalmente e filtrada por allow-list (`can_handoff_to`). Relevante ao gap "Delegation Graph ausente" do `GOV-FASE1.md`.
2. **Formato de checkpoint de `Context`** (`to_dict()`/`from_dict()`) — referência para "rollback/replay ausente" e "checkpoint HITL em `Map`, perde-se com restart" (`HitlManager.ts`).
3. **`wait_for_event` + `InputRequiredEvent`/`HumanResponseEvent` com `waiter_id`** — padrão de HITL com chave de idempotência. Importar também **o aviso**: replay do step inteiro exige que o trabalho antes do `wait` seja repetível/sem efeitos colaterais.
4. **Composição de retry policy estilo `tenacity`** — referência pronta para "rate limiting/retry ausente em `packages/core/` TS".
5. **Routing de eventos por assinatura de tipos** (`@step` infere eventos de entrada/saída pelas anotações de tipo) — contrato tipado entre passos.
6. **SECURITY.md com âmbito de bounty explícito e exclusões nomeadas** — template a copiar.

## 4. Classificação e porquê

**EXTRACT** — não usar o LlamaIndex (nem `llama-index-workflows`, nem `llama-agents`) como motor de execução. A parte que corresponderia ao "nosso runtime" (orquestração/deploy de agentes) é precisamente a menos madura e mais instável do ecossistema: 450 estrelas contra 52 mil do núcleo, três nomes/arquiteturas em dois anos, e o próprio projeto reposicionou-se publicamente como "document processing platform". Não é REJECT porque o código lido é real e bem desenhado em pontos específicos (checkpoint, retry, streaming, HITL) — vale estudar e portar padrões, não importar a dependência.

## 5. O que NÃO adotar

- O motor de execução completo (`Workflow`/`Context`/`@step` via `pip install llama-index-workflows`).
- `AgentWorkflow`/`FunctionAgent`/`ReActAgent` como motor de agentes — sem planning explícito maduro, e sem verificação de capacidade/scope antes de chamar tools (mesma lacuna do nosso `ToolExecutor`).
- `wait_for_event` sem a ressalva de idempotência — introduziria duplicação de efeitos colaterais em qualquer resume.
- SECURITY.md como garantia de segurança agentic — exclui prompt injection do âmbito de bounty.
- Números de popularidade do repo-mãe como prova de maturidade da camada de agentes — são domínios diferentes.
