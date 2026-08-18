import { describe, it, expect } from 'vitest';
import { DeliberationEngine } from '../../packages/core/src/governance/DeliberationEngine';
describe('DeliberationEngine', () => {
  it('should assess operational level', () => {
    const engine = new DeliberationEngine({
      operationalThreshold: 20,
      tacticalThreshold: 50,
      strategicThreshold: 75,
    });
    const result = engine.assessLevel({
      intent: 'Test intent',
      domain: 'test',
      criteria: {
        impact: 1,
        uncertainty: 1,
        risk: 1,
        reversibility: 9,
        cost: 1,
        dependencies: 0,
      },
    });
    expect(result.level).toBe('operational');
    expect(result.requiresApproval).toBe(false);
  });
  it('should assess tactical level', () => {
    const engine = new DeliberationEngine({
      operationalThreshold: 20,
      tacticalThreshold: 50,
      strategicThreshold: 75,
    });
    const result = engine.assessLevel({
      intent: 'Test intent',
      domain: 'test',
      criteria: {
        impact: 5,
        uncertainty: 5,
        risk: 5,
        reversibility: 5,
        cost: 5,
        dependencies: 3,
      },
    });
    expect(result.level).toBe('tactical');
    expect(result.requiresApproval).toBe(true);
  });
  it('should escalate correctly', () => {
    const engine = new DeliberationEngine();
    const escalation = engine.escalate({
      intent: 'Test intent',
      domain: 'test',
      criteria: {
        impact: 9,
        uncertainty: 9,
        risk: 9,
        reversibility: 1,
        cost: 9,
        dependencies: 10,
      },
    });
    expect(escalation.target).toBe('constitutional');
    expect(escalation.urgency).toBe('critical');
  });
});
