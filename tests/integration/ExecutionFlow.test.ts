import { describe, it, expect } from 'vitest';
import { Orchestrator } from '../../packages/core/src/orchestrator/Orchestrator';
import { Router } from '../../packages/core/src/orchestrator/Router';
import { Planner } from '../../packages/core/src/orchestrator/Planner';
import { Executor } from '../../packages/core/src/orchestrator/Executor';
import { MemoryManager } from '../../packages/memory/src/MemoryManager';
describe('Execution Flow Integration', () => {
  it('should process a complete request', async () => {
    const memory = new MemoryManager({});
    const router = new Router();
    const mockAgentFactory = {
      getAgentsByDomain: vi.fn().mockReturnValue([
        { id: 'test-agent', description: 'Test agent' },
      ]),
      getAgent: vi.fn().mockReturnValue({
        id: 'test-agent',
        systemPrompt: 'You are a test agent',
      }),
    };
    const mockLLM = {
      chat: vi.fn().mockResolvedValue({ content: 'Test response' }),
    };
    const mockHitl = {
      requestApproval: vi.fn(),
      getRequest: vi.fn(),
    };
    const planner = new Planner(mockAgentFactory as any, mockLLM as any);
    const executor = new Executor(
      mockAgentFactory as any,
      memory as any,
      mockLLM as any,
      mockHitl as any
    );
    const orchestrator = new Orchestrator(
      mockAgentFactory as any,
      router,
      planner,
      executor,
      memory as any
    );
    const result = await orchestrator.processRequest('Test request', { domain: 'business' });
    expect(result).toBeDefined();
    expect(result.content).toBeDefined();
  });
});
