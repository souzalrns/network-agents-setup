> **⚠️ ERRATA (2026-09-19):** o ponto 1 do Executive Summary e a secção 4 abaixo afirmam que `Orchestrator.ts` (TS) é MOCK. **Está errado** — verificado por leitura completa do ficheiro: liga Router→Planner→Executor de facto, com lógica real de segurança/deliberação/orçamento. Correção completa e cadeia do erro em `orchestration-audit/AUDIT-ORCHESTRATION.md`. A formulação correcta: o código é real dos dois lados (TS e Python); a diferença real é de **maturidade operacional** — o lado Python tem 167 testes que correm de facto, o lado TS tem código real mas nunca validado a correr contra infraestrutura de verdade (e um teste de integração com um bug de assinatura de construtor, por confirmar).

# AUDIT-AGENTS.md — Auditoria arquitectural profunda do ecossistema de agentes

## 1. Executive Summary

**A pergunta era: o que existe de alto padrão no ecossistema open source que este repo ainda não usa, e onde é que a nossa implementação já está à altura ou acima? A resposta, com código real por trás de cada linha: nenhum dos ~45 projetos/protocolos auditados foi classificado ADOPT ou ADAPT como substituto de runtime — e o maior achado desta auditoria não veio de nenhum deles. Veio de dentro.**

1. **O achado mais importante repete-se cinco vezes, em cinco fases diferentes, sem combinação prévia:** este repo tem peças reais e funcionais, desligadas umas das outras. `Planner.ts` (TypeScript) chama um LLM de verdade para escolher agentes e decompor tarefas — mas `Orchestrator.ts`, que devia ligá-lo a `Router.ts`/`Executor.ts` (ambos também REAIS), é MOCK. O motor Python `langgraph` já tem checkpoint real (`SqliteSaver`) e execução paralela por ondas — mas a tool MCP `run_plan` só invoca o motor `native`, sequencial e sem checkpoint. `yt-dlp`+`faster-whisper` já transcrevem vídeo em produção — mas nunca foram ligados ao pipeline de RAG. `budget_max_replans` existe no schema do plano — e nunca é lido em lado nenhum. Isto não é falta de tecnologia. É fiação.

2. **Nenhum dos 6 frameworks de agentes mais citados do mercado (Microsoft Agent Framework, Google ADK, OpenAI Agents SDK, LlamaIndex, DSPy, smolagents) foi classificado ADOPT ou ADAPT** — nem os 8 já avaliados antes desta auditoria (LangGraph, Agno, Timbal, CrewAI, PydanticAI, Mastra, AG2, Haystack). Todos são frameworks opinativos completos, cada um pensado para ser o runtime inteiro de quem os adota. O repo já tem dois runtimes próprios, incompletos mas reais — a decisão de não os substituir, tomada antes desta auditoria começar, sobreviveu a 14 verificações independentes.

