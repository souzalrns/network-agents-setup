import { describe, it, expect, vi, afterEach, beforeEach } from 'vitest';

// Mock só o `fetch` do undici (usado por http_request) -- por omissao
// delega para a implementacao real (chama actual.fetch de facto), o que
// deixa a guarda de SSRF real correr para os testes que nao sobrepoem o
// mock; testes que precisam de uma resposta controlada usam
// mockResolvedValueOnce/mockImplementationOnce.
vi.mock('undici', async (importOriginal) => {
  const actual = await importOriginal<typeof import('undici')>();
  return { ...actual, fetch: vi.fn(actual.fetch) };
});

import { fetch as undiciFetch } from 'undici';
import { createWebTools } from '../../packages/mcp/src/tools/built-in/web';

function mockFetchOnce(html: string) {
  vi.stubGlobal(
    'fetch',
    vi.fn().mockResolvedValue({
      text: async () => html,
    })
  );
}

describe('scrape_webpage — regex → cheerio (CodeQL / path A6)', () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it('selector com meta-caracteres de regex não quebra a execução', async () => {
    mockFetchOnce('<html><head><title>T</title></head><body><p>ok</p></body></html>');
    const tools = createWebTools();
    const scrape = tools.find((t) => t.name === 'scrape_webpage')!;
    const result: any = await scrape.execute({ url: 'http://example.com', selector: '(a|a)*' });
    // Nao deve lancar/crashar o processo -- ou devolve isError, ou devolve
    // matches vazio (selector CSS invalido nao casa nada), nunca explode.
    expect(result).toBeDefined();
    expect(result.content).toBeDefined();
  });

  it('selector válido extrai conteúdo real de HTML conhecido', async () => {
    mockFetchOnce(
      '<html><head><title>Página de teste</title></head><body><p>primeiro</p><p>segundo</p></body></html>'
    );
    const tools = createWebTools();
    const scrape = tools.find((t) => t.name === 'scrape_webpage')!;
    const result: any = await scrape.execute({ url: 'http://example.com', selector: 'p' });
    const parsed = JSON.parse(result.content[0].text);
    expect(parsed.title).toBe('Página de teste');
    expect(parsed.matches).toEqual(['primeiro', 'segundo']);
  });

  it('erro real de rede não expõe detalhe interno (A18)', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockRejectedValue(new Error('connect ECONNREFUSED 10.0.0.5:443 at /internal/secret/module.ts:12'))
    );
    const tools = createWebTools();
    const scrape = tools.find((t) => t.name === 'scrape_webpage')!;
    const result: any = await scrape.execute({ url: 'http://example.com' });
    expect(result.isError).toBe(true);
    expect(result.content[0].text).toBe('Erro ao processar página web');
    expect(result.content[0].text).not.toMatch(/10\.0\.0\.5/);
    expect(result.content[0].text).not.toMatch(/ECONNREFUSED/);
  });

  it('sem selector, devolve só o título', async () => {
    mockFetchOnce('<html><head><title>Sem selector</title></head><body><p>x</p></body></html>');
    const tools = createWebTools();
    const scrape = tools.find((t) => t.name === 'scrape_webpage')!;
    const result: any = await scrape.execute({ url: 'http://example.com' });
    const parsed = JSON.parse(result.content[0].text);
    expect(parsed.title).toBe('Sem selector');
    expect(parsed.matches).toBeUndefined();
  });
});

