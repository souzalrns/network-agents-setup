import { describe, it, expect, vi } from 'vitest';
import { SelfAwareness } from '../../packages/core/src/observability/SelfAwareness';
describe('SelfAwareness', () => {
  it('should update state', async () => {
    const awareness = new SelfAwareness({
      updateInterval: 0, // Disable auto-update
    });
    const state = await awareness.updateState();
    expect(state).toBeDefined();
    expect(state.timestamp).toBeInstanceOf(Date);
    expect(state.capabilities).toBeDefined();
    expect(state.agents).toBeDefined();
    expect(state.costs).toBeDefined();
    expect(state.health).toBeDefined();
  });
  it('should get health trend', async () => {
    const awareness = new SelfAwareness({
      updateInterval: 0,
    });
    await awareness.updateState();
    await awareness.updateState();
    const trend = awareness.getHealthTrend();
    expect(trend).toHaveProperty('direction');
    expect(trend).toHaveProperty('rate');
    expect(trend).toHaveProperty('indicators');
  });
  it('should generate report', async () => {
    const awareness = new SelfAwareness({
      updateInterval: 0,
    });
    await awareness.updateState();
    const report = awareness.generateReport();
    expect(report).toBeDefined();
    expect(report.length).toBeGreaterThan(100);
    expect(report).toContain('RELATÓRIO DE AUTOPERCEPÇÃO');
  });
  it('should get recommendations', async () => {
    const awareness = new SelfAwareness({
      updateInterval: 0,
    });
    await awareness.updateState();
    const recommendations = awareness.getRecommendations();
    expect(Array.isArray(recommendations)).toBe(true);
  });
});
