import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import { readFileSync } from 'fs';
import { ToolExecutor } from '../../packages/mcp/src/tools/ToolExecutor';
import { ToolRegistry } from '../../packages/mcp/src/tools/ToolRegistry';
import { getGlobalTracer } from '@network-agents/observability';
import { verifyChain } from '../../packages/mcp/src/tools/ActionReceipt';

function lastSpan() {
  const allTraces = getGlobalTracer().getAllTraces();
  const traceIds = [...allTraces.keys()];
  const lastTraceId = traceIds[traceIds.length - 1];
  const spans = allTraces.get(lastTraceId)!;
  return spans[spans.length - 1];
}

describe('ToolExecutor (D2 — spans gen_ai.tool)', () => {
  const ORIGINAL_ENV = { ...process.env };
  let tmpDir: string;

  beforeEach(async () => {
    process.env.MCP_POLICY_PROFILE = 'permissive';
    const fs = await import('fs/promises');
    const os = await import('os');
    const path = await import('path');
    tmpDir = await fs.mkdtemp(path.join(os.tmpdir(), 'tool-executor-spans-'));
    process.env.MCP_AUDIT_LOG_PATH = path.join(tmpDir, 'audit.jsonl');
  });

  afterEach(async () => {
    process.env = { ...ORIGINAL_ENV };
    const fs = await import('fs/promises');
    await fs.rm(tmpDir, { recursive: true, force: true });
  });

  it('executeTool() cria span gen_ai.tool.execute com o nome da tool, status ok', async () => {
    // Nome tem de estar em SCOPES (ToolPolicy.ts) -- authorize() nega
    // "unknown_tool" para nomes fora dessa lista, independente do profile.
    const registry = new ToolRegistry([
      {
        name: 'read_file',
        description: 'stub',
        inputSchema: { type: 'object', properties: {} },
        execute: async () => ({ content: [{ type: 'text', text: 'ok' }] }),
      },
    ]);
    const executor = new ToolExecutor(registry);
    const result: any = await executor.executeTool('read_file', {});
    expect(result.isError).toBeUndefined();

    const span = lastSpan();
    expect(span.name).toBe('gen_ai.tool.execute');
    expect(span.status).toBe('ok');
    expect(span.attributes['gen_ai.tool.name']).toBe('read_file');
    expect(span.attributes['gen_ai.operation.name']).toBe('execute_tool');
  });

  it('marca o span como error quando tool.execute() lança', async () => {
    const registry = new ToolRegistry([
      {
        name: 'write_file',
        description: 'stub',
        inputSchema: { type: 'object', properties: {} },
        execute: async () => {
          throw new Error('boom');
        },
      },
    ]);
    const executor = new ToolExecutor(registry);
    const result: any = await executor.executeTool('write_file', {});

    expect(result.isError).toBe(true);
    const span = lastSpan();
    expect(span.name).toBe('gen_ai.tool.execute');
    expect(span.status).toBe('error');
    expect(span.attributes['gen_ai.tool.name']).toBe('write_file');
  });

  it('acção bem sucedida grava um recibo na cadeia (C5), ao lado do audit.jsonl', async () => {
    const registry = new ToolRegistry([
      {
        name: 'read_file',
        description: 'stub',
        inputSchema: { type: 'object', properties: {} },
        execute: async () => ({ content: [{ type: 'text', text: 'ok' }] }),
      },
    ]);
    const executor = new ToolExecutor(registry);
    await executor.executeTool('read_file', {}, { caller: 'agent-x' });

    const chainPath = `${process.env.MCP_AUDIT_LOG_PATH}.chain`;
    const lines = readFileSync(chainPath, 'utf-8').trim().split('\n');
    expect(lines).toHaveLength(1);
    const receipt = JSON.parse(lines[0]);
    expect(receipt.actor).toBe('agent-x');
    expect(receipt.tool).toBe('read_file');
    expect(receipt.prev_receipt_hash).toBeNull();
    expect(verifyChain(chainPath)).toEqual({ valid: true });
  });
});
