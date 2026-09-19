import { describe, it, expect, vi, afterEach } from 'vitest';
import { toClientError as toClientErrorMcp } from '../../packages/mcp/src/util/sanitizeError';
import { toClientError as toClientErrorApi } from '../../apps/api/src/utils/sanitizeError';

describe('sanitizeError (packages/mcp) — toClientError', () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('devolve mensagem genérica com o contexto, nunca o detalhe do erro', () => {
    const error = new Error('connect ECONNREFUSED 10.0.0.5:5432 at /internal/secret/path.ts:42');
    const message = toClientErrorMcp(error, 'na consulta à base de dados');
    expect(message).toBe('Erro na consulta à base de dados');
    expect(message).not.toMatch(/10\.0\.0\.5/);
    expect(message).not.toMatch(/ECONNREFUSED/);
    expect(message).not.toMatch(/\/internal\/secret/);
  });

  it('regista o detalhe completo internamente (console.error), não o perde', () => {
    const spy = vi.spyOn(console, 'error').mockImplementation(() => {});
    const error = new Error('detalhe interno sensível');
    toClientErrorMcp(error, 'ao ler ficheiro');
    expect(spy).toHaveBeenCalledWith(expect.stringContaining('Erro ao ler ficheiro'), error);
  });
});

describe('sanitizeError (apps/api) — toClientError', () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('devolve mensagem genérica com o contexto, nunca o detalhe do erro', () => {
    const error = new Error('ECONNREFUSED 10.0.0.5:5432, stack em /internal/secret.ts');
    const message = toClientErrorApi(error, 'ao processar pedido');
    expect(message).toBe('Erro ao processar pedido');
    expect(message).not.toMatch(/10\.0\.0\.5/);
    expect(message).not.toMatch(/ECONNREFUSED/);
  });

  it('regista o detalhe completo no logger interno (não console.error directo)', () => {
    const spy = vi.spyOn(console, 'log').mockImplementation(() => {});
    const error = new Error('detalhe interno sensível para o log');
    toClientErrorApi(error, 'ao aprovar pedido');
    expect(spy).toHaveBeenCalled();
    const logged = JSON.parse(spy.mock.calls[0][0] as string);
    expect(logged.level).toBe('error');
    expect(logged.metadata.message).toBe('detalhe interno sensível para o log');
  });
});
