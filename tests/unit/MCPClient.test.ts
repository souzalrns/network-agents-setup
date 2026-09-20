import { describe, it, expect, vi, afterEach } from 'vitest';
import { MCPClient } from '../../packages/mcp/src/client/MCPClient';

describe('MCPClient — envia identidade real (A8/S11)', () => {
  afterEach(() => vi.unstubAllGlobals());

  it('connect() envia Authorization: Bearer <apiKey> no GET /tools', async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ tools: [] }),
    });
    vi.stubGlobal('fetch', fetchMock);

    const client = new MCPClient('minha-chave');
    await client.connect('http://mcp-server:9000');

    expect(fetchMock).toHaveBeenCalledWith(
      'http://mcp-server:9000/tools',
      expect.objectContaining({ headers: { Authorization: 'Bearer minha-chave' } })
    );
  });

  it('executeTool() envia Authorization: Bearer <apiKey> no POST /execute', async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ content: [{ type: 'text', text: 'ok' }] }),
    });
    vi.stubGlobal('fetch', fetchMock);

    const client = new MCPClient('minha-chave');
    (client as any).serverUrl = 'http://mcp-server:9000';
    await client.executeTool('read_file', { path: 'x' });

    const [, options] = fetchMock.mock.calls[0];
    expect(options.headers).toMatchObject({
      'Content-Type': 'application/json',
      Authorization: 'Bearer minha-chave',
    });
  });

  it('sem apiKey (nem construtor nem MCP_CLIENT_KEY) — não envia header Authorization (não regride o caso "cliente sem chave" já coberto por A18)', async () => {
    const ORIGINAL = process.env.MCP_CLIENT_KEY;
    delete process.env.MCP_CLIENT_KEY;
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ content: [{ type: 'text', text: 'ok' }] }),
    });
    vi.stubGlobal('fetch', fetchMock);

    const client = new MCPClient();
    (client as any).serverUrl = 'http://mcp-server:9000';
    await client.executeTool('read_file', {});

    const [, options] = fetchMock.mock.calls[0];
    expect(options.headers.Authorization).toBeUndefined();
    if (ORIGINAL !== undefined) process.env.MCP_CLIENT_KEY = ORIGINAL;
  });
});
