# Auditoria de Agentes — Fase 4: Evaluation + Testing

Continuação de `FASE1`–`FASE3-AGENTES.md`. Communication (A2A/ACP) já coberta em `FASE2-AGENTES.md`; Observability já coberta em `memory/FASE3-MEMORIA.md` secção 5 (Langfuse, OpenTelemetry, RAGAS "não verificado" na altura — pendência resolvida aqui, secção 3). Esta fase cobre o que restava: Evaluation (2.12) e Testing (2.13).

## 0. Baseline interna confirmada

`grep` no repo inteiro confirma **zero referências** a `ragas`, `deepeval`, `promptfoo`, `agentbench`, `gaia`, `braintrust` ou `autoeval`. Os 167 testes reais do `runner/plan_runner` (87% cobertura, `STATUS.md`) cobrem o **motor** (grafo, budget, HITL resume) — nada avalia o **comportamento** dos agentes (qualidade de resposta, correção de trajetória de tool-use, hallucination). O gap é real e total.

## 1. Evaluation

| Ferramenta | Estrelas/Licença/Atividade | O que mede de facto (verificado no código) | Local sem API paga? | Classificação |
|---|---|---|---|---|
| **Ragas** (`explodinggradients/ragas`) | 15,8k★, Apache-2.0, ativo | Confirmado no código-fonte (`_tool_call_accuracy.py`): `ToolCallAccuracy` compara sequência de tool calls prevista vs. referência, `_get_arg_score()` campo a campo — lógica real, não stub. Também `ToolCallF1`, `AgentGoalAccuracy*` (LLM-judge, trajetória multi-turno) | Sim, judge via Ollama/qualquer provider | **ADAPT** — usar `ToolCallAccuracy`/`ToolCallF1` (sem LLM-judge, grátis) desde já |
| **DeepEval** (`confident-ai/deepeval`) | 18,3k★, Apache-2.0, muito ativo | Integra-se nativamente com `pytest`; métricas dedicadas a agente (Task Completion, Tool Correctness, Argument Correctness, Goal Accuracy, Step Efficiency, Plan Adherence) via `evals_iterator()` que captura a trajetória completa. Integrações diretas com LangGraph/CrewAI/OpenAI Agents | Sim, judge 100% local via Ollama/LM Studio/vLLM | **ADOPT** — candidato mais maduro: nativo em pytest (já usado neste repo), cobre trajetória, sem API paga |
| **Promptfoo** (`promptfoo/promptfoo`) | 25,3k★, MIT, muito ativo | Regressão declarativa (YAML) em CI, multi-turno, red-teaming de agentes | Sim, 100% local | **REFERENCE** — boa camada de regressão em CI, menos granular que DeepEval para trajetória interna |
| **OpenAI Evals** (`openai/evals`) | 19,5k★, MIT | **Semi-abandonado** — hiato real Set/2024→Nov/2025, sem features novas desde então; README redireciona para o produto pago do Dashboard, "não aceita evals com código customizado" | Sim tecnicamente | **REJECT** |
| **Braintrust** (`braintrustdata/*`) | Control plane proprietário/SaaS; só `autoevals` (1,0k★, MIT) é real e standalone | `autoevals`: LLM-as-judge (Factuality, Summarization, Security) + heurísticas (Levenshtein, BLEU), funciona sem a plataforma | `autoevals` sim; plataforma não (self-host só Enterprise pago) | **EXTRACT** (`autoevals`) / **REJECT** (plataforma) |
| **Inspect AI** (`UKGovernmentBEIS/inspect_ai`) | 2,8k★, MIT, mantido pelo UK AI Security Institute | Model-graded scoring, tool-use, multi-turn, +200 evals pré-construídas, harness oficial do GAIA | Sim | **REFERENCE** — provavelmente a implementação de LLM-judge mais rigorosa/auditável avaliada (proveniência de AI safety governamental, não vendor comercial), mas curva de adoção maior |

**LLM-as-judge mais maduro:** Inspect AI e Ragas têm as implementações mais estruturadas (decompõem em claims/scorers verificáveis, não "pede a outro LLM sem estrutura"); DeepEval é o mais pragmático para uso imediato (acoplado a `pytest`).

## 2. Testing

| Padrão/Ferramenta | Estado real verificado | Classificação |
|---|---|---|
| **Mocking determinístico de LLM** (`langchain_core...fake_chat_models`: `FakeListChatModel`, `GenericFakeChatModel`) | Confirmado por leitura direta: 5 classes totalmente implementadas, com streaming/callbacks/ciclo de respostas configurável — é o padrão de facto do próprio LangChain/LangGraph nos seus testes internos | **ADOPT** — replicável no runner Python para testar nós do grafo LangGraph deterministicamente, grátis |
| **Replay determinístico (cassette/VCR)** — `vcr-langchain`, `llm-vcr`, `mockagents` | `vcr-langchain`: só 82★, o próprio autor admite cobertura incompleta. Os outros são pequenos, sem tração, ainda v0.x | **DEFER** — conceito correto, nenhuma ferramenta pronta madura; implementar internamente com `FakeListChatModel`-style + fixtures JSON |
| **AgentBench** (`THUDM/AgentBench`) | 3,7k★, Apache-2.0. Suite fixa de 8 ambientes para comparar LLMs entre si — não desenhado para importar o agente próprio | **REJECT** para aplicação direta / **REFERENCE** metodológica |
| **GAIA** (HuggingFace) | Dataset gated, 466 tarefas — domínio genérico (busca web, PDFs, planilhas), sem sobreposição com tarefas de rede/PCU | **REJECT** para aplicação direta / **REFERENCE** de leitura |

## 3. Pendência da auditoria de Memória — Ragas: resolvida

`FASE3-MEMORIA.md` (linha 65) registou: *"RAGAS — NÃO VERIFICADO — a busca pelo repo esperado não devolveu dados"*. Confirmado agora por WebFetch direto: o repositório existe (`explodinggradients/ragas`, 15,8k★, Apache-2.0), com métricas de agente reais e funcionais (não vaporware) — a falha anterior foi provavelmente pontual de busca, não de existência do projeto.

## 4. Recomendação mínima

1. **DeepEval** via `pytest` no `runner/plan_runner` — `Tool Correctness`+`Argument Correctness` para chamadas de tools, `assert_test` para qualidade de resposta num golden-set pequeno (10-20 cenários reais). Local via Ollama, zero custo de judge em desenvolvimento.
2. **Mocking estilo `FakeListChatModel`** nos testes unitários dos nós do grafo — determinístico, grátis, padrão já comprovado pelo próprio LangGraph.
3. **`ToolCallAccuracy`/`ToolCallF1` do Ragas** como segunda camada, sem exigir LLM-judge (métrica determinística).
4. **Fixtures de trajetória gravadas manualmente** (input → sequência esperada de tool calls → output) — substitui a necessidade de ferramenta de replay ainda imatura no mercado.

## 5. O que NÃO adotar

- OpenAI Evals — manutenção mínima, foco migrado para produto pago.
- Braintrust (plataforma) — SaaS proprietário; só `autoevals` vale extrair.
- `vcr-langchain`/`llm-vcr`/`mockagents` — imaturos, baixa tração; não depender em CI.
- AgentBench/GAIA como suites a "rodar directamente" — domínios sem sobreposição com o repo.
- Promptfoo como substituto do DeepEval — bom complemento de regressão em CI, não tem a granularidade de trajetória interna já confirmada em DeepEval/Ragas.
