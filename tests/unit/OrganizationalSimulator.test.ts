import { describe, it, expect, vi } from 'vitest';
import { OrganizationalSimulator } from '../../packages/core/src/simulation/OrganizationalSimulator';
import { SelfAwareness } from '../../packages/core/src/observability/SelfAwareness';
describe('OrganizationalSimulator', () => {
  it('should create a scenario', () => {
    const awareness = new SelfAwareness({ updateInterval: 0 });
    const simulator = new OrganizationalSimulator(awareness, {
      maxConcurrentSimulations: 5,
      defaultSteps: 50,
    });
    const scenario = simulator.createScenario({
      name: 'Test Scenario',
      description: 'Test description',
      type: 'architectural',
      parameters: { test: true },
      duration: 10,
      steps: 20,
    });
    expect(scenario.id).toBeDefined();
    expect(scenario.status).toBe('draft');
  });
  it('should run a simulation', async () => {
    const awareness = new SelfAwareness({ updateInterval: 0 });
    await awareness.updateState();
    const simulator = new OrganizationalSimulator(awareness, {
      maxConcurrentSimulations: 5,
      defaultSteps: 10,
    });
    const scenario = simulator.createScenario({
      name: 'Test Scenario',
      description: 'Test description',
      type: 'architectural',
      parameters: { test: true },
      duration: 5,
      steps: 10,
    });
    const result = await simulator.runSimulation(scenario.id);
    expect(result).toBeDefined();
    expect(result.metrics).toBeDefined();
    expect(result.events).toBeDefined();
  });
  it('should generate report', async () => {
    const awareness = new SelfAwareness({ updateInterval: 0 });
    await awareness.updateState();
    const simulator = new OrganizationalSimulator(awareness, {
      maxConcurrentSimulations: 5,
      defaultSteps: 10,
    });
    const scenario = simulator.createScenario({
      name: 'Test Scenario',
      description: 'Test description',
      type: 'architectural',
      parameters: { test: true },
      duration: 5,
      steps: 10,
    });
    await simulator.runSimulation(scenario.id);
    const report = simulator.generateReport(scenario.id);
    expect(report).toBeDefined();
    expect(report).toContain('RELATÓRIO DE SIMULAÇÃO');
  });
});
