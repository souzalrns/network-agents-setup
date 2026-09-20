import { describe, it, expect, vi } from 'vitest';
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
      // B10/D8: sem valor resolvido, DeliberationOrchestrator.deliberate()
      // (linha 121) faz `hitlRequest.id` sobre `undefined` -- este teste
      // nunca tinha corrido antes (bloqueado por falta de `prisma generate`),
      // por isso este gap no mock nunca tinha sido exercitado.
      requestApproval: vi.fn().mockResolvedValue({ id: 'hitl-test-id' }),
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
      memory as any,
      mockHitl as any
    );
    const result = await orchestrator.processRequest('Test request', { domain: 'business' });
    expect(result).toBeDefined();
    expect(result.content).toBeDefined();
  });
});
