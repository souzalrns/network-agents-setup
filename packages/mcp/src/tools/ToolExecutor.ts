import { ToolRegistry, MCPTool, MCPToolResult } from './ToolRegistry';
import { authorize, rateLimit, audit, hashParamsForAudit } from './ToolPolicy';
import { appendReceipt, hashResult } from './ActionReceipt';
import { toClientError } from '../util/sanitizeError';
import { getGlobalTracer } from '@network-agents/observability';

export interface ExecutionContext {
  caller?: string;
  providedKey?: string;
}

export class ToolExecutor {
  constructor(private registry: ToolRegistry) {}
  async executeTool(
    name: string,
    params: Record<string, any>,
    context: ExecutionContext = {}
  ): Promise<MCPToolResult> {
    const caller = context.caller || 'unknown';
    const tool = this.registry.getTool(name);
    if (!tool) {
      return { content: [{ type: 'text', text: `Tool ${name} not found` }], isError: true };
    }

    const auth = authorize(caller, name, context.providedKey);
    if (!auth.allowed) {
      audit({ caller, tool: name, params_hash: hashParamsForAudit(params), allowed: false, reason: auth.reason });
      return { content: [{ type: 'text', text: `Access denied: ${auth.reason}` }], isError: true };
    }

    const rate = rateLimit(caller);
    if (!rate.allowed) {
      audit({
        caller,
        tool: name,
        params_hash: hashParamsForAudit(params),
        allowed: false,
        reason: 'rate_limit_exceeded',
      });
      return { content: [{ type: 'text', text: 'Rate limit exceeded' }], isError: true };
    }

    const tracer = getGlobalTracer();
    const spanId = tracer.startSpan('gen_ai.tool.execute');
    tracer.setAttribute(spanId, 'gen_ai.tool.name', name);
    tracer.setAttribute(spanId, 'gen_ai.operation.name', 'execute_tool');
    try {
      this.validateParams(tool, params);
      const result = await tool.execute(params);
      tracer.endSpan(spanId, 'ok');
      audit({ caller, tool: name, params_hash: hashParamsForAudit(params), allowed: true, reason: auth.reason });
      // C5: recibo de acção com hash encadeado (ADR-001 §8), aditivo ao
      // audit.jsonl já existente -- ver ActionReceipt.ts para o escopo
      // deliberadamente reduzido face ao contrato completo do ADR-001.
      appendReceipt({
        actor: caller,
        tool: name,
        params_hash: hashParamsForAudit(params),
        result_hash: hashResult(result),
      });
      return result;
    } catch (error: any) {
      tracer.endSpan(spanId, 'error', error);
      audit({
        caller,
        tool: name,
        params_hash: hashParamsForAudit(params),
        allowed: false,
        reason: 'execution_error',
      });
      return { content: [{ type: 'text', text: toClientError(error, 'ao executar a tool') }], isError: true };
    }
  }
  private validateParams(tool: MCPTool, params: Record<string, any>): void {
    const required = tool.inputSchema.required || [];
    for (const field of required) {
      if (params[field] === undefined || params[field] === null) {
        throw new Error(`Missing required parameter: ${field}`);
      }
    }
  }
}
