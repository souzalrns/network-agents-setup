import { describe, it, expect, vi, afterEach } from 'vitest';
import { OpenAIProvider } from '../../packages/core/src/llm/LLMService';

function fakeResponse(body: any, ok = true) {
  return { ok, status: ok ? 200 : 400, statusText: 'x', json: async () => body };
}

describe('OpenAIProvider — mapeamento de mensagens (S33)', () => {
  afterEach(() => vi.unstubAllGlobals());

  it('chatWithTools() envia tools + tool_choice:auto quando tools presentes', async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      fakeResponse({ choices: [{ message: { content: 'ok' } }] })
    );
    vi.stubGlobal('fetch', fetchMock);

    const provider = new OpenAIProvider('sk-test');
    await provider.chatWithTools({
      messages: [{ role: 'user', content: 'x' }],
      tools: [{ type: 'function', function: { name: 'read_file', description: 'd', parameters: {} } }],
    });

    const [, options] = fetchMock.mock.calls[0];
    const body = JSON.parse(options.body);
    expect(body.tools).toHaveLength(1);
    expect(body.tool_choice).toBe('auto');
  });

  it('chatWithTools() preserva tool_call_id numa mensagem role:tool (bug real corrigido)', async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      fakeResponse({ choices: [{ message: { content: 'final' } }] })
    );
    vi.stubGlobal('fetch', fetchMock);

    const provider = new OpenAIProvider('sk-test');
    await provider.chatWithTools({
      messages: [
        { role: 'user', content: 'x' },
        { role: 'assistant', content: '', toolCalls: [{ id: 'call_1', type: 'function', function: { name: 'read_file', arguments: '{}' } }] },
        { role: 'tool', tool_call_id: 'call_1', content: 'conteudo do ficheiro' },
      ],
    });

    const [, options] = fetchMock.mock.calls[0];
    const body = JSON.parse(options.body);
    const assistantMsg = body.messages.find((m: any) => m.role === 'assistant');
    const toolMsg = body.messages.find((m: any) => m.role === 'tool');

    expect(assistantMsg.tool_calls).toEqual([
      { id: 'call_1', type: 'function', function: { name: 'read_file', arguments: '{}' } },
    ]);
    expect(toolMsg.tool_call_id).toBe('call_1');
    expect(toolMsg.content).toBe('conteudo do ficheiro');
  });

  it('chat() (sem tools) tambem preserva tool_call_id -- mesma correcao, mesmo caminho de mapeamento', async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      fakeResponse({ choices: [{ message: { content: 'ok' } }] })
    );
    vi.stubGlobal('fetch', fetchMock);

    const provider = new OpenAIProvider('sk-test');
    await provider.chat({
      messages: [{ role: 'tool', tool_call_id: 'call_9', content: 'x' }],
    });

    const [, options] = fetchMock.mock.calls[0];
    const body = JSON.parse(options.body);
    expect(body.messages[0].tool_call_id).toBe('call_9');
  });

  it('chatWithTools() devolve toolCalls parseados da resposta real da API', async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      fakeResponse({
        choices: [
          {
            message: {
              content: '',
              tool_calls: [{ id: 'call_2', type: 'function', function: { name: 'search', arguments: '{"q":"x"}' } }],
            },
          },
        ],
      })
    );
    vi.stubGlobal('fetch', fetchMock);

    const provider = new OpenAIProvider('sk-test');
    const result = await provider.chatWithTools({ messages: [{ role: 'user', content: 'x' }] });

    expect(result.toolCalls).toEqual([
      { id: 'call_2', type: 'function', function: { name: 'search', arguments: '{"q":"x"}' } },
    ]);
  });
});
