# Auditoria de Agentes — Fase 2: Skills, Tool Use, Ecossistema MCP, Agent Communication

Continuação de `FASE1-AGENTES.md`. Mesma disciplina: código > README, verificação directa antes de qualquer classificação.

## 0. Escopo desta fase e o que já existia

Antes de pesquisar qualquer coisa nova, esta fase verificou a sobreposição com trabalho já feito — o mesmo cuidado que evitou refazer `patterns-from-orchestrators/` na Fase 1:

- **Skills (2.7) — já coberto, não refeito.** `docs/architecture/patterns-from-hermes/` já tem um ciclo de vida de skills completo e real (`candidate → reviewed → active → patched → stale → archived`, com critérios de promoção, regra "nunca auto-merge", formato mínimo de candidate) extraído do Hermes Agent (Nous Research, MIT). Cobre exactamente o que a secção 2.7 da auditoria pedia (skill discovery, lifecycle, versioning, permissões via human gate).
- **Observability (2.11) — já coberto, não refeito.** `docs/architecture/memory/FASE3-MEMORIA.md` secção 5 já avaliou Langfuse (34.774★, real), OpenTelemetry (padrão de indústria, não pesquisado de novo por ser conhecimento estável), RAGAS (não verificado — nome/org pode estar errado), Attestix e "Agent Passport" (ambos fragmentados/não confirmados como produto único). Não há razão para repetir isto sob o rótulo "Agentes" — é a mesma pergunta, já respondida.
- **Evaluation (2.12) e Testing (2.13) — deliberadamente adiados para a Fase 3**, como já anunciado no fecho da Fase 1.

O que sobrou para esta fase, genuinamente novo: **Tool Use (2.8)** — resolvido por verificação directa do próprio repo, sem precisar de pesquisa externa nova; **ecossistema MCP sob a perspectiva de agentes (2.9)**; **Agent Communication / A2A (2.10)**.

## 1. Achado interno (Tool Use, 2.8) — a superfície MCP exposta é mais estreita do que o runtime por baixo

Verificado por leitura directa de `docs/architecture/patterns-from-mcp/tools-catalog.md` e `governance-pipeline.md` contra os achados da Fase 1 (secção 1b, `runner/plan_runner/`):

| Capacidade do runtime (Fase 1) | Exposta via MCP (`mcp/plan_runner/mcp_plan_runner/tools_impl.py`)? |
|---|---|
| Motor "langgraph" — checkpoint real (`SqliteSaver`) + execução paralela por ondas | **Não.** A tool `run_plan` só chama `plan_runner.engine.run_plan` (motor "native"). O parâmetro `--engine langgraph` só existe na CLI directa |
| HITL `edit` com payload real (`--payload-file`) | **Não.** A tool `resume_plan` só aceita `decision: approve\|reject` (`tools-catalog.md` secção `resume_plan`) — `edit` nem consta do enum documentado |
| Contrato HITL partilhado (`hitl-requests.jsonl`/`hitl-decisions.jsonl`, `hitl.py`) | Não exposto como tool própria — é um ficheiro lido/escrito directamente, fora do MCP |

**O que isto significa:** um cliente MCP (outra sessão Claude, ou qualquer agente externo) que só conheça o servidor via `tools-catalog.md` não tem forma de pedir checkpoint/paralelismo nem de resolver um HITL com edição — mesmo essas capacidades já existindo, testadas, no motor por baixo. Isto não é um bug de segurança (ao contrário da lacuna equivalente em `packages/mcp/ToolExecutor`, que não verifica nada) — é uma lacuna de **superfície incompleta**: a tool existe, só não expõe tudo o que podia.

## 2. Agent Communication (2.10) — A2A e ACP

