import { describe, it, expect, vi, afterEach, beforeEach } from 'vitest';

// prisma real precisa de `prisma generate` (bloqueio conhecido, ver B10/D8) --
// mockado aqui para os testes de legal tools nao dependerem disso.
vi.mock('../../packages/mcp/src/tools/legal/db', () => ({
  prisma: {
    legalDocument: {
      findMany: vi.fn(),
      findUnique: vi.fn(),
      findFirst: vi.fn(),
    },
  },
}));

import { MCPClient } from '../../packages/mcp/src/client/MCPClient';
import { ToolExecutor } from '../../packages/mcp/src/tools/ToolExecutor';
import { ToolRegistry } from '../../packages/mcp/src/tools/ToolRegistry';
import { createDatabaseTools } from '../../packages/mcp/src/tools/built-in/database';
import { createPortugueseLawTools } from '../../packages/mcp/src/tools/legal/portuguese-law';
import { createBrazilianLawTools } from '../../packages/mcp/src/tools/legal/brazilian-law';
import { prisma } from '../../packages/mcp/src/tools/legal/db';

const SENSITIVE = /10\.0\.0\.5|ECONNREFUSED|password=|\/internal\//;

describe('MCPClient.executeTool — não expõe detalhe de rede (A18)', () => {
  afterEach(() => vi.unstubAllGlobals());

  it('erro real de rede devolve mensagem genérica', async () => {
    const client = new MCPClient();
    (client as any).serverUrl = 'http://internal-mcp-server:9000';
    vi.stubGlobal(
      'fetch',
      vi.fn().mockRejectedValue(new Error('connect ECONNREFUSED 10.0.0.5:9000'))
    );
    const result: any = await client.executeTool('some_tool', {});
    expect(result.isError).toBe(true);
    expect(result.content[0].text).toBe('Erro ao comunicar com o servidor MCP');
    expect(result.content[0].text).not.toMatch(SENSITIVE);
  });
});

describe('ToolExecutor — catch genérico não expõe detalhe (A18)', () => {
  const ORIGINAL_ENV = { ...process.env };
  let tmpDir: string;

  beforeEach(async () => {
    process.env.MCP_POLICY_PROFILE = 'permissive';
    const fs = await import('fs/promises');
    const os = await import('os');
    const path = await import('path');
    tmpDir = await fs.mkdtemp(path.join(os.tmpdir(), 'tool-executor-audit-'));
    process.env.MCP_AUDIT_LOG_PATH = path.join(tmpDir, 'audit.jsonl');
  });

  afterEach(async () => {
    process.env = { ...ORIGINAL_ENV };
    const fs = await import('fs/promises');
    await fs.rm(tmpDir, { recursive: true, force: true });
  });

  it('erro real dentro de tool.execute() devolve mensagem genérica', async () => {
    const registry = new ToolRegistry([
      {
        name: 'read_file',
        description: 'stub',
        inputSchema: { type: 'object', properties: {} },
        execute: async () => {
          throw new Error('ENOENT: /internal/secret/config.json password=hunter2');
        },
      },
    ]);
    const executor = new ToolExecutor(registry);
    const result: any = await executor.executeTool('read_file', {});
    expect(result.isError).toBe(true);
    expect(result.content[0].text).toBe('Erro ao executar a tool');
    expect(result.content[0].text).not.toMatch(SENSITIVE);
  });
});

describe('query_database / get_schema — não expõem detalhe do driver (A18)', () => {
  it('erro real do pg (query_database) devolve mensagem genérica', async () => {
    const pool: any = { query: vi.fn().mockRejectedValue(new Error('connection to server at "10.0.0.5", port 5432 failed')) };
    const tools = createDatabaseTools(pool);
    const queryTool = tools.find((t) => t.name === 'query_database')!;
    const result: any = await queryTool.execute({ query: 'SELECT 1' });
    expect(result.isError).toBe(true);
    expect(result.content[0].text).toBe('Erro na consulta à base de dados');
    expect(result.content[0].text).not.toMatch(SENSITIVE);
  });

  it('erro real do pg (get_schema) devolve mensagem genérica', async () => {
    const pool: any = { query: vi.fn().mockRejectedValue(new Error('connection to server at "10.0.0.5", port 5432 failed')) };
    const tools = createDatabaseTools(pool);
    const schemaTool = tools.find((t) => t.name === 'get_schema')!;
    const result: any = await schemaTool.execute({});
    expect(result.isError).toBe(true);
    expect(result.content[0].text).toBe('Erro ao obter o schema da base de dados');
    expect(result.content[0].text).not.toMatch(SENSITIVE);
  });
});

describe('legal tools (PT/BR) — não expõem detalhe do Prisma (A18)', () => {
  afterEach(() => vi.clearAllMocks());

  it('search_portuguese_law: erro real do prisma devolve mensagem genérica', async () => {
    (prisma.legalDocument.findMany as any).mockRejectedValue(
      new Error('connection to server at "10.0.0.5" failed')
    );
    const tools = createPortugueseLawTools();
    const search = tools.find((t) => t.name === 'search_portuguese_law')!;
    const result: any = await search.execute({ query: 'civil' });
    expect(result.isError).toBe(true);
    expect(result.content[0].text).toBe('Erro na busca de legislação');
    expect(result.content[0].text).not.toMatch(SENSITIVE);
  });

  it('get_portuguese_law: erro real do prisma devolve mensagem genérica', async () => {
    (prisma.legalDocument.findUnique as any).mockRejectedValue(
      new Error('connection to server at "10.0.0.5" failed')
    );
    const tools = createPortugueseLawTools();
    const get = tools.find((t) => t.name === 'get_portuguese_law')!;
    const result: any = await get.execute({ id: 'x' });
    expect(result.isError).toBe(true);
    expect(result.content[0].text).toBe('Erro ao obter lei');
    expect(result.content[0].text).not.toMatch(SENSITIVE);
  });

  it('search_brazilian_law: erro real do prisma devolve mensagem genérica', async () => {
    (prisma.legalDocument.findMany as any).mockRejectedValue(
      new Error('connection to server at "10.0.0.5" failed')
    );
    const tools = createBrazilianLawTools();
    const search = tools.find((t) => t.name === 'search_brazilian_law')!;
    const result: any = await search.execute({ query: 'civil' });
    expect(result.isError).toBe(true);
    expect(result.content[0].text).toBe('Erro na busca de legislação');
    expect(result.content[0].text).not.toMatch(SENSITIVE);
  });

  it('get_brazilian_law: erro real do prisma devolve mensagem genérica', async () => {
    (prisma.legalDocument.findUnique as any).mockRejectedValue(
      new Error('connection to server at "10.0.0.5" failed')
    );
    const tools = createBrazilianLawTools();
    const get = tools.find((t) => t.name === 'get_brazilian_law')!;
    const result: any = await get.execute({ id: 'x' });
    expect(result.isError).toBe(true);
    expect(result.content[0].text).toBe('Erro ao obter lei');
    expect(result.content[0].text).not.toMatch(SENSITIVE);
  });
});
