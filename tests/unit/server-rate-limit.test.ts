import { describe, it, expect, afterEach, beforeEach } from 'vitest';
import http from 'http';
import { createServer } from '../../apps/api/src/server';

function get(port: number, path: string): Promise<{ status: number; headers: http.IncomingHttpHeaders }> {
  return new Promise((resolve) => {
    http.get(`http://127.0.0.1:${port}${path}`, (res) => {
      res.resume();
      resolve({ status: res.statusCode!, headers: res.headers });
    });
  });
}

const fakeAgentFactory = { getAllAgents: () => [] } as any;

describe('createServer — rate limit (A16)', () => {
  let server: http.Server | undefined;
  const ORIGINAL_ENV = { ...process.env };

  beforeEach(() => {
    // Sem API_KEY, authMiddleware devolve 503 antes de chegar ao rate
    // limiter -- ALLOW_UNAUTHENTICATED deixa os pedidos passarem por auth.ts.
    process.env.ALLOW_UNAUTHENTICATED = 'true';
    process.env.NODE_ENV = 'test';
    delete process.env.API_KEY;
  });

  afterEach(() => {
    process.env = { ...ORIGINAL_ENV };
    server?.close();
  });

  it('permite 60 pedidos na mesma janela (não-regressão)', async () => {
    const app = createServer({} as any, fakeAgentFactory, {} as any, {} as any);
    server = app.listen(0);
    const port = (server.address() as any).port;

    for (let i = 0; i < 60; i++) {
      const res = await get(port, '/agents');
      expect(res.status).not.toBe(429);
    }
  }, 20000);

  it('a 61ª chamada na mesma janela devolve 429', async () => {
    const app = createServer({} as any, fakeAgentFactory, {} as any, {} as any);
    server = app.listen(0);
    const port = (server.address() as any).port;

    let last: { status: number; headers: http.IncomingHttpHeaders } | undefined;
    for (let i = 0; i < 61; i++) {
      last = await get(port, '/agents');
    }
    expect(last!.status).toBe(429);
  }, 20000);

  it('não aplica o limite a /health (checks de infra)', async () => {
    const app = createServer({} as any, fakeAgentFactory, {} as any, {} as any);
    server = app.listen(0);
    const port = (server.address() as any).port;

    // Esgota o limite noutra rota primeiro.
    for (let i = 0; i < 61; i++) {
      await get(port, '/agents');
    }
    const health = await get(port, '/health');
    expect(health.status).not.toBe(429);
  }, 20000);
});
