# AU-20: contrato do executor de tools do worker (contract-first §15.4)

**Estado:** **implementado atrás de uma flag** (`PLAN_RUNNER_TOOLS=1`, desligada por omissão). P-37 = B decidida pelo maestro: executor mínimo em Python dentro do `plan_runner` (D1). Código em `runner/plan_runner/tool_executor.py`, ligado em `external_worker.py`. Testes em `runner/tests/test_tool_executor.py` (45, Gemini falso). Ver "Implementação" no fim. **Seguimento (2026-10-07, decisão do maestro):** o nível `act` pára no HITL chamada a chamada, e o `retrieve_knowledge` só usa os kb permitidos ao passo.
**Pré-requisito feito:** `activate_for_task` + SEC-1.3 (`docs/ops/SKILL-ACTIVATION.md`, merge do #123).
**Governança:** ISO/IEC 42001 (P-40), ver a secção "ISO/IEC 42001" abaixo.
**Sem a flag** (omissão): o worker faz a chamada única de sempre, e o prompt diz "Nao tens tools neste passo", mesmo nos 42 passos que declaram `read_repo_file`. **Com a flag:** os passos com `tools_allowed` ∩ registo passam pelo loop de function calling.

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

## Implementação (2026-10-07)

| Item do contrato | Onde | Teste |
|---|---|---|
| Flag, desligada por omissão | `tool_executor.ENV_FLAG` (`PLAN_RUNNER_TOOLS`); `GeminiWorker(tools=...)` | `test_sem_flag_o_passo_faz_a_chamada_unica_de_sempre` |
| Autorizado = `tools_allowed` ∩ registo; `read` corre, `act` com aprovação, `prepare` recusado | `plan_tools`, `LEVELS_AUTO`, `LEVELS_APPROVAL`, `LEVELS_ALLOWED` | `test_plano_de_tools_intersecta_com_o_registo` |
| O modelo só vê as autorizadas; as outras vão para `unsupported` | `run_tool_loop` (declarações), `meta.tools.unsupported` | `test_com_flag_o_worker_usa_a_tool_e_audita` |
| Chamada não autorizada não corre | `execute_call` → `tool_not_allowed` | `test_tool_nao_autorizada_nao_corre` |
| `act` nunca corre sem decisão: sem decisão → `requires_approval`; `reject` → `rejected_by_human`; `approve` → corre | `execute_call(approval=...)` | `test_tool_act_exige_aprovacao_e_nao_corre` |
| **`act` pára no HITL antes de correr** qualquer chamada do turno; o estado da conversa fica no disco | `run_tool_loop` → `ToolApprovalRequired`; `GeminiWorker._open_tool_approval` (pedido `hitl-request-v1` com `context.tool_calls`, `tool_approval.json`, evento `tool_approval_requested`); executor → `awaiting_tool_approval`; motor → `paused_human_gate` + `status.tool_approval` + `HITL.md` | `test_loop_act_para_antes_de_correr_qualquer_chamada_do_turno`, `test_com_flag_tool_act_pausa_no_hitl` (o pedido valida contra o contrato) |
| Resume: `approve` executa a chamada, `reject` recusa-a e o modelo continua (o run não acaba) | `resume_run` / `resume_plan_langgraph` → `_resolve_tool_approval` (decisão em `hitl-decisions.jsonl`); `_tool_approval_resume` (evento `tool_approval_resolved`); `run_tool_loop(resume=..., approvals=...)` | `test_loop_act_retoma_com_a_decisao`, `test_com_flag_tool_act_retoma_com_a_decisao`, `test_com_flag_langgraph_tambem_pausa_e_retoma` |
| A decisão é a **deste pedido** (por id): a do lado Node manda; uma aprovação antiga nunca aprova um pedido novo; cada aprovação vale para 1 chamada; `edit` não é aceite | `_tool_approval_resume` (procura pelo `request_id`); `approvals.pop`; CLI `resume` sem `--decision` recusa (aprovar nunca é o default) | `test_com_flag_decisao_do_lado_node_manda`, `test_com_flag_uma_aprovacao_antiga_nao_aprova_um_pedido_novo`, `test_loop_cada_aprovacao_vale_para_uma_chamada`, `test_com_flag_tool_act_edit_nao_e_aceite`, `test_cli_aprovar_tool_act_nunca_e_o_default` |
| Args inválidos de uma `act` não incomodam o humano (voltam como `invalid_args`) | `_pending_approvals` | `test_loop_act_com_args_invalidos_nao_incomoda_o_humano` |
| **`kb` permitido ao passo:** `tool_kbs:` ou o `kb` do bloco `knowledge:`; o modelo vê o `kb` como enum; outro kb → `kb_not_allowed` sem chegar ao L5; sem kb declarado, a tool fica em `refused_policy` | `step_kbs`, `plan_tools(kbs=...)`, `declarations_for`, `_validation_error` | `test_kb_permitidos_vem_do_passo`, `test_declaracao_do_retrieve_knowledge_restringe_o_kb`, `test_retrieve_knowledge_com_backend_falso`, `test_com_flag_retrieve_knowledge_so_nos_kb_do_passo`, `test_com_flag_retrieve_knowledge_sem_kb_fica_de_fora` |
| `tool_limits:` e `tool_kbs:` no schema dos planos (o step tem `additionalProperties: false`: um plano com `tool_limits:` chumbava no W-006) | `runner/plan_runner/plan.schema.json` | `test_schema_dos_planos_aceita_tool_limits_e_tool_kbs` |
| Validação JSON Schema antes de executar | `VALIDATION` + `jsonschema` → `invalid_args` | `test_args_invalidos_sao_recusados_antes_de_executar` |
| `read_repo_file`: SEC-1 (denylist, sem `..`, sem symlinks para fora, 20 KB) | `_read_repo_file` → `repo_files.read_repo_files` | `test_read_repo_file_le_e_recusa_segredos`, `test_com_flag_segredo_nunca_chega_ao_modelo` |
| `retrieve_knowledge`: L5 com proveniência, backend injectável | `_retrieve_knowledge` → `McpKnowledge` | `test_retrieve_knowledge_com_backend_falso` |
| Output como dados, nunca instrução | `DATA_NOTE` na `functionResponse` e no prompt | `test_com_flag_o_worker_usa_a_tool_e_audita` |
| Thought signatures (Gemini 2.5/3) e `id` das chamadas | o conteúdo do modelo volta tal como veio | `test_loop_preserva_thought_signature_e_ids` |
| `max_turns` 6 e `max_tool_calls` 12; `tool_limits:` por passo, com tecto 10/24 | `ToolLimits.from_step` | `test_limites_do_passo_com_tecto_rigido`, `test_loop_para_no_max_turns`, `test_loop_para_no_max_tool_calls`, `test_com_flag_limite_deixa_o_passo_em_waiting_external` |
| Orçamento antes de cada turno extra | `before_turn` → `check_budget` | `test_com_flag_orcamento_para_antes_do_turno_seguinte` |
| Ledger: 1 linha por turno; `meta.tokens_*` somados | `_run_with_tools` | `test_com_flag_o_worker_usa_a_tool_e_audita` |
| Auditoria: evento `tool_called` com sha256 dos args (nunca os args em claro) | `on_call` → `events.jsonl` | idem |
| Tool que rebenta não parte o passo | `execute_call` → `tool_error` | `test_tool_que_rebenta_volta_como_erro` |
| Artefacto JSON com tools (sem `responseMimeType`) | `gemini_generate(function_declarations=...)` + `_parse_json_output` | `test_com_flag_artefacto_json_continua_a_ser_lido` |

**Testes de mutação** (cada um parte o código de propósito): tirar a preservação das thought signatures, a validação, o orçamento por turno, a troca da frase "sem tools" ou a autorização faz falhar pelo menos um teste. No seguimento, os 12 mutantes da aprovação e do kb (pausa, recusa, consumo da aprovação, decisão por id, gravação da decisão, resume nos 2 motores, limpeza do estado, filtro e política do kb) são todos apanhados.

**Para ligar num run real:**
1. Corre `PLAN_RUNNER_TOOLS=1 python -m plan_runner run <plano> --mode external --worker gemini`.
2. Confirma em `result.json → meta.tools` (turnos, chamadas, `unsupported`, `refused_policy`, `kbs`) e nos eventos `tool_called`.
3. Com uma tool `act` no passo, o run pára em `paused_human_gate`: lê o pedido em `hitl-requests.jsonl` (`context.tool_calls` tem os argumentos) e decide com `python -m plan_runner resume <run> --decision approve|reject` (ou pelo lado Node, no mesmo contrato).

O AU-20 fecha com o merge e com um run real com a flag ligada (DEV).

**Fica para depois** (não está no registo, fica `unsupported`): `web_search` (10 passos o declaram) e qualquer tool `prepare`/`act` real. O caminho de aprovação das `act` já existe e está testado com uma tool falsa; uma `act` real só entra no registo com idempotência + rollback (§15.6, item 10). `prepare` continua recusado até ter semântica definida.

