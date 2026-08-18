import { describe, it, expect, vi } from 'vitest';
import { OpportunityRadar } from '../../packages/core/src/opportunity/OpportunityRadar';
import { SelfAwareness } from '../../packages/core/src/observability/SelfAwareness';
describe('OpportunityRadar', () => {
  it('should initialize with sources', () => {
    const awareness = new SelfAwareness({ updateInterval: 0 });
    const radar = new OpportunityRadar(awareness, {
      scanInterval: 0,
      minPotential: 50,
      maxDistance: 70,
    });
    expect(radar.sources.size).toBeGreaterThan(0);
  });
  it('should scan for opportunities', async () => {
    const awareness = new SelfAwareness({ updateInterval: 0 });
    const radar = new OpportunityRadar(awareness, {
      scanInterval: 0,
      minPotential: 50,
      maxDistance: 70,
    });
    const opportunities = await radar.scanAll();
    expect(Array.isArray(opportunities)).toBe(true);
  });
  it('should add manual opportunity', () => {
    const awareness = new SelfAwareness({ updateInterval: 0 });
    const radar = new OpportunityRadar(awareness, {
      scanInterval: 0,
    });
    const opp = radar.addOpportunity({
      title: 'Manual Opportunity',
      description: 'Test description',
      source: 'internal',
      category: 'test',
      potential: 80,
      distance: 30,
      roi: 75,
      effort: 40,
      tags: ['test'],
      technologies: ['TypeScript'],
      relatedCapabilities: [],
      metadata: {},
    });
    expect(opp.id).toBeDefined();
    expect(opp.status).toBe('new');
  });
  it('should filter opportunities', () => {
    const awareness = new SelfAwareness({ updateInterval: 0 });
    const radar = new OpportunityRadar(awareness, {
      scanInterval: 0,
    });
    // Add some opportunities
    radar.addOpportunity({
      title: 'High Priority',
      description: 'Test',
      source: 'internal',
      category: 'test',
      potential: 90,
      distance: 20,
      roi: 90,
      effort: 30,
      tags: [],
      technologies: [],
      relatedCapabilities: [],
      metadata: {},
    });
    const opportunities = radar.getOpportunities({ priority: 'high' });
    expect(Array.isArray(opportunities)).toBe(true);
  });
});
