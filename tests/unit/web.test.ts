import { describe, it, expect, vi, afterEach } from 'vitest';
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
