import { describe, it, expect, vi } from 'vitest';
import http from 'http';
import { errorHandler } from '../../apps/api/src/middleware/errorHandler';
import { ChatController } from '../../apps/api/src/controllers/ChatController';
import { HitlController } from '../../apps/api/src/controllers/HitlController';
import { setupWebSocket } from '../../apps/api/src/websocket';

const SENSITIVE = /10\.0\.0\.5|ECONNREFUSED|\/internal\/|at .*\.ts:\d+/;

function mockRes() {
  const res: any = {};
  res.status = vi.fn().mockReturnValue(res);
  res.json = vi.fn().mockReturnValue(res);
  res.setHeader = vi.fn();
  res.write = vi.fn();
  res.end = vi.fn();
  return res;
}

describe('errorHandler (Express, central) — não expõe detalhe (A18)', () => {
  it('erro real (com stack) devolve mensagem genérica em produção', () => {
    const original = process.env.NODE_ENV;
    process.env.NODE_ENV = 'production';
    const err: any = new Error('connect ECONNREFUSED 10.0.0.5:5432 at /internal/db.ts:99');
    const req: any = { path: '/api/chat' };
    const res = mockRes();
    errorHandler(err, req, res, vi.fn());
    process.env.NODE_ENV = original;

    expect(res.status).toHaveBeenCalledWith(500);
    const body = res.json.mock.calls[0][0];
    expect(body.error).toBe('Erro ao processar pedido');
    expect(body.error).not.toMatch(SENSITIVE);
    expect(body.stack).toBeUndefined();
  });
});

describe('ChatController — não expõe detalhe (A18)', () => {
  it('processChat: erro real do orchestrator devolve mensagem genérica', async () => {
    const orchestrator: any = {
      processRequest: vi.fn().mockRejectedValue(new Error('connect ECONNREFUSED 10.0.0.5:5432')),
    };
    const controller = new ChatController(orchestrator, {} as any);
    const req: any = { body: { message: 'olá' } };
    const res = mockRes();
    await controller.processChat(req, res);
    const body = res.json.mock.calls[0][0];
    expect(body.status).toBe('failed');
    expect(body.errors[0]).toBe('Erro ao processar pedido de chat');
    expect(body.errors[0]).not.toMatch(SENSITIVE);
  });
});

describe('HitlController — não expõe detalhe (A18)', () => {
  it('approveRequest: erro real do hitlManager devolve mensagem genérica', async () => {
    const hitlManager: any = {
      approveRequest: vi.fn().mockRejectedValue(new Error('connect ECONNREFUSED 10.0.0.5:5432')),
    };
    const controller = new HitlController(hitlManager);
    const req: any = { params: { id: 'x' }, body: { responderId: 'r1' } };
    const res = mockRes();
    await controller.approveRequest(req, res);
    expect(res.status).toHaveBeenCalledWith(400);
    const body = res.json.mock.calls[0][0];
    expect(body.error).toBe('Erro ao aprovar pedido');
    expect(body.error).not.toMatch(SENSITIVE);
  });

  it('rejectRequest: erro real do hitlManager devolve mensagem genérica', async () => {
    const hitlManager: any = {
      rejectRequest: vi.fn().mockRejectedValue(new Error('connect ECONNREFUSED 10.0.0.5:5432')),
    };
    const controller = new HitlController(hitlManager);
    const req: any = { params: { id: 'x' }, body: { responderId: 'r1' } };
    const res = mockRes();
    await controller.rejectRequest(req, res);
    const body = res.json.mock.calls[0][0];
    expect(body.error).toBe('Erro ao rejeitar pedido');
    expect(body.error).not.toMatch(SENSITIVE);
  });
});

describe('websocket.ts — handlers não expõem detalhe (A18)', () => {
  it('chat:send: erro real do orchestrator devolve payload genérico', async () => {
    const httpServer = http.createServer();
    const orchestrator: any = {
      processRequest: vi.fn().mockRejectedValue(new Error('connect ECONNREFUSED 10.0.0.5:5432')),
    };
    const wsServer = setupWebSocket(httpServer, orchestrator, {} as any, {} as any, {} as any);
    const result: any = await new Promise((resolve) => {
      wsServer.emit('chat:send', { message: 'olá', userId: 'u1' }, (res: any, err: any) => resolve(err || res));
    });
    wsServer.close();
    expect(result).toEqual({ error: 'Erro ao processar mensagem de chat' });
    expect(result.error).not.toMatch(SENSITIVE);
  });

  it('hitl:approve: erro real do hitlManager devolve payload genérico', async () => {
    const httpServer = http.createServer();
    const hitlManager: any = {
      approveRequest: vi.fn().mockRejectedValue(new Error('connect ECONNREFUSED 10.0.0.5:5432')),
    };
    const wsServer = setupWebSocket(httpServer, {} as any, hitlManager, {} as any, {} as any);
    const result: any = await new Promise((resolve) => {
      wsServer.emit('hitl:approve', { hitlId: 'h1', responderId: 'r1' }, (res: any, err: any) => resolve(err || res));
    });
    wsServer.close();
    expect(result).toEqual({ error: 'Erro ao aprovar pedido HITL' });
    expect(result.error).not.toMatch(SENSITIVE);
  });

  it('agent:list: erro real do agentFactory devolve payload genérico', async () => {
    const httpServer = http.createServer();
    const agentFactory: any = {
      getAllAgents: vi.fn().mockImplementation(() => {
        throw new Error('connect ECONNREFUSED 10.0.0.5:5432');
      }),
    };
    const wsServer = setupWebSocket(httpServer, {} as any, {} as any, agentFactory, {} as any);
    const result: any = await new Promise((resolve) => {
      wsServer.emit('agent:list', {}, (res: any, err: any) => resolve(err || res));
    });
    wsServer.close();
    expect(result).toEqual({ error: 'Erro ao listar agentes' });
    expect(result.error).not.toMatch(SENSITIVE);
  });
});
