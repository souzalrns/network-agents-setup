import { describe, it, expect } from 'vitest';
import { SecurityManager } from '../../packages/core/src/security/SecurityManager';
import { DataGovernance } from '../../packages/core/src/data/DataGovernance';

describe('DataGovernance.observeData', () => {
  it('não inventa activos para uma fonte desconhecida', async () => {
    const d = new (DataGovernance as any)(new SecurityManager());
    expect(await d.observeData('api://nao-existe')).toEqual([]);
  });

  it('devolve o que foi registado para a fonte', async () => {
    const d = new (DataGovernance as any)(new SecurityManager());
    d.registerDataAsset({
      name: 'clientes', type: 'structured', source: 'db://x', format: 'sql', size: 1, owner: 'o',
      classification: 'internal', retentionDays: 30, tags: [], lineage: { source: 'db://x', transformations: [] }, metadata: {},
    });
    const got = await d.observeData('db://x');
    expect(got).toHaveLength(1);
    expect(got[0].name).toBe('clientes');
  });
});
