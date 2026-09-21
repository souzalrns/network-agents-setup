import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { Executor } from '../../packages/core/src/orchestrator/Executor';
import { ToolRegistry } from '../../packages/mcp/src/tools/ToolRegistry';
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

  describe('S33 — tools reais chegam a chatWithTools()', () => {
    // Isola o audit.jsonl/.chain reais do ToolPolicy/ActionReceipt (senão
    // escrevem na raiz do repo -- mesmo padrão de ToolExecutor.test.ts).
    const ORIGINAL_ENV = { ...process.env };
    let tmpDir: string;

    beforeEach(async () => {
      const fs = await import('fs/promises');
      const os = await import('os');
      const path = await import('path');
      tmpDir = await fs.mkdtemp(path.join(os.tmpdir(), 'executor-tools-'));
      process.env.MCP_AUDIT_LOG_PATH = path.join(tmpDir, 'audit.jsonl');
    });

    afterEach(async () => {
      process.env = { ...ORIGINAL_ENV };
      const fs = await import('fs/promises');
      await fs.rm(tmpDir, { recursive: true, force: true });
    });

    function baseMocks() {
      const mockAgentFactory = {
        getAgent: vi.fn().mockReturnValue({ id: 'test-agent', systemPrompt: 'You are a test agent' }),
      };
      const mockMemory = {
        update: vi.fn(),
        executions: { update: vi.fn() },
        addMessage: vi.fn(),
        checkpoints: { create: vi.fn(), deleteByHitlRequest: vi.fn() },
        snapshot: vi.fn().mockReturnValue({}),
      };
      const mockHitl = { requestApproval: vi.fn(), getRequest: vi.fn() };
      return { mockAgentFactory, mockMemory, mockHitl };
    }

    function plan(step: Record<string, any>) {
      return {
        id: 'test-plan',
        intent: 'Test execution',
        domain: 'test',
        steps: [{ id: 'step-1', agentId: 'test-agent', description: 'Test step', prompt: 'Do something', ...step }],
      };
    }

    it('step sem toolsAllowed nunca chama chatWithTools() (não-regressão)', async () => {
      const { mockAgentFactory, mockMemory, mockHitl } = baseMocks();
      const mockLLM = {
        chat: vi.fn().mockResolvedValue({ content: 'sem tools', usage: { tokens: 5 } }),
        chatWithTools: vi.fn(),
      };
      // "read_file" -- ToolPolicy.SCOPES so autoriza os 6 nomes reais
      // (read_file/write_file/list_directory/http_request/scrape_webpage/
      // query_database); um nome inventado seria sempre "unknown_tool".
      const registry = new ToolRegistry([
        { name: 'read_file', description: 'd', inputSchema: { type: 'object', properties: {} }, execute: vi.fn() },
      ]);
      const executor = new Executor(mockAgentFactory as any, mockMemory as any, mockLLM as any, mockHitl as any, registry);

      const result = await executor.execute(plan({}) as any, 'exec-1');

      expect(mockLLM.chatWithTools).not.toHaveBeenCalled();
      expect(mockLLM.chat).toHaveBeenCalledOnce();
      expect(result.steps[0].output).toBe('sem tools');
    });

    it('step com toolsAllowed, sem ToolRegistry no Executor, cai no caminho antigo (não-regressão do construtor de 4 argumentos)', async () => {
      const { mockAgentFactory, mockMemory, mockHitl } = baseMocks();
      const mockLLM = {
        chat: vi.fn().mockResolvedValue({ content: 'sem registry', usage: { tokens: 5 } }),
        chatWithTools: vi.fn(),
      };
      const executor = new Executor(mockAgentFactory as any, mockMemory as any, mockLLM as any, mockHitl as any);

      const result = await executor.execute(plan({ toolsAllowed: ['read_file'] }) as any, 'exec-1');

      expect(mockLLM.chatWithTools).not.toHaveBeenCalled();
      expect(result.steps[0].output).toBe('sem registry');
    });

    it('LLM pede uma tool real → ToolExecutor executa-a de facto → resultado volta como role:tool → 2ª chamada sintetiza', async () => {
      const { mockAgentFactory, mockMemory, mockHitl } = baseMocks();
      const readFileExecute = vi.fn().mockResolvedValue({ content: [{ type: 'text', text: 'conteudo:ola.txt' }] });
      const registry = new ToolRegistry([
        { name: 'read_file', description: 'le um ficheiro', inputSchema: { type: 'object', properties: { path: { type: 'string' } } }, execute: readFileExecute },
      ]);
      const mockLLM = {
        chatWithTools: vi.fn().mockResolvedValue({
          content: '',
          toolCalls: [{ id: 'call_1', function: { name: 'read_file', arguments: '{"path":"ola.txt"}' } }],
          usage: { tokens: 10 },
        }),
        chat: vi.fn().mockResolvedValue({ content: 'resposta final com o eco', usage: { tokens: 7 } }),
      };
      const executor = new Executor(mockAgentFactory as any, mockMemory as any, mockLLM as any, mockHitl as any, registry);

      const result = await executor.execute(plan({ toolsAllowed: ['read_file'] }) as any, 'exec-1');

      // A tool foi mesmo executada (via ToolExecutor real, com policy/audit/receipt do C1/A8/S11)
      expect(readFileExecute).toHaveBeenCalledWith({ path: 'ola.txt' });

      // A 2ª chamada (.chat) recebeu a mensagem assistant com tool_calls + a mensagem tool com o resultado real
      const secondCallMessages = mockLLM.chat.mock.calls[0][0].messages;
      const toolMsg = secondCallMessages.find((m: any) => m.role === 'tool');
      expect(toolMsg.tool_call_id).toBe('call_1');
      expect(toolMsg.content).toBe('conteudo:ola.txt');

      expect(result.steps[0].output).toBe('resposta final com o eco');
      expect(result.steps[0].tokens).toBe(17); // 10 (chatWithTools) + 7 (chat final)
    });

    it('LLM não pede nenhuma tool → devolve logo o content da 1ª chamada, sem 2ª chamada a chat()', async () => {
      const { mockAgentFactory, mockMemory, mockHitl } = baseMocks();
      const registry = new ToolRegistry([
        { name: 'read_file', description: 'd', inputSchema: { type: 'object', properties: {} }, execute: vi.fn() },
      ]);
      const mockLLM = {
        chatWithTools: vi.fn().mockResolvedValue({ content: 'respondeu sem tool', usage: { tokens: 4 } }),
        chat: vi.fn(),
      };
      const executor = new Executor(mockAgentFactory as any, mockMemory as any, mockLLM as any, mockHitl as any, registry);

      const result = await executor.execute(plan({ toolsAllowed: ['read_file'] }) as any, 'exec-1');

      expect(mockLLM.chat).not.toHaveBeenCalled();
      expect(result.steps[0].output).toBe('respondeu sem tool');
    });
  });
});
