import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { authMiddleware, assertAuthConfig } from '../../apps/api/src/middleware/auth';

function mockRes() {
  const res: any = {};
  res.status = vi.fn().mockReturnValue(res);
  res.json = vi.fn().mockReturnValue(res);
  return res;
}

const ORIGINAL_ENV = { ...process.env };

describe('authMiddleware (fail-closed)', () => {
  beforeEach(() => {
    delete process.env.API_KEY;
    delete process.env.ALLOW_UNAUTHENTICATED;
    delete process.env.NODE_ENV;
  });

  afterEach(() => {
    process.env = { ...ORIGINAL_ENV };
  });

  it('recusa com 503 quando API_KEY não está configurada', () => {
    const res = mockRes();
    const next = vi.fn();
    authMiddleware({ headers: {} } as any, res, next);
    expect(next).not.toHaveBeenCalled();
    expect(res.status).toHaveBeenCalledWith(503);
  });

  it('recusa com 401 quando a chave enviada está errada', () => {
    process.env.API_KEY = 'chave-correta';
    const res = mockRes();
    const next = vi.fn();
    authMiddleware({ headers: { 'x-api-key': 'chave-errada' } } as any, res, next);
    expect(next).not.toHaveBeenCalled();
    expect(res.status).toHaveBeenCalledWith(401);
  });

  it('deixa passar quando a chave está correta', () => {
    process.env.API_KEY = 'chave-correta';
    const res = mockRes();
    const next = vi.fn();
    authMiddleware({ headers: { 'x-api-key': 'chave-correta' } } as any, res, next);
    expect(next).toHaveBeenCalled();
    expect(res.status).not.toHaveBeenCalled();
  });

  it('recusa quando não é enviado header nenhum, mesmo com chave configurada', () => {
    process.env.API_KEY = 'chave-correta';
    const res = mockRes();
    const next = vi.fn();
    authMiddleware({ headers: {} } as any, res, next);
    expect(next).not.toHaveBeenCalled();
    expect(res.status).toHaveBeenCalledWith(401);
  });

  it('permite sem chave apenas com ALLOW_UNAUTHENTICATED fora de produção', () => {
    process.env.ALLOW_UNAUTHENTICATED = 'true';
    process.env.NODE_ENV = 'development';
    const res = mockRes();
    const next = vi.fn();
    authMiddleware({ headers: {} } as any, res, next);
    expect(next).toHaveBeenCalled();
  });

  it('ignora ALLOW_UNAUTHENTICATED em produção (continua fail-closed)', () => {
    process.env.ALLOW_UNAUTHENTICATED = 'true';
    process.env.NODE_ENV = 'production';
    const res = mockRes();
    const next = vi.fn();
    authMiddleware({ headers: {} } as any, res, next);
    expect(next).not.toHaveBeenCalled();
    expect(res.status).toHaveBeenCalledWith(503);
  });
});

describe('assertAuthConfig', () => {
  beforeEach(() => {
    delete process.env.API_KEY;
    delete process.env.ALLOW_UNAUTHENTICATED;
    delete process.env.NODE_ENV;
  });

  afterEach(() => {
    process.env = { ...ORIGINAL_ENV };
  });

  it('lança em produção sem API_KEY', () => {
    process.env.NODE_ENV = 'production';
    expect(() => assertAuthConfig()).toThrow(/API_KEY em falta/);
  });

  it('devolve ok com API_KEY configurada', () => {
    process.env.API_KEY = 'x';
    expect(assertAuthConfig()).toEqual({ ok: true });
  });

  it('avisa (sem lançar) em desenvolvimento sem chave', () => {
    process.env.NODE_ENV = 'development';
    const result = assertAuthConfig();
    expect(result.ok).toBe(false);
    expect(result.warning).toMatch(/503/);
  });
});