3. **A implementação de referência das próprias empresas que desenham estes padrões falha da mesma forma que este repo falha.** O Google ADK teve um bug real em que a recusa humana não bloqueava a execução da tool (issue #7148, corrigido recentemente) — a mesma classe de falha que o `HitlManager.ts` deste repo tem hoje, e que o próprio motor `native` do `plan_runner` replica (decisão `edit` aceite mas sem efeito real). E `mcp-agent` (lastmile-ai, ~8,5k estrelas, a implementação mais citada dos padrões "Building Effective Agents" da Anthropic) **também não verifica scope/capacidade antes de chamar uma tool** — confirmando que a lacuna do `packages/mcp/ToolExecutor.ts` (já registada em `GOV-FASE1.md`) não tem correção externa disponível: nenhuma biblioteca cliente madura resolve isto, tem de ser construído.

4. **Duas correções feitas a alegações de terceiros, não escondidas:** a auditoria de memória (Fase 3) tinha citado `OpenHands/OpenHands` (88.401★) como referência de sandbox — mas o repositório principal já não é o runtime do agente, é uma app Electron de controlo; o loop real vive em `OpenHands/software-agent-sdk`, com apenas 1.134 estrelas e ~1 ano de idade. E a pendência "Ragas não verificado" da mesma auditoria foi resolvida: o projeto existe, com métricas de agente reais (`ToolCallAccuracy`), não vaporware.

5. **ACP (Agent Communication Protocol, IBM/BeeAI) está morto** — arquivado desde agosto de 2025, fundido no A2A. O A2A sobrevive e é maduro (25,6k estrelas, spec 1.0, adotado de fato por Google ADK e Microsoft Agent Framework), mas resolve um problema — comunicação entre agentes de organizações diferentes — que este repo não tem hoje; fica REFERENCE, não ADOPT.

6. **Veredicto final, sem ranking de "melhor ferramenta":** o trabalho de maior retorno imediato não é adotar nenhum dos ~45 projetos auditados — é ligar as peças já construídas (secção 4) e portar, internamente, os 3-4 padrões mais concretos e diretamente aplicáveis às lacunas já conhecidas (secção 6): `ToolCallAccuracy`/DeepEval para avaliação, o padrão de enforcement de HITL no boundary (confirmado em 3 fontes independentes), e o windowed-editor do SWE-agent para o agente de desenvolvimento.

## 2. Reconciliação de numeração de fases

Esta auditoria foi executada em 5 fases sequenciais (`FASE1`–`FASE5-AGENTES.md`), pela ordem real em que o trabalho foi feito. Uma proposta de agrupamento diferente foi sugerida a meio do processo; a tabela abaixo mapeia as duas, para que nada fique perdido entre nomenclaturas:

| Fase executada (este repo) | Conteúdo real | Fase proposta (agrupamento alternativo) |
|---|---|---|
| `FASE1-AGENTES.md` | Estado real do runtime próprio + Agent Frameworks (2.1) + Multi-Agent Architectures (2.2) + Runtime/Execution (2.3) + Planning (2.4) | Fase 1 — Núcleo de execução |
| `FASE2-AGENTES.md` | Tool Use (2.8, achado interno) + Agent Communication/A2A-ACP (2.10) + Ecossistema MCP (2.9) | Metade da Fase 3 (Skills/Tool/MCP) + metade da Fase 4 (Communication) |
| `FASE3-AGENTES.md` | Knowledge/Ingestion (2.6) | Fase 2 — Conhecimento e ingestão |
| `FASE4-AGENTES.md` | Evaluation (2.12) + Testing (2.13) | Metade da Fase 4 |
| `FASE5-AGENTES.md` | Coding/Research Agents (2.14) + Agentes Especializados (2.15) | Fase 5 |
| Este ficheiro | Síntese, matriz, veredictos, roadmap | Fase 6 — Síntese |

**Skills (2.7) e Observability (2.11, ângulo geral)** não foram refeitos em nenhuma fase — já cobertos por `docs/architecture/patterns-from-hermes/` (ciclo de vida de skills) e `docs/architecture/memory/FASE3-MEMORIA.md` secção 5 (Langfuse/OpenTelemetry/RAGAS), respectivamente. Repetir essa pesquisa seria o mesmo erro que esta auditoria evitou deliberadamente com `patterns-from-orchestrators/` na Fase 1.

## 3. Metodologia

"README serve para descoberta. Código é a evidência." — mesma disciplina de `GOV-FASE1-3`/`AUDIT-GOVERNANCE.md` e `FASE1-4-MEMORIA.md`. Toda alegação de maturidade/capacidade foi verificada por leitura direta de código-fonte (via WebFetch em ficheiros reais do GitHub), GitHub API (estrelas, atividade, contribuidores, issues), não por confiança em README/marketing. 22 pesquisas paralelas em subagentes cobriram 6 frameworks de agentes, 2 protocolos de comunicação, 3 projetos de ecossistema MCP, 12 ferramentas de ingestão de conhecimento, 6 frameworks de avaliação/teste, e 4 coding/research agents — cruzadas em todos os casos contra o estado real deste repo, verificado por leitura direta (não assumido).

## 4. O padrão recorrente: peças reais, desligadas

Confirmado, com evidência de código, em todas as 5 fases:

| Onde | Peça(s) real(is) | O que falta |
|---|---|---|
| `packages/core/src/orchestrator/` (TS) | `Router.ts`, `Planner.ts` (chama LLM de facto), `Executor.ts` — todos REAL | `Orchestrator.ts` que os liga é MOCK |
| `runner/plan_runner/` (Python) | Motor `langgraph`: checkpoint real (`SqliteSaver`), execução paralela por ondas | Não é o motor por omissão da CLI; tool MCP `run_plan` nem sabe que existe |
| `runner/plan_runner/` (Python) | HITL `edit` com payload real, via `--payload-file` | Só funciona no motor `langgraph`; motor `native` aceita `edit` sem efeito; tool MCP `resume_plan` nem expõe a opção |
| `runner/plan_runner/models.py` | `budget_max_replans` no schema do plano | Nunca é lido em nenhum motor — campo morto, sem replaneamento algum |
| Repo irmão `agent-network-mcp` | `yt-dlp`+`faster-whisper` já transcrevem vídeo em produção | Nunca ligado ao pipeline de RAG (`knowledge.py`/`chunking.py`) |
| `config/agents.config.ts` | 33 agentes já categorizados manualmente (`MCP-MAPPING.md`), 17 técnicas já extraídas para 16 skills | Nenhum campo `profile` no schema — a lição já aprendida não foi formalizada |

**Isto é o achado central desta auditoria.** Nenhuma das 5 fases foi desenhada para encontrar isto — apareceu de forma independente em cada uma, porque cada fase começou por auditar o estado real do repo antes de comparar com o exterior (a mesma disciplina de `GOV-FASE1`/`FASE1-MEMORIA`). O padrão é consistente demais para ser coincidência: este repo constrói peças de qualidade real e não as termina de ligar antes de passar à peça seguinte.

## 5. Matriz de capacidades — estado atual vs. o que o ecossistema já resolve

| Capacidade | Estado real neste repo | Melhor referência externa confirmada | Resolve por adoção directa? |
|---|---|---|---|
| Planning (decompor tarefa, escolher agentes) | REAL, mas desligado (`Planner.ts`) | Magentic Task/Progress Ledger (Microsoft Agent Framework, O21) | Não — falta ligar `Orchestrator.ts`, não adotar framework |
| Multi-agent handoff/delegação | Ausente — file-drop manual (`pending_steps/`) | `Handoff` tipado (OpenAI SDK), handoff-como-tool (LlamaIndex/ADK) | Não diretamente — nenhum caso de uso cross-org que justifique A2A |
| Checkpoint/resume | Real só no motor `langgraph`, local (não distribuído) | Nenhum framework resolve *distribuído* de verdade (nem o Microsoft Agent Framework — admitido pelo próprio maintainer) | Não — é limitação de todo o ecossistema, não só deste repo |
| HITL approve/reject/edit | `edit` só real no motor `langgraph`; MCP não expõe `edit` | `RunState` serializável (OpenAI SDK), `ToolConfirmation` (ADK) | Extrair padrão, não adotar |
| Autorização de tool antes de execução | Ausente em `packages/mcp/ToolExecutor.ts` | **Nenhuma** biblioteca cliente madura resolve isto (confirmado: nem FastMCP nem `mcp-agent`) | **Não — tem de ser construído internamente** |
| Ingestão de conhecimento | Só Markdown | MarkItDown (documentos), Crawl4AI (web), gitingest (código) | Sim, para os formatos — mas ligação ao pipeline continua trabalho próprio |
| Avaliação de comportamento de agente | Ausente (167 testes só cobrem o motor) | DeepEval (nativo pytest, local) + Ragas `ToolCallAccuracy` | Sim, diretamente adotável |
| Edição de código por agente | `desenvolvimento.agent.md` é só definição de prompt | Windowed editor do SWE-agent (2x SWE-Bench comprovado) | Extrair padrão (script isolável) |
| Agentes especializados por domínio | 24 agentes em lista plana, sem `profile` | Convergência de 4+ fontes (ADK, DSPy, Aider, proposta interna) para "perfis", não mais agentes | Não é adoção — é decisão de schema interno |

## 6. Matriz de classificação consolidada (todos os projetos/padrões auditados)

| Categoria | Item | Classificação |
|---|---|---|
| **Frameworks (Fase 1, novos)** | Microsoft Agent Framework | EXTRACT + REFERENCE |
| | Google ADK | EXTRACT |
| | OpenAI Agents SDK | EXTRACT |
| | LlamaIndex (agentes/workflows) | EXTRACT |
| | DSPy | EXTRACT (só a técnica de otimização) |
| | smolagents | EXTRACT |
| **Frameworks (já cobertos antes)** | LangGraph, Agno, Timbal, CrewAI, PydanticAI, Mastra, AG2, Haystack | Ver `patterns-from-orchestrators/` — não redecididos aqui |
| **Comunicação** | A2A | REFERENCE |
| | AgentCard (padrão isolado) | EXTRACT |
| | ACP | REJECT (morto) |
| | AGNTCY | NOT VERIFIED |
| **Ecossistema MCP** | FastMCP (padrões) | EXTRACT |
| | FastMCP (framework completo) | DEFER |
| | mcp-agent (padrões) | REFERENCE |
| | mcp-agent (como substituto de ToolRegistry) | REJECT |
| | Agente-como-servidor MCP | ADOPT (como princípio) |
| | MCP Registry oficial | REFERENCE |
| | Elicitation/MRTR (spec 2026-07-28) | ADAPT |
| | Sampling | REJECT/DEFER |
| **Conhecimento — Web** | Crawl4AI | ADOPT |
| | Trafilatura | ADOPT |
| | Firecrawl | DEFER |
| **Conhecimento — YouTube** | yt-dlp | ADOPT (já) |
| | faster-whisper | ADOPT (já) |
| | youtube-transcript-api | ADAPT |
| **Conhecimento — GitHub** | gitingest | ADOPT |
| | LlamaIndex/LangChain readers | EXTRACT |
| **Conhecimento — Documentos** | MarkItDown | ADOPT |
| | Docling | ADOPT (condicional) |
| | Unstructured | DEFER |
| **Conhecimento — Multimodal** | Tesseract | DEFER/REJECT |
| | OCR via VLM | REFERENCE |
| **Evaluation** | Ragas | ADAPT |
| | DeepEval | **ADOPT** |
| | Promptfoo | REFERENCE |
| | OpenAI Evals | REJECT |
| | Braintrust/`autoevals` | EXTRACT / REJECT (plataforma) |
| | Inspect AI | REFERENCE |
| **Testing** | `FakeListChatModel`-style mocking | ADOPT |
| | vcr-langchain / llm-vcr / mockagents | DEFER |
| | AgentBench / GAIA | REJECT (aplicação direta) |
| **Coding/Research Agents** | OpenHands (app) | REJECT |
| | OpenHands (`software-agent-sdk`) | EXTRACT |
| | SWE-agent | **ADAPT** |
| | Aider | REFERENCE |
| | browser-use | DEFER |
| **Interno** | `packages/mcp/ToolExecutor` — autorização | **BUILD** |
| | `AgentConfig.profile` | **BUILD** |
| | Ligar `Orchestrator.ts` a Router/Planner/Executor | **BUILD** (fiação, prioridade 0) |
| | Ligar `yt-dlp`/`faster-whisper` ao RAG | **BUILD** (fiação) |
| | Expor motor `langgraph`+`edit` via MCP | **BUILD** (fiação) |

## 7. Arquitetura recomendada — o que fazer primeiro

```
FASE 0 — FIAÇÃO (maior retorno, zero dependência nova)
  │
  ├── Ligar Orchestrator.ts a Router.ts + Planner.ts + Executor.ts (TS)
  ├── Expor --engine langgraph e decision=edit via mcp_plan_runner (Python)
  ├── Ligar yt-dlp/faster-whisper (já existentes) ao pipeline de RAG
  └── Adicionar campo `profile` a AgentConfig (schema, TS)
                           │
                           ▼
FASE 1 — LACUNAS DE SEGURANÇA/QUALIDADE JÁ CONHECIDAS
  │
  ├── packages/mcp/ToolExecutor: portar sanitize→auth→rate→scope→execute→audit
  │   (já testado em mcp/plan_runner/policy.py) — confirmado sem alternativa externa
  ├── DeepEval + Ragas ToolCallAccuracy no runner/plan_runner (pytest, local)
  └── FakeListChatModel-style mocking nos testes de nós do grafo
                           │
                           ▼
FASE 2 — EXTRAÇÃO DE PADRÕES PONTUAIS (sem adoptar frameworks)
  │
  ├── Windowed editor (SWE-agent) → desenvolvimento.agent.md
  ├── StuckDetector (OpenHands SDK) → executor.py
  ├── ToolConfirmation/RunState (ADK/OpenAI SDK) → HitlManager.ts + hitl.py
  └── MarkItDown/Crawl4AI/gitingest → pipeline de ingestão (novos formatos)
                           │
                           ▼
FASE 3 — SÓ SE/QUANDO A NECESSIDADE SURGIR (não construir antecipadamente)
  │
  ├── A2A — só se um agente de terceiros/outra organização precisar de ser exposto/consumido
  ├── browser-use — só se surgir um agente que precise de controlar UI web
  └── Docling/OCR — só se extração de tabelas em PDF ou documentos escaneados for requisito real
```

## 8. Donos de responsabilidade

| Responsabilidade | Dono recomendado |
|---|---|
| Ligar Router→Planner→Executor (`Orchestrator.ts`) | Trabalho próprio — nenhum framework externo substitui esta fiação |
| Autorização de tool (`packages/mcp/ToolExecutor`) | Portar `mcp/plan_runner/policy.py` (já testado) — confirmado, sem alternativa externa madura |
| Avaliação de comportamento de agente | DeepEval (adotar) + Ragas `ToolCallAccuracy` (adaptar, sem LLM-judge) |
| Ingestão — Web | Crawl4AI + Trafilatura |
| Ingestão — Documentos | MarkItDown por omissão; Docling só se tabelas em PDF forem requisito |
| Ingestão — GitHub | gitingest (código) + script próprio contra API REST (issues/PRs) |
| Edição de código por agente | Padrão SWE-agent (windowed editor), portado, não a dependência |
| Comunicação entre agentes (hoje) | Continua o file-drop (`pending_steps/`), reforçado com vocabulário A2A (Task states, Artifact/Parts) sem montar servidor |
| Comunicação entre agentes (cross-org, futuro) | A2A, se/quando surgir esse caso de uso |
| Schema de especialização (`profile`) | Trabalho próprio de schema — decisão humana pendente, método já validado em `MCP-MAPPING.md` |

## 9. Riscos

- **Nenhuma das verificações desta auditoria testou os padrões extraídos dentro deste repo** — é avaliação estática do ecossistema externo + leitura de código próprio, não implementação nem teste de integração. Tal como as auditorias de memória e governança.
- **A2A e AGNTCY são projetos jovens sob uma fundação (AAIF) criada há menos de um ano** — a governança pode mudar; reavaliar antes de qualquer adoção futura, não assumir que o estado descrito aqui é permanente.
- **A spec MCP 2026-07-28** (elimina handshake, depreca Sampling/Roots/Logging/DCR) foi confirmada por fetch direto e ultrapassa o conhecimento base do modelo — recomenda-se confirmação humana antes de qualquer decisão de arquitetura HTTP+OAuth que dependa especificamente destes detalhes.
- **Aider e faster-whisper mostram sinais de abrandamento de manutenção** (4 e ~10 meses sem commit, respectivamente) — não depender deles assumindo atividade contínua sem reverificar periodicamente.
- **A lista de ~45 projetos classificados aqui data de 2026-09-18/19** — maturidade e estrelas mudam; esta síntese é uma fotografia, não uma verdade permanente.

## 10. Questões não resolvidas

1. **`packages/mcp/` (TS) vs. `mcp/plan_runner/` (Python)** — qual fica, qual se descontinua, ou fundem-se? Já identificado em `GOV-FASE1.md`, ainda sem decisão. Esta auditoria de agentes encontrou o mesmo tipo de duplicação na camada de planeamento (TS `Planner.ts` com LLM real vs. Python `plan.yaml` sem LLM) — reforça a urgência da decisão, não a resolve.
2. **AGNTCY (Cisco)** não foi aprofundado com a mesma profundidade que A2A/ACP — se algum dia a necessidade de identidade cross-org/mensageria surgir, falta essa parte da auditoria.
3. **A lacuna de "direcionamento e planejamento"** que abriu esta auditoria (falta de um PMO/Project Director que defina escopo, desmembre em fases, execute uma a uma) continua sem resposta técnica — nenhum dos ~45 projetos auditados nas 5 fases se propõe a ser isso. `agents/meta/planejador.agent.md` e `orchestrator/Planner.ts` cobrem planeamento de *uma tarefa*; nenhum cobre gestão de *portfólio de iniciativas*. É decisão humana de arquitetura organizacional, não uma lacuna que uma Fase 7 de pesquisa resolveria — mais pesquisa não vai encontrar um "framework de PMO" que sirva, porque o problema não é técnico.

---

**Nada ficou por decidir sem razão declarada.** As 3 questões acima dependem de decisão humana (1, 3) ou de uma leitura ainda não feita (2) — não de evasão. A auditoria está completa quanto ao que foi pedido: descobrir, verificar, classificar. A decisão de o que integrar, e em que ordem, é a Fase 0 da secção 7 — e essa, com a evidência já reunida, pode começar amanhã sem esperar por nenhuma pesquisa adicional.
