import { describe, it, expect } from 'vitest';
import { ComplianceManager } from '../../packages/core/src/compliance/ComplianceManager';

const make = () => new ComplianceManager({} as any, {} as any, {} as any);

describe('ComplianceManager — pedidos do titular sem mentiras', () => {
  it('sem executor, o pedido de apagamento NÃO fica concluído', async () => {
    const m = make();
    const req = m.requestDataAccess('u1', 'erasure');
    const done = await m.processDataRequest(req.id);
    expect(done?.status).toBe('pending');
    expect(done?.response).toMatch(/Sem executor/);
    expect(m.getStats().completedDataRequests).toBe(0);
    expect(m.getStats().complianceScore).toBe(50);
  });

  it('com executor registado, conclui e guarda a resposta real', async () => {
    const m = make();
    m.registerDataRequestHandler('erasure', () => '3 registos apagados');
    const req = m.requestDataAccess('u1', 'erasure');
    const done = await m.processDataRequest(req.id);
    expect(done?.status).toBe('completed');
    expect(done?.response).toBe('3 registos apagados');
    expect(m.getStats().complianceScore).toBe(100);
  });

  it('se o executor falhar, não dá como concluído', async () => {
    const m = make();
    m.registerDataRequestHandler('erasure', () => {
      throw new Error('base indisponível');
    });
    const req = m.requestDataAccess('u1', 'erasure');
    const done = await m.processDataRequest(req.id);
    expect(done?.status).toBe('pending');
    expect(done?.response).toMatch(/base indisponível/);
  });

  it('sem dados, a pontuação é 100 e sobe/desce com as auditorias', () => {
    const m = make();
    expect(m.getStats().complianceScore).toBe(100);
    m.logAudit({ userId: 'u', action: 'a', resource: 'r', details: {}, status: 'failure' });
    expect(m.getStats().complianceScore).toBe(50);
  });
});
