import { describe, it, expect, vi } from 'vitest';
import { TokenEconomy } from '../../packages/core/src/economy/TokenEconomy';
describe('TokenEconomy', () => {
  it('should allocate budget', () => {
    const economy = new TokenEconomy({
      defaultBudget: 1000000,
    });
    const budget = economy.allocateBudget('exec_001', 10000);
    expect(budget.allocated).toBe(10000);
    expect(budget.used).toBe(0);
  });
  it('should record usage', () => {
    const economy = new TokenEconomy();
    economy.allocateBudget('exec_001', 10000);
    
    economy.recordUsage('exec_001', {
      model: 'gpt-4-turbo',
      inputTokens: 100,
      outputTokens: 200,
      totalTokens: 300,
      estimatedCost: 0.003,
      timestamp: new Date(),
    });
    const budget = economy.budgets.get('exec_001');
    expect(budget?.used).toBe(300);
  });
  it('should estimate cost', () => {
    const economy = new TokenEconomy();
    const cost = economy.estimateCost('gpt-4-turbo', 100, 200);
    expect(cost.totalTokens).toBe(300);
    expect(cost.estimatedCost).toBeGreaterThan(0);
  });
  it('should get optimizations', () => {
    const economy = new TokenEconomy({
      minSavingsForOptimization: 100,
    });
    economy.allocateBudget('exec_001', 10000);
    economy.recordUsage('exec_001', {
      model: 'gpt-4-turbo',
      inputTokens: 1000,
      outputTokens: 2000,
      totalTokens: 3000,
      estimatedCost: 0.03,
      timestamp: new Date(),
    });
    const optimizations = economy.getOptimizations('exec_001');
    expect(optimizations).toBeDefined();
    expect(optimizations.length).toBeGreaterThan(0);
  });
  it('should search before build', async () => {
    const economy = new TokenEconomy();
    const result = await economy.searchBeforeBuild({
      type: 'capability',
      description: 'OCR de documentos',
      domain: 'legal',
    });
    expect(result).toHaveProperty('exists');
    expect(result).toHaveProperty('alternatives');
    expect(result).toHaveProperty('recommendation');
  });
});
