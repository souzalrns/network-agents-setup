# AU-20: contrato do executor de tools do worker (PROPOSTA, contract-first §15.4)

**Estado:** proposta. **Não há código.** À espera da decisão do maestro no **P-37** (recomendação B: executor mínimo em Python dentro do `plan_runner`, D1).
**Pré-requisito feito:** `activate_for_task` + SEC-1.3 (`docs/ops/SKILL-ACTIVATION.md`).
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

## Opções para o P-37 (inalteradas, só detalhadas)

| Opção | O quê | Custo | Risco |
|---|---|---|---|
| A | Portar o `ToolExecutor.ts` para Node e chamá-lo do worker | 2.º runtime (viola D1) | alto |
| **B (RECOMENDADA)** | Executor mínimo em Python no `plan_runner`, com as 2 tools `read` acima e o loop de function calling Gemini | ~1 módulo + testes; custo zero de infra | baixo: tudo opt-in por `tools_allowed`; sem ele, nada muda |
| C | Adoptar pydantic-ai (MIT) como motor do loop | dependência nova + 2.º modelo de execução ao lado do LangGraph | médio: duplica o B3/D1 |

Evidência para o B: o worker já tem transport injectável, `BudgetExceeded`, HITL e eventos. A diferença é um loop de no máximo `max_turns` à volta do `gemini_generate` existente, mais um registo de 2 tools que reutilizam código já testado (`repo_files.py`, `mcp_knowledge.py`).