describe('http_request — guarda de SSRF (A5)', () => {
  beforeEach(() => {
    vi.mocked(undiciFetch).mockClear();
  });

  it('esquema não permitido (file://) é rejeitado antes de qualquer rede', async () => {
    const tools = createWebTools();
    const httpRequest = tools.find((t) => t.name === 'http_request')!;
    const result: any = await httpRequest.execute({ url: 'file:///etc/passwd' });
    expect(result.isError).toBe(true);
    expect(result.content[0].text).toMatch(/Scheme not allowed/);
    expect(undiciFetch).not.toHaveBeenCalled();
  });

  it('esquema não permitido (gopher://) é rejeitado antes de qualquer rede', async () => {
    const tools = createWebTools();
    const httpRequest = tools.find((t) => t.name === 'http_request')!;
    const result: any = await httpRequest.execute({ url: 'gopher://example.com' });
    expect(result.isError).toBe(true);
    expect(result.content[0].text).toMatch(/Scheme not allowed/);
    expect(undiciFetch).not.toHaveBeenCalled();
  });

  it('URL interna (169.254.169.254, metadata cloud) é bloqueada pela guarda real', async () => {
    const tools = createWebTools();
    const httpRequest = tools.find((t) => t.name === 'http_request')!;
    const result: any = await httpRequest.execute({ url: 'http://169.254.169.254/latest/meta-data' });
    expect(result.isError).toBe(true);
    expect(result.content[0].text).toMatch(/SSRF bloqueado/);
  });

  it('URL interna (127.0.0.1) é bloqueada pela guarda real', async () => {
    const tools = createWebTools();
    const httpRequest = tools.find((t) => t.name === 'http_request')!;
    const result: any = await httpRequest.execute({ url: 'http://127.0.0.1/' });
    expect(result.isError).toBe(true);
    expect(result.content[0].text).toMatch(/SSRF bloqueado/);
  });

  it('URL interna (10.x.x.x, RFC1918) é bloqueada pela guarda real', async () => {
    const tools = createWebTools();
    const httpRequest = tools.find((t) => t.name === 'http_request')!;
    const result: any = await httpRequest.execute({ url: 'http://10.0.0.5/' });
    expect(result.isError).toBe(true);
    expect(result.content[0].text).toMatch(/SSRF bloqueado/);
  });

  it('redirect (3xx) é bloqueado, mesmo para um alvo externo legítimo', async () => {
    vi.mocked(undiciFetch).mockResolvedValueOnce({
      status: 302,
      ok: false,
      headers: { get: (h: string) => (h === 'location' ? 'http://169.254.169.254/' : null) },
    } as any);
    const tools = createWebTools();
    const httpRequest = tools.find((t) => t.name === 'http_request')!;
    const result: any = await httpRequest.execute({ url: 'https://example.com/redirect-me' });
    expect(result.isError).toBe(true);
    expect(result.content[0].text).toMatch(/Redirect blocked/);
  });

  it('URL legítima (mock 200 JSON) devolve o resultado normalmente', async () => {
    vi.mocked(undiciFetch).mockResolvedValueOnce({
      status: 200,
      ok: true,
      headers: { get: (h: string) => (h === 'content-type' ? 'application/json' : null) },
      json: async () => ({ hello: 'world' }),
    } as any);
    const tools = createWebTools();
    const httpRequest = tools.find((t) => t.name === 'http_request')!;
    const result: any = await httpRequest.execute({ url: 'https://example.com/api' });
    expect(result.isError).toBeUndefined();
    const parsed = JSON.parse(result.content[0].text);
    expect(parsed.status).toBe(200);
    expect(parsed.data).toEqual({ hello: 'world' });
  });

  it('timeout (>5s) é abortado e reportado como tal', async () => {
    vi.mocked(undiciFetch).mockImplementationOnce(
      (_url: any, init: any) =>
        new Promise((_resolve, reject) => {
          init.signal.addEventListener('abort', () => {
            const err: any = new Error('This operation was aborted');
            err.name = 'AbortError';
            reject(err);
          });
        })
    );
    const tools = createWebTools();
    const httpRequest = tools.find((t) => t.name === 'http_request')!;
    const result: any = await httpRequest.execute({ url: 'https://example.com/slow' });
    expect(result.isError).toBe(true);
    expect(result.content[0].text).toMatch(/Timeout after 5000ms/);
  }, 10000);
});
