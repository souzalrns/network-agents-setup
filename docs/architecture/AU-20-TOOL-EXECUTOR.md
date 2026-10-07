# AU-20: contrato do executor de tools do worker (PROPOSTA, contract-first §15.4)

**Estado:** contrato aprovado. **P-37 = B decidida pelo maestro** (executor mínimo em Python dentro do `plan_runner`, D1). Ainda **não há código**: é o próximo passo do AU-20.
**Pré-requisito feito:** `activate_for_task` + SEC-1.3 (`docs/ops/SKILL-ACTIVATION.md`, merge do #123).
**Governança:** ISO/IEC 42001 (P-40), ver a secção "ISO/IEC 42001" abaixo.
**Hoje:** o worker faz uma única chamada Gemini `generateContent` sem `tools` (`runner/plan_runner/external_worker.py`, `gemini_generate`), e o prompt diz "Nao tens tools neste passo". `tools_allowed` é só declarativo (`models.py`, `executor.py`).

## Padrões maduros que este contrato segue

| Padrão | Fonte | Como entra aqui |
|---|---|---|
| Tecto de pedidos e de tool calls por run | pydantic-ai `UsageLimits` (`request_limit`, por omissão 50; `tool_calls_limit`) | `max_turns` + `max_tool_calls` por passo, com estado `paused_budget` igual ao dos tokens (BUDGET.md) |
| Tools que precisam de aprovação terminam o run e retomam depois | pydantic-ai *deferred tools* (`requires_approval` → `DeferredToolRequests` → novo run com `DeferredToolResults`); OpenAI Agents SDK `needs_approval` | nível `act` → o passo pára no HITL existente (`hitl.py`, `paused_human_gate`); o resume injecta o resultado aprovado |
| Guardrails de input/output por tool | OpenAI Agents SDK *tool guardrails* | validação JSON Schema dos args **antes** e redacção/limite do output **depois** |
| Precedência deny > ask > allow | modelo de permissões do Claude Code | `tools_allowed` do passo ∩ registo ∩ policy; deny ganha sempre |
| Registo + auth + rate limit + audit com hash dos params | `packages/mcp/src/tools/ToolExecutor.ts` (TS arquivado, D1) | portado o **desenho**, não o runtime |
| Skills com scripts tratadas como software de terceiros | OWASP Agentic Skills Top 10; Agent Skills spec (`allowed-tools`) | qualquer tool que execute script consulta `is_script_allowed()` (SEC-1.3) |
| Function calling nativo | Gemini API `tools.functionDeclarations`, `toolConfig.functionCallingConfig` (`AUTO`/`ANY`/`NONE`, `allowedFunctionNames`), partes `functionCall` → `functionResponse` | só se declaram ao modelo as tools autorizadas no passo (`allowedFunctionNames` = intersecção) |

A confirmar no primeiro PR de código, contra a documentação oficial do Gemini: a devolução das *thought signatures* nas partes `functionCall` (modelos 2.5/3) e o formato exacto do `id` das chamadas paralelas. Nesta sessão a documentação não estava acessível (egress); não se inventa o formato.

## Os 10 itens do §15.4

1. **Contrato.** `run_tool_loop(request, step, activation, registry, limits) -> LoopResult`. Corre **dentro** de `GeminiWorker.process` (sem 2.º runtime, D1). O passo **sem** `tools_allowed` executa exactamente como hoje (single-shot): é um teste de regressão obrigatório.
2. **Input schema.** Cada tool regista `name`, `description`, `parameters` (JSON Schema, subconjunto OpenAPI aceite pelo Gemini), `level` (`read`/`prepare`/`act`), `timeout_s`, `max_output_chars`. Primeiras tools (todas `read`):
   - `read_repo_file(path)`: reutiliza `repo_files.py` (denylist, 50 KB, sem symlinks para fora);
   - `retrieve_knowledge(query, kb)`: reutiliza `McpKnowledge` (L5, v2 com proveniência).
3. **Output schema.** `{ok: bool, content: str|object, truncated: bool, error?: str}` → parte `functionResponse` com `name` (e `id` quando o modelo o enviar).
4. **Policy.** Autorizado = `step.tools_allowed` ∩ registo ∩ nível permitido na área. `act` exige HITL (§15.5). Tool desconhecida ou não autorizada → `functionResponse` com `error: "tool_not_allowed"`, **sem** executar; o modelo nunca vê tools fora da intersecção.
5. **Provenance.** Cada chamada gera um evento `tool_called` em `events.jsonl`: `step_id`, `tool`, `sha256(args canónicos)`, duração, bytes, `ok`, e `sources` (paths ou `citation.uri` do L5). Os args em claro não vão para eventos.
6. **Estados de erro.** `tool_not_allowed`, `invalid_args` (o schema falhou), `timeout`, `tool_error`, `output_truncated`, `max_turns`, `max_tool_calls`, `budget_exceeded`. Os quatro primeiros voltam ao modelo como `functionResponse` (o loop continua). Os três últimos param o passo: `max_turns` e `max_tool_calls` → `waiting_external` com `worker_error`; `budget_exceeded` → `paused_budget`.
7. **Validação.** JSON Schema dos args antes de executar; paths normalizados; testes com Gemini falso (transport injectável, como hoje), sem rede.
8. **Observabilidade.** `result.json → meta.tools`: lista por chamada (tool, ok, ms, bytes, hash). `tokens_in`/`tokens_out` somados por turno. O resumo do run mostra as tools usadas por passo.
9. **Custo/budget.** Cada turno conta para o tecto de tokens da área (BUDGET.md). Por omissão `max_turns = 6` e `max_tool_calls = 12`, configuráveis por passo (`tool_limits:`). Ao atingir o tecto, pára **antes** de pedir mais um turno.
10. **Fronteira de segurança.** Tools `read` não escrevem nem fazem rede fora do MCP/Supabase de leitura já existentes. O output de uma tool entra no prompt como **dados**, numa secção marcada, e nunca como instrução (prompt injection). Scripts de skills só correm se `is_script_allowed()` for verdadeiro, **e** num processo filho com timeout e sem env de segredos (o padrão do T6d). Nenhuma tool `act` antes de idempotência + rollback (§15.6).

## ISO/IEC 42001 (P-40): controlos do executor ↔ norma

Alinhamento voluntário, não certificação. A política é `docs/governance/AI-MANAGEMENT-SYSTEM.md` e o mapeamento completo é `docs/governance/ISO-42001-MAPPING.md`. Os números são da ISO/IEC 42001:2023, com títulos em tradução livre. Hoje A.4.4 e A.6.2.6 estão `Parcial` por causa deste item (AU-20). Passam a `Cumpre` só com a evidência do código e dos testes do executor.

| Controlo do executor (itens do §15.4 acima) | Cláusula / controlo | Evidência esperada quando implementado |
|---|---|---|
| Tools autorizadas = `step.tools_allowed` ∩ registo ∩ nível da área; deny ganha; o modelo só vê a intersecção (`allowedFunctionNames`) | A.9.2 (uso responsável), A.6.2.5 (implantação), 6.1.3 (tratamento de risco) | teste: tool fora da intersecção → `tool_not_allowed`, sem executar |
| Nível `act` só depois de aprovação humana (pára no HITL, retoma com o resultado aprovado) | A.9.2, A.9.4 (uso previsto), 8.3 (tratamento na operação) | teste: `act` sem decisão → `paused_human_gate`; registo no `hitl-requests.jsonl` |
| Validação JSON Schema dos argumentos antes de executar | A.6.2.4 (verificação e validação) | teste: args inválidos → `invalid_args`, tool não chamada |
| Evento `tool_called` por chamada (tool, hash dos args canónicos, ms, bytes, `ok`, `sources`); args em claro fora dos eventos | A.6.2.8 (registos de eventos), 9.1 (monitorização), A.7.5 (proveniência) | teste: o evento existe e não contém os args em claro |
| `max_turns`, `max_tool_calls`, tecto de tokens/USD da área; pára antes de pedir mais um turno | A.4.5 (recursos de computação), A.6.2.6 (operação e monitorização) | teste: o tecto é atingido → `waiting_external` / `paused_budget` sem chamada extra |
| Output da tool entra como **dados** numa secção marcada, nunca como instrução | 6.1.2 (risco identificado: prompt injection), A.6.1.3 | teste: output com "ignora as instruções" fica dentro da secção de dados |
| Scripts de skills só com `is_script_allowed()` e `pins:` a conferir; processo filho com timeout e sem env de segredos | A.4.4 (recursos de ferramentas), A.10.3 (fornecedores), A.7.5 | teste: script bloqueado → recusado; pin errado → todos bloqueados |
| Skills externas: candidatas com revisão humana, nunca instaladas | A.10.3 | já coberto pelo SEC-1.3 (`runner/tests/test_skill_activation.py`) |
| Erros tipados (`tool_not_allowed`, `invalid_args`, `timeout`, `budget_exceeded`…) contados por run | A.8.4 (incidentes), 10.2 (não conformidade) | `result.json → meta.tools`; um padrão repetido vira item no PENDENCIAS |

**Regra do AIMS para cada tool nova** (`AI-MANAGEMENT-SYSTEM.md` §2, ponto 7): o contract-first só fica completo com uma linha de risco no `PENDENCIAS.md` (6.1.2) e uma linha na Declaração de Aplicabilidade (`ISO-42001-MAPPING.md`). O teste `runner/tests/test_governance_mapping.py` falha se o mapeamento citar evidência que não existe.

## Opções do P-37 (decidida: B)

| Opção | O quê | Custo | Risco |
|---|---|---|---|
| A | Portar o `ToolExecutor.ts` para Node e chamá-lo do worker | 2.º runtime (viola D1) | alto |
| **B (DECIDIDA)** | Executor mínimo em Python no `plan_runner`, com as 2 tools `read` acima e o loop de function calling Gemini | ~1 módulo + testes; custo zero de infra | baixo: tudo opt-in por `tools_allowed`; sem ele, nada muda |
| C | Adoptar pydantic-ai (MIT) como motor do loop | dependência nova + 2.º modelo de execução ao lado do LangGraph | médio: duplica o B3/D1 |

Evidência para o B: o worker já tem transport injectável, `BudgetExceeded`, HITL e eventos. A diferença é um loop de no máximo `max_turns` à volta do `gemini_generate` existente, mais um registo de 2 tools que reutilizam código já testado (`repo_files.py`, `mcp_knowledge.py`).
