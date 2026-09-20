# AUDIT-OBSERVABILITY.md — Auditoria de Observabilidade

Consolida `memory/FASE3-MEMORIA.md` secção 5 (avaliação inicial de Langfuse/OTel/RAGAS) com uma verificação profunda nova, incluindo uma **correção a um achado da auditoria de governança**.

## 1. Correção importante: o lado TypeScript não está "ausente" — está presente, mock, e com um bug real

`GOV-FASE1.md` classificou observability em TS como "PARCIAL, só do lado Python" / "Ausente em TS". **Verificado agora, isto é parcialmente falso.** Existe `packages/observability/` (`@network-agents/observability`), com `Logger.ts`, `Metrics.ts`, `Tracer.ts`, consumido por `packages/core/src/orchestrator/Executor.ts`.

`Tracer.ts` é uma **reimplementação manual** de spans em memória (`Map<string, Span[]>`, nunca limpo — memory leak em processo long-running), com exportador OTLP montado à mão via `fetch()` (sem SDK oficial, sem batching, sem retries). Usado num **único ponto** de todo o `packages/core`: `Executor.ts` cria um span por **execução de plano inteiro** (não por passo, não por chamada a LLM, não por tool call). Há um **bug real confirmado**: `exportTrace(traceSpanId)` recebe um `spanId` onde a assinatura espera um `traceId` — só funciona hoje porque, neste único call site, span raiz e trace coincidem; quebraria com spans aninhados.

Em paralelo, `packages/core/src/observability/{SelfAwareness,MetricsDashboard}.ts` não fazem observabilidade real: `getCostsState()`, `getGaps()`, `getOpportunities()` devolvem **dados estáticos hardcoded** (comentário no próprio código: "Em produção, consulta o TokenEconomy" — hoje não consulta nada real).

**Conclusão:** pior do que "ausente" em termos de risco — passa falsa impressão de que existe tracing, quando é telemetria de brinquedo que nunca chega a lado nenhum sem `OTLP_ENDPOINT` definido manualmente.

## 2. Estado real do lado Python

`runner/plan_runner/events.py`: `EventLog.append()` escreve `{id, type, run_id, at, payload}` em JSONL, sem qualquer campo de trace/span. `mcp/plan_runner/audit/audit.jsonl` — caminho gerado dinamicamente, nunca versionado (`.gitignore: *`).

## 3. Ferramentas externas — resumo

| Ferramenta | Achado | Classificação |
|---|---|---|
| **OpenTelemetry SDK** (Python+JS) | Graduou no CNCF (maio/2026), 48,5% de adoção. Convenções GenAI (`gen_ai.*`): só os **spans de cliente LLM** (`gen_ai.client`) estão estáveis; o resto (agent/workflow spans) continua em *Development* | **ADOPT** (parcial — só a parte estável) |
| **Langfuse** — licença | Pendência da auditoria de memória (`NOASSERTION`) **resolvida**: `LICENSE` real = MIT Expat para tudo exceto `ee/*` (SCIM, audit log, RBAC de projeto — licença comercial separada). Self-host completo corre o mesmo código do Cloud | **ADAPT** (consumidor opcional via OTLP genérico) |
| **Arize Phoenix** | 11,5k★, licença Elastic 2.0 (não OSI), local-first genuíno, junta evals+tracing — mas sobrepõe-se ao DeepEval já escolhido na Fase de Evaluation | **DEFER** |
| **OpenLLMetry / OpenLLMetry-JS** | Apache-2.0, 7,4k★, camada de instrumentação (não visualiza). **Traceloop (mantenedor) foi adquirida pela ServiceNow em março/2026** — risco de governança a monitorizar | **REFERENCE** |

## 4. Proposta mínima de wiring (aditivo, sem infra obrigatória)

1. **Python**: acrescentar `trace_id`/`span_id`/`parent_span_id` opcionais ao `EventLog.append()` (aditivo, não quebra consumidores existentes); novo módulo `otel_bridge.py` que envolve `step_started`/`step_finished` num span OTel real (SDK oficial, `ConsoleSpanExporter` por omissão, troca para `OTLPSpanExporter` se `OTEL_EXPORTER_OTLP_ENDPOINT` estiver definida — variável oficial do SDK, não a `OTLP_ENDPOINT` artesanal que o `Tracer.ts` já usa).
2. **TypeScript**: substituir o motor de `Tracer.ts` por `@opentelemetry/api`+`@opentelemetry/sdk-trace-node`, mantendo a mesma API pública (`startSpan`/`endSpan`/`setAttribute`) para não tocar em `Executor.ts`. Resolve de imediato o memory leak e o bug `traceId`/`spanId`. Estender cobertura a `LLMService.ts` (spans `gen_ai.client`) e `packages/mcp/ToolExecutor.ts` (spans de tool call), hoje sem nenhuma instrumentação.
3. **Não tocar** em `MetricsDashboard.ts`/`SelfAwareness.ts` nesta fase — são scaffolds mockados; misturar com telemetria real esconderia que os dados são fake.
4. **Backend opcional**: Langfuse local via `OTEL_EXPORTER_OTLP_ENDPOINT` aponta directo para o endpoint OTLP do Langfuse — sem escrever nenhum importador dedicado de `events.jsonl`.

Custo total: 1 ficheiro novo em Python, 2 dependências + 1 ficheiro reescrito em TS, zero mudança de schema em `events.jsonl`/`audit.jsonl`, zero infraestrutura obrigatória.

## 5. Classificação consolidada

| Item | Classificação |
|---|---|
| OpenTelemetry SDK | ADOPT |
| OTel GenAI semantic conventions (`gen_ai.client`) | ADOPT (parcial — só a parte estável) |
| Langfuse self-host | ADAPT (consumidor opcional) |
| Arize Phoenix | DEFER |
| OpenLLMetry | REFERENCE |
| `Tracer.ts` actual (hand-rolled) | REJECT (substituir) |
| `MetricsDashboard.ts`/`SelfAwareness.ts` | REJECT (como observabilidade) / DEFER (como conceito, depois de haver dados reais) |

## 6. O que NÃO fazer

- Não adoptar Phoenix agora — sobreporia com DeepEval já escolhido.
- Não adoptar OpenLLMetry como dependência de produção ainda — aquisição recente, esperar sinal de estabilidade de roadmap.
- Não implementar já os spans "agent"/"workflow" do OTel GenAI — ainda em Development, atributos podem mudar de nome.
- Não misturar `MetricsDashboard`/`SelfAwareness` na instrumentação real sem reescrever a lógica de coleta.
- Não construir parser dedicado de `events.jsonl` para Langfuse/Phoenix — gerar OTLP diretamente é mais barato.
