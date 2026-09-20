import { describe, it, expect, afterEach, beforeEach } from 'vitest';
import http from 'http';
import { createServer } from '../../apps/api/src/server';

function get(port: number, path: string): Promise<number> {
  return new Promise((resolve) => {
    http.get(`http://127.0.0.1:${port}${path}`, (res) => {
      res.resume();
      resolve(res.statusCode!);
    });
  });
}

// A17: bot protection só faz sentido em endpoints que aceitam tráfego humano
// não-autenticado. Este teste prova a premissa da classificação N/A -- todas
// as 19 rotas reais de apps/api (agents/chat/executions/health/hitl/metrics)
// exigem X-API-Key (authMiddleware, auth.ts, montado globalmente em
// server.ts antes de qualquer rota) e devolvem 503 sem ela configurada.
const ALL_ROUTES = [
  '/agents',
  '/agents/x',
  '/agents/domain/legal',
  '/chat',
  '/chat/stream',
  '/executions',
  '/executions/x',
  '/health',
  '/health/ready',
  '/health/metrics',
  '/hitl/pending',
  '/hitl/x',
  '/hitl/x/checkpoint',
  '/hitl/stats',
  '/metrics',
  '/metrics/prometheus',
  '/metrics/agents',
  '/metrics/hitl',
  '/metrics/costs',
  '/metrics/performance',
];

describe('createServer — nenhum endpoint é público (A17)', () => {
  let server: http.Server | undefined;
  const ORIGINAL_ENV = { ...process.env };

  beforeEach(() => {
    delete process.env.API_KEY;
    delete process.env.ALLOW_UNAUTHENTICATED;
    process.env.NODE_ENV = 'test';
  });

  afterEach(() => {
    process.env = { ...ORIGINAL_ENV };
    server?.close();
  });

  it('todas as rotas GET devolvem 503 sem API_KEY configurada (fail-closed, sem excepções)', async () => {
    const app = createServer({} as any, {} as any, {} as any, {} as any);
    server = app.listen(0);
    const port = (server.address() as any).port;

    for (const path of ALL_ROUTES) {
      const status = await get(port, path);
      expect(status, `${path} devia ser 503 (fail-closed), não é rota pública`).toBe(503);
    }
  }, 20000);
});
