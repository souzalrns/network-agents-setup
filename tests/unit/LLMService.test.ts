import { describe, it, expect } from 'vitest';
import { LLMService, LLMProvider, ChatOptions } from '../../packages/core/src/llm/LLMService';
import { getGlobalTracer } from '@network-agents/observability';

class FakeProvider implements LLMProvider {
  async chat(_options: ChatOptions) {
    return {
      content: 'olá',
      usage: { tokens: 30, promptTokens: 20, completionTokens: 10 },
    };
  }
  async chatWithTools(_options: ChatOptions) {
    return {
      content: '',
      toolCalls: [{ name: 'search', args: {} }],
      usage: { tokens: 50, promptTokens: 35, completionTokens: 15 },
    };
  }
}

function lastSpan() {
  const allTraces = getGlobalTracer().getAllTraces();
  const traceIds = [...allTraces.keys()];
  const lastTraceId = traceIds[traceIds.length - 1];
  const spans = allTraces.get(lastTraceId)!;
  return spans[spans.length - 1];
}

describe('LLMService (D2 — spans gen_ai.client)', () => {
  it('chat() cria span gen_ai.client.chat com atributos de modelo e tokens não-zero', async () => {
    const service = new LLMService(new FakeProvider());
    await service.chat({ messages: [{ role: 'user', content: 'oi' }], model: 'gpt-4-turbo' });

    const span = lastSpan();
    expect(span.name).toBe('gen_ai.client.chat');
    expect(span.status).toBe('ok');
    expect(span.attributes['gen_ai.request.model']).toBe('gpt-4-turbo');
    expect(span.attributes['gen_ai.usage.input_tokens']).toBe(20);
    expect(span.attributes['gen_ai.usage.output_tokens']).toBe(10);
    expect(span.attributes['gen_ai.usage.input_tokens']).toBeGreaterThan(0);
    expect(span.attributes['gen_ai.usage.output_tokens']).toBeGreaterThan(0);
  });

  it('chatWithTools() cria span gen_ai.client.chat_with_tools com atributos correctos', async () => {
    const service = new LLMService(new FakeProvider());
    await service.chatWithTools({ messages: [{ role: 'user', content: 'busca' }], model: 'gpt-4o' });

    const span = lastSpan();
    expect(span.name).toBe('gen_ai.client.chat_with_tools');
    expect(span.attributes['gen_ai.request.model']).toBe('gpt-4o');
    expect(span.attributes['gen_ai.usage.input_tokens']).toBe(35);
    expect(span.attributes['gen_ai.usage.output_tokens']).toBe(15);
  });

  it('marca o span como error e propaga a excepção quando o provider falha', async () => {
    class FailingProvider implements LLMProvider {
      async chat(): Promise<{ content: string; usage?: any }> {
        throw new Error('boom');
      }
    }
    const service = new LLMService(new FailingProvider());
    await expect(
      service.chat({ messages: [{ role: 'user', content: 'x' }] })
    ).rejects.toThrow('boom');

    const span = lastSpan();
    expect(span.status).toBe('error');
    expect(span.attributes.error).toBe('boom');
  });
});
