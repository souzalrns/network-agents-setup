# DSPy (Stanford NLP, `stanfordnlp/dspy`) — auditoria profunda

Repositório: https://github.com/stanfordnlp/dspy. Auditoria por leitura direta de código-fonte, `pyproject.toml`, GitHub API, SECURITY.md/LICENSE.

**Nota de enquadramento:** DSPy é fundamentalmente diferente dos outros frameworks desta fase (LangGraph, Agno, CrewAI, ADK, etc.) — é um framework de "programação declarativa de prompts" com otimização automática, não um orquestrador de agentes. Não forçar comparação direta onde não faz sentido.

## 1. Tabela de capacidades

| Capacidade | O que o projeto alega | Evidência verificada (link) | Validado? |
|---|---|---|---|
| Identidade do projeto | "Framework for programming — not prompting — language models" | [README.md](https://github.com/stanfordnlp/dspy/blob/main/README.md): "Iterating quickly on building modular AI systems... optimizing prompts and weights... support for classifiers, RAG pipelines, and Agent loops" | Confirma: é otimização declarativa de programas de LM, "Agent loops" é caso de uso suportado, não o produto central |
| `Signature` = contrato I/O declarativo | Substitui prompt string por classe tipada | [`dspy/signatures/signature.py`](https://github.com/stanfordnlp/dspy/blob/main/dspy/signatures/signature.py): `class MySignature(dspy.Signature): input: str = InputField(); output: str = OutputField()`; docstring vira instruções; fallback automático | Sim — DTO de prompt com metadados, reutilizável e transformável (`with_instructions`, `append_instructions`) |
| `Module` = unidade composável | Módulos compõem-se em pipelines/"programas" | [`dspy/primitives/module.py`](https://github.com/stanfordnlp/dspy/blob/main/dspy/primitives/module.py): `named_predictors()`/`named_parameters()` descobrem `Predict` aninhados por atributo; `set_lm()`/`get_lm()` propagam LM à árvore | Sim — composição por atribuição de atributos Python + reflexão (parecido a `nn.Module` do PyTorch), não um DAG explícito |
| `dspy.ReAct` = módulo agentic | Suporta "Agent loops" com ferramentas | [`dspy/predict/react.py`](https://github.com/stanfordnlp/dspy/blob/main/dspy/predict/react.py): loop `for idx in range(max_iters)`, gera `next_thought`/`next_tool_name`/`next_tool_args`, executa a tool, acumula `trajectory`, termina em `"finish"` ou `max_iters` (default 20) | Sim, real — mas single-agent, sem HITL nem checkpoint |
| Multi-agente nativo | Não alegado explicitamente | [`parallel.py`](https://github.com/stanfordnlp/dspy/blob/main/dspy/predict/parallel.py) executa o **mesmo** módulo sobre inputs diferentes em threads — não é orquestração entre agentes distintos. Sem `Team`/`Handoff`/`Crew` no core | Confirmado **ausente no core** — comunidade constrói multi-agente por cima (`dspy-multi-agent`, `Agenspy`), não o DSPy em si |
| Runtime/execução | — | `forward()`/`aforward()` síncrono e assíncrono; `__getstate__`/`__setstate__` excluem `history`/`callbacks` — serve para checkpoint de módulo *treinado* (pesos/demos), não de execução em curso | Confirmado: essencialmente **stateless/funcional por invocação**, sem state machine, sem HITL, sem resume de chamada interrompida |
| Compiler `BootstrapFewShot` | Otimiza demos few-shot automaticamente | [`dspy/teleprompt/bootstrap.py`](https://github.com/stanfordnlp/dspy/blob/main/dspy/teleprompt/bootstrap.py): "teacher" corre até `max_rounds` vezes por exemplo, `temperature=1.0` nas rondas seguintes para diversidade; filtra por `metric(example, prediction, trace)`; popula `demos` do `student` | Validado, real e funcional |
| Compiler `MIPROv2` | Otimização Bayesiana de instruções + few-shot | [`dspy/teleprompt/mipro_optimizer_v2.py`](https://github.com/stanfordnlp/dspy/blob/main/dspy/teleprompt/mipro_optimizer_v2.py): `optuna.samplers.TPESampler(multivariate=True)`; 3 fases (bootstrap demos → propor instruções → otimizar via TPE); custo declarado em nº de chamadas LLM ("light" ~100, "heavy" ~1000) | Validado, real e funcional; depende de extra opcional `optuna`, sem docstring de produção na classe principal |
| Planning / decomposição explícita | Não alegado | Nenhum módulo `Planner`/`TaskDecomposer` em `dspy/predict/` (`predict, chain_of_thought, react, react_v2, program_of_thought, code_act, multi_chain_comparison, best_of_n, refine, retry, parallel, knn, aggregation, rlm`) | Confirmado ausente — decomposição é implícita via reasoning, não plano estruturado separado |
| Maturidade do projeto | Ativo e maduro | API GitHub: **38.121 estrelas**, 3.322 forks, 706 issues abertas, criado 2023-01-09, último push 2026-09-18, 152+ contribuidores, top `okhat` (Omar Khattab) com 1.129 commits | Validado |
| Uso em produção | "Dozens" de empresas (Shopify, Databricks, Dropbox, JetBlue, Moody's, Replit, AWS, Sephora, VMware) | [`docs/docs/production/index.md`](https://github.com/stanfordnlp/dspy/blob/main/docs/docs/production/index.md) lista os nomes sem link a case study independente por empresa | **Parcial** — auto-reportado; existe ao menos 1 case study de terceiros (AlixPartners, via ZenML LLMOps Database) |
| Licença e comercial | MIT | `LICENSE`: MIT, copyright Stanford Future Data Systems, 2023 | Validado |
| Segurança | Processo de disclosure | `SECURITY.md`: reporte privado via GitHub, contacto `isaac@dspy.ai` | Validado |
| Agnóstico a provider LLM | Sim | `pyproject.toml`: core `litellm>=1.65.8` + `openai>=1.66.2` base; extras `anthropic`, `mcp`, `langchain`, `weaviate`, `optuna`, `deno` | Validado — corre local, agnóstico via LiteLLM |
| Curva de aprendizagem | — | Fontes secundárias descrevem 2026 como o ano em que "most teams hit a ceiling with manual prompt engineering" antes de adotar DSPy | **NÃO VERIFICADO por código** — inferência qualitativa |

## 2. Padrões extraíveis

1. **`Signature` como contrato tipado de I/O de prompt** — separa "o que o LM deve produzir" (campos, tipos, descrições) de "como o prompt é montado". Os contratos Plan-Execute já têm essa intenção; DSPy mostra forma concreta de a tornar reutilizável via classes Python.
2. **Composição de módulos por reflexão de atributos** (`named_predictors()`/`named_parameters()`) — padrão leve para descobrir sub-componentes optimizáveis sem registo central explícito.
3. **`BootstrapFewShot`: geração automática de demonstrações via "teacher rollout" + filtro por métrica** — o padrão mais valioso e extraível: gerar N execuções do próprio agente contra dados reais, aceitar só as que passam uma métrica de sucesso, usar como few-shot. Diretamente portável para otimizar prompts dos próprios agentes contra métricas de produção (ex. taxa de sucesso do `plan_runner`), sem precisar do resto do DSPy.
4. **Otimização Bayesiana de instruções (MIPROv2, via Optuna TPE)** — separa "gerar candidatos" de "avaliar combinações", com orçamento de chamadas LLM explícito por modo.
5. **Truncamento de trajetória em agentes de loop (`ReAct`)** — ao rebentar o context window, remove os passos mais antigos em blocos de 4, até 3 tentativas, antes de falhar.
6. **Serialização seletiva de estado treinado** (`__getstate__`/`__setstate__` excluindo `history`/`callbacks`) — separa "o que foi otimizado" de "ruído de execução" no checkpoint.
7. **Custo de otimização declarado explicitamente antes de correr** — padrão de transparência de custo copiável para qualquer auto-tuning contra LLMs de produção.

## 3. Classificação e porquê

**EXTRACT — técnica de otimização de prompts (`BootstrapFewShot`/MIPROv2 + o padrão Signature) — não adotar o framework inteiro.**

DSPy não é um substituto do runtime Plan-Execute nem do MCP produção Python — é ortogonal. Não há noção de handoff/team/state machine de execução/checkpoint/HITL (confirmado pela ausência de `Team`/`Handoff` no core). O que é genuinamente maduro e único é o mecanismo de otimização (`BootstrapFewShot`, `MIPROv2`): código real, testado, usado em produção por terceiros (38k estrelas, ritmo diário, 152+ contribuidores, MIT), mas não "enterprise polished" (MIPROv2 depende de extra opcional, sem docstring de produção). Adotar o framework inteiro implicaria reescrever os agentes como `dspy.Module`/`dspy.Signature` — contradiz a diretiva de manter contratos próprios. Extrair só o algoritmo de bootstrap de few-shot + filtro por métrica é possível sem essa reescrita, usando `events.jsonl` já existente como fonte de traces.

## 4. O que NÃO adotar

- `dspy.Module`/`dspy.Signature` como camada de definição de agentes — substituiria o contrato Plan-Execute próprio.
- Tratar DSPy como solução de orquestração multi-agente — não tem `Team`/`Handoff`/state machine nativos; "multi-agente" à volta do DSPy vem de projetos de terceiros não-oficiais.
- Adotar `ReAct` como motor de execução de produção sem adaptação — sem HITL nem checkpoint/resume.
- Depender da lista de "empresas em produção" como validação de robustez — auto-reportada, sem case study verificável por empresa (exceção parcial: AlixPartners).
- Adotar MIPROv2 tal como está para otimização contínua sem orçamento avaliado — modo "heavy" pode custar ~1000 chamadas LLM de validação por otimização.
