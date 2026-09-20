import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import { readFileSync } from 'fs';
import { MCPServer } from '../../packages/mcp/src/server/MCPServer';
import { callerIdFromKey } from '../../packages/mcp/src/server/McpAuth';

function fakeReqRes(body: any, headers: Record<string, string> = {}) {
  const req = { body, headers } as any;
  let statusCode = 200;
  let jsonBody: any = null;
  const res: any = {
    status(code: number) {
      statusCode = code;
      return this;
    },
    json(payload: any) {
      jsonBody = payload;
      return this;
    },
  };
  return { req, res, getStatus: () => statusCode, getJson: () => jsonBody };
}

describe('MCPServer.createHttpHandler() — autenticação + propagação de caller (A8/S11)', () => {
  const ORIGINAL_ENV = { ...process.env };
  let tmpDir: string;
  let server: MCPServer;

  beforeEach(async () => {
    const fs = await import('fs/promises');
    const os = await import('os');
    const path = await import('path');
    tmpDir = await fs.mkdtemp(path.join(os.tmpdir(), 'mcp-server-auth-'));
    process.env.MCP_AUDIT_LOG_PATH = path.join(tmpDir, 'audit.jsonl');
    process.env.MCP_SERVER_KEYS = 'key-one,key-two';
    delete process.env.MCP_ALLOW_UNAUTHENTICATED;
    delete process.env.NODE_ENV;

    server = new MCPServer([
      {
        name: 'read_file',
        description: 'stub',
        inputSchema: { type: 'object', properties: {} },
        execute: async () => ({ content: [{ type: 'text', text: 'ok' }] }),
      },
    ]);
  });

  afterEach(async () => {
    process.env = { ...ORIGINAL_ENV };
    const fs = await import('fs/promises');
    await fs.rm(tmpDir, { recursive: true, force: true });
  });

  function lastAuditEntry() {
    const lines = readFileSync(process.env.MCP_AUDIT_LOG_PATH as string, 'utf-8').trim().split('\n');
    return JSON.parse(lines[lines.length - 1]);
  }

  it('pedido com Bearer key-one → ToolExecutor é chamado com caller = hash(key-one)', async () => {
    const handler = server.createHttpHandler();
    const { req, res, getStatus } = fakeReqRes(
      { method: 'executeTool', params: { name: 'read_file', params: {} } },
      { authorization: 'Bearer key-one' }
    );
    await handler(req, res);

    expect(getStatus()).toBe(200);
    const entry = lastAuditEntry();
    expect(entry.caller).toBe(callerIdFromKey('key-one'));
  });

  it('pedido com Bearer key-two → caller = hash(key-two), diferente de hash(key-one)', async () => {
    const handler = server.createHttpHandler();
    const { req, res } = fakeReqRes(
      { method: 'executeTool', params: { name: 'read_file', params: {} } },
      { authorization: 'Bearer key-two' }
    );
    await handler(req, res);

    const entry = lastAuditEntry();
    expect(entry.caller).toBe(callerIdFromKey('key-two'));
    expect(entry.caller).not.toBe(callerIdFromKey('key-one'));
  });

  it('sem header Authorization → 401, ToolExecutor nunca é invocado (nada escrito no audit.jsonl)', async () => {
    const handler = server.createHttpHandler();
    const { req, res, getStatus, getJson } = fakeReqRes({
      method: 'executeTool',
      params: { name: 'read_file', params: {} },
    });
    await handler(req, res);

    expect(getStatus()).toBe(401);
    expect(getJson()).toEqual({ error: 'Unauthorized' });
    expect(() => readFileSync(process.env.MCP_AUDIT_LOG_PATH as string, 'utf-8')).toThrow();
  });

  it('Bearer com key errada → 401', async () => {
    const handler = server.createHttpHandler();
    const { req, res, getStatus } = fakeReqRes(
      { method: 'executeTool', params: { name: 'read_file', params: {} } },
      { authorization: 'Bearer key-nao-existe' }
    );
    await handler(req, res);
    expect(getStatus()).toBe(401);
  });

  it('sem MCP_SERVER_KEYS configurada (e sem MCP_ALLOW_UNAUTHENTICATED) → 503, fail-closed', async () => {
    delete process.env.MCP_SERVER_KEYS;
    const handler = server.createHttpHandler();
    const { req, res, getStatus, getJson } = fakeReqRes(
      { method: 'getTools', params: {} },
      { authorization: 'Bearer qualquer-coisa' }
    );
    await handler(req, res);
    expect(getStatus()).toBe(503);
    expect(getJson().error).toMatch(/authentication is not configured/);
  });

  it('getTools também exige autenticação (gate uniforme, mesmo padrão de authMiddleware em apps/api)', async () => {
    const handler = server.createHttpHandler();
    const { req, res, getStatus } = fakeReqRes({ method: 'getTools', params: {} });
    await handler(req, res);
    expect(getStatus()).toBe(401);
  });

  it('não-regressão: MCPServer.executeTool() público continua a aceitar chamada sem context (2 argumentos)', async () => {
    const result: any = await server.executeTool('read_file', {});
    expect(result.isError).toBeUndefined();
  });
});