| Alegação | Evidência verificada | Validado? |
|---|---|---|
| A2A (Agent2Agent) foi lançado pela Google em abril 2025, doado à Linux Foundation em junho 2025, e mudou de casa outra vez em agosto 2026 para a **Agentic AI Foundation (AAIF)** — o mesmo guarda-chuva neutro que agora hospeda o MCP (Anthropic), goose (Block) e AGENTS.md (OpenAI) | [a2a-protocol.org blog](https://a2a-protocol.org/latest/blog/2026/08/27/a-new-chapter-for-a2a-joining-the-agentic-ai-foundation/), [Linux Foundation press release](https://www.linuxfoundation.org/press/linux-foundation-announces-the-formation-of-the-agentic-ai-foundation) | Sim |
| Especificação real: `AgentCard` (manifesto de capacidades descoberto por URL), `Task` com máquina de estados explícita (`submitted→working→{completed\|failed\|canceled\|rejected}`, mais `input_required`/`auth_required`), `Artifact` composto por `Parts` tipadas, streaming via SSE, transporte JSON-RPC 2.0 + bindings gRPC/REST | [a2a-protocol.org/specification](https://a2a-protocol.org/latest/specification/) | Sim, spec 1.0 estável (não draft) |
| Maturidade real: ~25.6k estrelas, 161 contribuidores, 6 SDKs oficiais (Python/JS/Java/.NET/Go/Rust), Apache-2.0 | [github.com/a2aproject/A2A](https://github.com/a2aproject/A2A) | Sim |
| Adopção real por código, não só anúncio: **Google ADK** (`src/google/adk/a2a/`, `to_a2a()` real) e **Microsoft Agent Framework** (pacote PyPI `agent-framework-a2a`, classe `A2AAgent` documentada) | Repos confirmados, ver `deep/microsoft-agent-framework.md`/`deep/google-adk.md` da Fase 1 | Sim |
| **OpenAI Agents SDK "suporta A2A"** — alegação repetida por vários blogs de terceiros | Issues #472 e #1374 no repo oficial, ambas pedidos de feature **fechados sem PR associado** | **Contradita** — não há suporte nativo real, ao contrário do que artigos de terceiros sugerem |
| **ACP (Agent Communication Protocol, IBM/BeeAI)** — lançado maio 2025, um mês depois do A2A | Repo `i-am-bee/acp` **arquivado** desde 27/08/2025, SDK npm **deprecated**, fusão formal no A2A confirmada pelo próprio Linux Foundation | Sim — **ACP está morto** como protocolo independente |
| AGNTCY (Cisco) — terceiro projecto, foco em descoberta (OASF) e identidade/mensageria (SLIM), descrito como complementar (não concorrente) a A2A/MCP | [Linux Foundation](https://www.linuxfoundation.org/press/linux-foundation-welcomes-the-agntcy-project-to-standardize-open-multi-agent-system-infrastructure-and-break-down-ai-agent-silos) | Não aprofundado nesta fase — **NOT VERIFIED**, fica para decisão futura se necessário |

**Isto resolve o problema real deste repo (`pending_steps/request.json` → `result.json`, secção 1b da Fase 1)?** Não — e adoptá-lo hoje seria desproporcionado. O A2A resolve comunicação entre agentes **opacos, de organizações diferentes**, que precisam de descoberta pública e negociação de autenticação cross-domínio (OAuth2/OIDC/mTLS). O problema actual do `plan_runner` é IPC **dentro da mesma confiança** — um humano ou uma sessão Claude a resolver um ficheiro dentro do mesmo repo. Não há hoje cenário de "agente de terceiros fora do nosso controlo" que justifique montar um servidor A2A completo.

**Onde A2A ficaria genuinamente relevante:** no dia em que o PCU precisar de expor um agente a terceiros, ou consumir um agente de outra organização/rede. Nesse dia, o vocabulário Task/Artifact/AgentCard é claramente melhor do que inventar um protocolo próprio.

## 3. Ecossistema MCP sob a perspectiva de agentes (2.9)

| Alegação | Evidência verificada | Validado? |
|---|---|---|
| **FastMCP** (`jlowin/fastmcp`, agora sob a Prefect) tem composição multi-servidor via `mount()`/`create_proxy()`, expondo por omissão a superfície **completa** do servidor montado, com filtragem explícita opt-in (`namespace=`, `enable(tags=..., only=True)`) | [gofastmcp.com/servers/composition](https://gofastmcp.com/servers/composition) | Sim |
| FastMCP tem OAuth2/OIDC/bearer, mas **não tem verificação de scope/capacidade por tool** — só autentica identidade, não autoriza acção | [gofastmcp.com/servers/auth](https://gofastmcp.com/servers/auth/authentication) — ausência confirmada por leitura directa | Sim |
| **mcp-agent** (`lastmile-ai`, ~8.5k★) implementa os padrões "Building Effective Agents" da Anthropic (Parallel, Router, Orchestrator-Workers, Evaluator-Optimizer, Swarm) com descoberta dinâmica multi-servidor (`MCPAggregator`) | [github.com/lastmile-ai/mcp-agent](https://github.com/lastmile-ai/mcp-agent) | Sim |
| **`mcp-agent` também não verifica scope/capacidade antes de chamar uma tool** — `Agent.call_tool()` delega directo ao aggregator, sem autorização, assumindo que "isso é responsabilidade do servidor MCP, não do agente" | Leitura directa de `src/mcp_agent/agents/agent.py` | Sim — **achado mais importante desta fase**: a mesma lacuna que `packages/mcp/ToolExecutor.ts` tem hoje (`GOV-FASE1.md`) é o padrão dominante em bibliotecas cliente, não uma falha exclusiva nossa |
| Padrão "agente-como-servidor MCP" confirmado em **3 implementações independentes**: Microsoft Agent Framework (`hosting-mcp`), mcp-agent (`examples/mcp_agent_server`), FastMCP (qualquer app montável) | Repos confirmados directamente | Sim — deixa de ser caso isolado, é padrão consolidado do ecossistema (eleva O22 de "referência" a quase-adopção como princípio) |
| Existe um **MCP Registry oficial** (`registry.modelcontextprotocol.io`), real e funcional (não só anúncio), API v0.1 já congelada, ~2000 entradas | [blog.modelcontextprotocol.io](https://blog.modelcontextprotocol.io/posts/2025-11-25-first-mcp-anniversary/), [github.com/modelcontextprotocol/registry](https://github.com/modelcontextprotocol/registry) | Sim |
| O Registry é um **catálogo de metadados estático**, não um mecanismo de descoberta+instalação dinâmica em runtime para um agente | Confirmado por ausência de menção após busca dirigida em 2 fontes primárias | Sim |
| **A spec MCP actual é 2026-07-28, não 2025-11-25** — elimina o handshake `initialize`/sessões (protocolo stateless por-pedido); **deprecia Sampling, Roots e Logging** (janela de 12 meses, migração recomendada para chamar o provider de LLM directamente); deprecia Dynamic Client Registration a favor de Client ID Metadata Documents; deprecia HTTP+SSE como transporte | [modelcontextprotocol.io/specification/2026-07-28/changelog](https://modelcontextprotocol.io/specification/2026-07-28/changelog) | Sim, **mas nota de cautela**: é informação que ultrapassa o corte de conhecimento do modelo e representa uma mudança de rutura na própria versão do protocolo — vale confirmação humana antes de qualquer decisão de arquitectura que dependa disto especificamente |

**Isto resolve as 2 lacunas já identificadas?** Parcialmente. Para a lacuna do §1 (superfície MCP estreita): não resolve, mas o padrão FastMCP ("expor tudo por omissão + narrowing explícito nomeado") mostra como tornar a omissão *visível e auditável* em vez de implícita em `tools_impl.py`. Para a lacuna do `packages/mcp/ToolExecutor` sem verificação de capacidade (`GOV-FASE1.md`): **não há nenhum framework cliente maduro que resolva isto por nós** — confirmado que nem FastMCP nem mcp-agent (a referência mais citada do ecossistema) fazem essa verificação. A conclusão prática é reforçada, não alterada: a correcção continua a ser interna, replicando o pipeline sanitize→auth→rate→scope→execute→audit que `mcp/plan_runner/policy.py` já tem testado, para dentro de `packages/mcp/`.

## 4. Padrões unificados novos (O59–O69)

Continuando a numeração de `FASE1-AGENTES.md` (O01–O58):

| ID | Padrão | Origem | Onde no nosso setup |
|---|---|---|---|
| O59 | `AgentCard` como manifesto de capacidades descoberto por URL | A2A | Um `resolver_manifest.json` leve ao lado de `pending_steps/<id>/request.json` — sem montar servidor |
| O60 | `Task` como máquina de estados rica (`submitted/working/input_required/auth_required/completed/failed/canceled/rejected`) | A2A | Vocabulário mais rico que o actual "pending vs. resolved" de `pending_steps/` |
| O61 | `Artifact` = lista de `Parts` tipadas (`text`/`file`/`data`) em vez de payload amorfo | A2A | Estruturar `result.json` para o runner validar o que voltou, em vez de assumir shape implícito |
| O62 | `security` declarado por acção/skill individual, não só por agente inteiro | A2A | Refinamento directo aplicável a `policy.py` (`SCOPES` já é por tool, este padrão aprofunda para sub-acções) |
| O63 | Modelo de maturidade Sandbox→Growth→Impact como critério de adopção de protocolos emergentes | AAIF | Heurística geral: só considerar ADOPT quando um protocolo tiver saído de "Sandbox" e provado adopção por 2+ organizações não-afiliadas |
| O64 | Composição por omissão-total + narrowing explícito (`mount`/`enable(tags=...)`) | FastMCP | Tornar visível/nomeado o corte já feito em `tools_impl.py` (motor native-only, sem edit) |
| O65 | Proxy multi-transporte unificado (`create_proxy`: stdio/HTTP/npx/uvx) | FastMCP | Se `packages/mcp` (TS) precisar de falar com `mcp/plan_runner` (Python/stdio) sem reimplementar transporte |
| O66 | Agente-como-servidor MCP, confirmado em 3 implementações independentes | Microsoft Agent Framework + mcp-agent + FastMCP | Já identificado na Fase 1 (O22) como referência isolada — corroboração eleva a princípio quase-adoptável |
| O67 | Client ID Metadata Documents em vez de Dynamic Client Registration | Spec MCP 2026-07-28 | Se/quando a fase HTTP+OAuth de `auth-and-scopes.md` avançar, não implementar DCR clássico (já deprecado) |
| O68 | MRTR (Multi Round-Trip Requests) — resultado interino que pede mais input, cliente reenvia com resposta | Spec MCP 2026-07-28 | `resume_plan` já é uma implementação *ad hoc* do mesmo conceito — realinhar nomenclatura em `auth-and-scopes.md`, não o motor |
| O69 | Registo público como catálogo versionado + prova de posse de namespace (não como provisionamento em runtime) | MCP Registry oficial | Modelo a copiar **se** um "Capability Registry" interno vier a ser construído — não resolve descoberta dinâmica em runtime por si só |

## 5. Classificação consolidada desta fase

| Item | Classificação |
|---|---|
| A2A (protocolo completo) | **REFERENCE** — maduro, mas resolve um problema (cross-org) que o repo não tem hoje |
| Padrão AgentCard isolado (O59) | **EXTRACT** |
| ACP (IBM/BeeAI) | **REJECT** — morto, arquivado, fundido no A2A |
| AGNTCY (Cisco) | **NOT VERIFIED** — não aprofundado nesta fase |
| FastMCP (padrões de composição) | **EXTRACT** |
| FastMCP (framework completo, substituindo `mcp/plan_runner`) | **DEFER** — trocaria um motor já testado (72 testes) sem resolver as lacunas identificadas |
| mcp-agent (padrões de orquestração) | **REFERENCE** |
| mcp-agent (como substituto de `ToolRegistry.ts`) | **REJECT** — mesma lacuna de autorização já documentada |
| Agente-como-servidor MCP (O66) | **ADOPT** como princípio de desenho (não como dependência) |
| MCP Registry oficial | **REFERENCE** |
| Elicitation/MRTR (spec 2026-07-28) | **ADAPT** — realinhar nomenclatura de `resume_plan`, sem reescrever |
| Sampling | **REJECT/DEFER** — a própria spec oficial deprecou-o |
| `packages/mcp/ToolExecutor` — pipeline de autorização | **BUILD** — confirmado, nenhuma biblioteca cliente madura resolve isto por nós |

## 6. Próxima fase

Fica para a Fase 3: Coding/Research agents (OpenHands — já identificado com 88.401★ na `FASE3-MEMORIA.md` secção 4, SWE-agent, Aider, browser-use), Evaluation (DeepEval, Ragas, Promptfoo, OpenAI Evals, Braintrust), Testing (unit/integration/regression para agentes), Agentes especializados por domínio (2.15, só depois de decidida a arquitectura de perfis/plugins discutida no início desta auditoria).
