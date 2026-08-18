import { describe, it, expect } from 'vitest';
import { ImmunologicalMemory } from '../../packages/core/src/immunity/ImmunologicalMemory';
describe('ImmunologicalMemory', () => {
  it('should register an event', () => {
    const memory = new ImmunologicalMemory();
    const event = memory.registerEvent({
      type: 'incident',
      severity: 'high',
      description: 'Test incident',
      rootCause: 'test_cause',
      impact: {
        components: ['test'],
        durationMs: 1000,
        dataLoss: false,
        serviceDegradation: true,
      },
      response: {
        action: 'test_action',
        executedBy: 'test',
        durationMs: 100,
        success: true,
      },
      learnings: ['Learning 1'],
      recommendations: ['Recommendation 1'],
      status: 'open',
      recurrenceCount: 0,
      similarEvents: [],
      metadata: {},
    });
    expect(event.id).toBeDefined();
    expect(event.type).toBe('incident');
    expect(event.status).toBe('open');
  });
  it('should update event status', () => {
    const memory = new ImmunologicalMemory();
    const event = memory.registerEvent({
      type: 'incident',
      severity: 'high',
      description: 'Test incident',
      rootCause: 'test_cause',
      impact: {
        components: ['test'],
        durationMs: 1000,
        dataLoss: false,
        serviceDegradation: true,
      },
      response: {
        action: 'test_action',
        executedBy: 'test',
        durationMs: 100,
        success: true,
      },
      learnings: ['Learning 1'],
      recommendations: ['Recommendation 1'],
      status: 'open',
      recurrenceCount: 0,
      similarEvents: [],
      metadata: {},
    });
    const updated = memory.updateEvent(event.id, {
      status: 'resolved',
    });
    expect(updated.status).toBe('resolved');
    expect(updated.resolvedAt).toBeDefined();
  });
  it('should detect patterns', () => {
    const memory = new ImmunologicalMemory();
    // Register multiple events
    memory.registerEvent({
      type: 'incident',
      severity: 'high',
      description: 'Test incident 1',
      rootCause: 'test_cause',
      impact: {
        components: ['test'],
        durationMs: 1000,
        dataLoss: false,
        serviceDegradation: true,
      },
      response: {
        action: 'test_action',
        executedBy: 'test',
        durationMs: 100,
        success: true,
      },
      learnings: ['Learning 1'],
      recommendations: ['Recommendation 1'],
      status: 'open',
      recurrenceCount: 0,
      similarEvents: [],
      metadata: {},
    });
    const patterns = memory.getActivePatterns();
    expect(Array.isArray(patterns)).toBe(true);
  });
  it('should calculate entropy', () => {
    const memory = new ImmunologicalMemory();
    const entropy = memory.calculateEntropy();
    expect(entropy.totalEntropy).toBeDefined();
    expect(entropy.byCategory).toBeDefined();
    expect(entropy.trends).toBeDefined();
    expect(entropy.recommendations).toBeDefined();
  });
  it('should generate report', () => {
    const memory = new ImmunologicalMemory();
    const report = memory.generateReport();
    expect(report).toBeDefined();
    expect(report).toContain('RELATÓRIO IMUNOLÓGICO');
  });
  it('should get stats', () => {
    const memory = new ImmunologicalMemory();
    const stats = memory.getStats();
    expect(stats).toHaveProperty('totalEvents');
    expect(stats).toHaveProperty('activeEvents');
    expect(stats).toHaveProperty('resolvedEvents');
    expect(stats).toHaveProperty('patterns');
    expect(stats).toHaveProperty('antibodies');
    expect(stats).toHaveProperty('entropy');
    expect(stats).toHaveProperty('health');
  });
});
