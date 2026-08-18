export interface ChatMessage {
  role: 'system' | 'user' | 'assistant' | 'tool';
  content: string;
  tool_call_id?: string;
}
export interface ChatOptions {
  system?: string;
  messages: ChatMessage[];
  temperature?: number;
  maxTokens?: number;
  model?: string;
  tools?: any[];
}
export interface LLMProvider {
  chat(options: ChatOptions): Promise<{ content: string; usage?: { tokens: number } }>;
  chatWithTools?(options: ChatOptions): Promise<{
    content: string;
    toolCalls?: any[];
    usage?: { tokens: number };
  }>;
}
export class LLMService {
  constructor(private provider: LLMProvider) {}
  async chat(options: ChatOptions): Promise<{ content: string; usage?: { tokens: number } }> {
    return this.provider.chat(options);
  }
  async chatWithTools(options: ChatOptions): Promise<{
    content: string;
    toolCalls?: any[];
    usage?: { tokens: number };
  }> {
    if (this.provider.chatWithTools) {
      return this.provider.chatWithTools(options);
    }
    const result = await this.provider.chat(options);
    return { content: result.content, usage: result.usage };
  }
}
// OpenAI Provider
export class OpenAIProvider implements LLMProvider {
  constructor(private apiKey: string, private defaultModel: string = 'gpt-4-turbo') {}
  async chat(options: ChatOptions): Promise<{ content: string; usage?: { tokens: number } }> {
    const messages = [];
    if (options.system) {
      messages.push({ role: 'system', content: options.system });
    }
    messages.push(...options.messages.map((m) => ({ role: m.role, content: m.content })));
    const response = await fetch('https://api.openai.com/v1/chat/completions', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${this.apiKey}`,
      },
      body: JSON.stringify({
        model: options.model || this.defaultModel,
        messages,
        temperature: options.temperature || 0.3,
        max_tokens: options.maxTokens || 2000,
        tools: options.tools,
      }),
    });
    const data = await response.json();
    const message = data.choices?.[0]?.message;
    return {
      content: message?.content || '',
      usage: data.usage ? { tokens: data.usage.total_tokens } : undefined,
    };
  }
  async chatWithTools(options: ChatOptions): Promise<{
    content: string;
    toolCalls?: any[];
    usage?: { tokens: number };
  }> {
    const messages = [];
    if (options.system) {
      messages.push({ role: 'system', content: options.system });
    }
    messages.push(...options.messages.map((m) => ({ role: m.role, content: m.content })));
    const response = await fetch('https://api.openai.com/v1/chat/completions', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${this.apiKey}`,
      },
      body: JSON.stringify({
        model: options.model || this.defaultModel,
        messages,
        temperature: options.temperature || 0.3,
        max_tokens: options.maxTokens || 2000,
        tools: options.tools,
        tool_choice: options.tools ? 'auto' : undefined,
      }),
    });
    const data = await response.json();
    const message = data.choices?.[0]?.message;
    return {
      content: message?.content || '',
      toolCalls: message?.tool_calls,
      usage: data.usage ? { tokens: data.usage.total_tokens } : undefined,
    };
  }
}
