import { describe, it, expect, vi } from 'vitest';
import { Executor } from '../../packages/core/src/orchestrator/Executor';
describe('Executor', () => {
  it('should execute a plan successfully', async () => {
    const mockAgentFactory = {
      getAgent: vi.fn().mockReturnValue({
        id: 'test-agent',
        systemPrompt: 'You are a test agent',
      }),
    };
    const mockLLM = {
      chat: vi.fn().mockResolvedValue({ content: 'Test result', usage: { tokens: 100 } }),
    };
    const mockMemory = {
      update: vi.fn(),
      executions: { update: vi.fn() },
      addMessage: vi.fn(),
      checkpoints: { create: vi.fn(), deleteByHitlRequest: vi.fn() },
      snapshot: vi.fn().mockReturnValue({}),
    };
    const mockHitl = {
      requestApproval: vi.fn(),
      getRequest: vi.fn(),
    };
    const executor = new Executor(
      mockAgentFactory as any,
      mockMemory as any,
      mockLLM as any,
      mockHitl as any
    );
    const plan = {
      id: 'test-plan',
      intent: 'Test execution',
      domain: 'test',
      steps: [
        {
          id: 'step-1',
          agentId: 'test-agent',
          description: 'Test step',
          prompt: 'Do something',
        },
      ],
    };
    const result = await executor.execute(plan, 'exec-123');
    expect(result.success).toBe(true);
    expect(result.steps).toHaveLength(1);
    expect(result.steps[0].output).toBe('Test result');
  });
  it('should handle step failure', async () => {
    const mockAgentFactory = {
      getAgent: vi.fn().mockReturnValue({
        id: 'test-agent',
        systemPrompt: 'You are a test agent',
      }),
    };
    const mockLLM = {
      chat: vi.fn().mockRejectedValue(new Error('LLM error')),
    };
    const mockMemory = {
      update: vi.fn(),
      executions: { update: vi.fn() },
      addMessage: vi.fn(),
      checkpoints: { create: vi.fn(), deleteByHitlRequest: vi.fn() },
      snapshot: vi.fn().mockReturnValue({}),
    };
    const mockHitl = {
      requestApproval: vi.fn(),
      getRequest: vi.fn(),
    };
    const executor = new Executor(
      mockAgentFactory as any,
      mockMemory as any,
      mockLLM as any,
      mockHitl as any
    );
    const plan = {
      id: 'test-plan',
      intent: 'Test execution',
      domain: 'test',
      steps: [
        {
          id: 'step-1',
          agentId: 'test-agent',
          description: 'Test step',
          prompt: 'Do something',
          critical: true,
        },
      ],
    };
    const result = await executor.execute(plan, 'exec-123');
    expect(result.success).toBe(false);
    expect(result.steps[0].success).toBe(false);
    expect(result.steps[0].error).toBe('LLM error');
  });
});
