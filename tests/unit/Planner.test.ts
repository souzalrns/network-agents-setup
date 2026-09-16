import { describe, it, expect, vi } from 'vitest';
import { Planner } from '../../packages/core/src/orchestrator/Planner';

describe('Planner', () => {
  const mockAgentFactory = {} as any;

  const domainAgents = [
    { id: 'research-agent', description: 'Research', domain: 'marketing' },
    { id: 'copy-agent', description: 'Copy', domain: 'marketing' },
  ];

  function makePlanner(responseContent: string) {
    const mockLLM = {
      chat: vi.fn().mockResolvedValue({ content: responseContent }),
    };
    const planner = new Planner(mockAgentFactory, mockLLM as any);
    return { planner, mockLLM };
  }

  it('should build a plan from valid LLM JSON', async () => {
    const llmJson = JSON.stringify({
      intent: 'Criar artigo SEO',
      steps: [
        { id: 'step_1', agentId: 'research-agent', description: 'Pesquisar' },
        { id: 'step_2', agentId: 'copy-agent', description: 'Escrever' },
      ],
      finalConsolidator: 'copy-agent',
    });
    const { planner } = makePlanner(llmJson);
    const plan = await planner.plan('artigo seo', domainAgents);

    expect(plan.intent).toBe('Criar artigo SEO');
    expect(plan.steps).toHaveLength(2);
    expect(plan.steps[0].agentId).toBe('research-agent');
    expect(plan.finalConsolidator).toBe('copy-agent');
    expect(plan.id).toMatch(/^plan_/);
  });

  it('should extract JSON from LLM text with surrounding noise', async () => {
    const llmJson =
      'Aqui está o plano:\n' +
      JSON.stringify({
        intent: 'X',
        steps: [{ id: 's1', agentId: 'research-agent', description: 'D' }],
      }) +
      '\nFim.';
    const { planner } = makePlanner(llmJson);

    const plan = await planner.plan('x', domainAgents);
    expect(plan.steps).toHaveLength(1);
  });

  it('should propagate domain and conversationId from context', async () => {
    const llmJson = JSON.stringify({
      intent: 'X',
      steps: [{ id: 's1', agentId: 'copy-agent', description: 'D' }],
    });
    const { planner } = makePlanner(llmJson);

    const plan = await planner.plan('x', domainAgents, {
      domain: 'marketing',
      conversationId: 'conv-1',
    });

    expect(plan.domain).toBe('marketing');
    expect(plan.conversationId).toBe('conv-1');
  });

  it('should default domain to general when context missing', async () => {
    const llmJson = JSON.stringify({
      intent: 'X',
      steps: [{ id: 's1', agentId: 'copy-agent', description: 'D' }],
    });
    const { planner } = makePlanner(llmJson);

    const plan = await planner.plan('x', domainAgents);
    expect(plan.domain).toBe('general');
  });

  it('should fallback when LLM returns invalid JSON', async () => {
    const { planner } = makePlanner('isto nao e JSON');
    const plan = await planner.plan('tarefa', domainAgents);

    expect(plan.id).toMatch(/^plan_fallback_/);
    expect(plan.intent).toBe('tarefa');
    expect(plan.steps).toHaveLength(1);
    expect(plan.steps[0].agentId).toBe('research-agent');
  });

  it('should fallback when LLM plan references an unknown agent', async () => {
    const llmJson = JSON.stringify({
      intent: 'X',
      steps: [{ id: 's1', agentId: 'agente-inexistente', description: 'D' }],
    });
    const { planner } = makePlanner(llmJson);
    const plan = await planner.plan('x', domainAgents);

    expect(plan.id).toMatch(/^plan_fallback_/);
  });

  it('should handle empty steps array', async () => {
    const llmJson = JSON.stringify({ intent: 'X', steps: [] });
    const { planner } = makePlanner(llmJson);

    const plan = await planner.plan('x', domainAgents);
    expect(plan.steps).toEqual([]);
  });

  it('should use input as intent when LLM omits intent', async () => {
    const llmJson = JSON.stringify({
      steps: [{ id: 's1', agentId: 'copy-agent', description: 'D' }],
    });
    const { planner } = makePlanner(llmJson);

    const plan = await planner.plan('tarefa original', domainAgents);
    expect(plan.intent).toBe('tarefa original');
  });

  it('should include metadata priority (default medium)', async () => {
    const llmJson = JSON.stringify({
      intent: 'X',
      steps: [{ id: 's1', agentId: 'copy-agent', description: 'D' }],
    });
    const { planner } = makePlanner(llmJson);

    const plan = await planner.plan('x', domainAgents);
    expect(plan.metadata?.priority).toBe('medium');
  });

  it('should call llm.chat with temperature 0.2', async () => {
    const llmJson = JSON.stringify({
      intent: 'X',
      steps: [{ id: 's1', agentId: 'copy-agent', description: 'D' }],
    });
    const { planner, mockLLM } = makePlanner(llmJson);
    await planner.plan('x', domainAgents);

    expect(mockLLM.chat).toHaveBeenCalledOnce();
    const callArg = mockLLM.chat.mock.calls[0][0];
    expect(callArg.temperature).toBe(0.2);
  });
});