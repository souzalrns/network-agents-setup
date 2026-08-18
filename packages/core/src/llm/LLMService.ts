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

  // NOTA DE FIDELIDADE: adicionado durante a tarefa de "Ingestão Inicial" (Direito BR/PT),
  // depois que um smoke-test real (rodando scripts/validate/test-agents.ts sem
  // OPENAI_API_KEY configurada) mostrou que um erro de rede/autenticação virava
  // `SyntaxError: Unexpected token 'H', "Host not i"... is not valid JSON` — porque o
  // código chamava `response.json()` sem checar `response.ok`/content-type antes. Isso é
  // um bug pré-existente do scaffolding base (não fazia parte do material da Ingestão
  // Inicial), mas foi corrigido aqui porque impedia diagnosticar problemas reais de
  // configuração da API key.
  private assertApiKey(): void {
    if (!this.apiKey || this.apiKey === 'your-openai-api-key-here') {
      throw new Error(
        'OPENAI_API_KEY não configurada ou inválida. Configure a variável de ambiente OPENAI_API_KEY com uma chave válida da OpenAI.'
      );
    }
  }

  private async parseResponse(response: Response): Promise<any> {
    if (!response.ok) {
      let detail = response.statusText;
      try {
        const errorBody: any = await response.json();
        detail = errorBody?.error?.message || detail;
      } catch {
        // corpo não era JSON (ex.: bloqueio de rede/proxy) — mantém statusText
      }
      // Mensagens específicas para os códigos de erro mais comuns da OpenAI.
      if (response.status === 401) {
        throw new Error(`Chave de API inválida (401). Verifique sua OPENAI_API_KEY. Detalhe: ${detail}`);
      }
      if (response.status === 429) {
        throw new Error(`Limite de requisições/cota da OpenAI excedido (429). Aguarde e tente novamente. Detalhe: ${detail}`);
      }
      if (response.status >= 500) {
        throw new Error(`Erro interno da OpenAI (${response.status}). Tente novamente mais tarde. Detalhe: ${detail}`);
      }
      throw new Error(`OpenAI API error (${response.status}): ${detail}`);
    }
    try {
      return await response.json();
    } catch {
      throw new Error(
        'Resposta da OpenAI não é um JSON válido — verifique conectividade de rede com api.openai.com (pode ser um bloqueio de proxy/firewall retornando uma página de erro em HTML).'
      );
    }
  }

  async chat(options: ChatOptions): Promise<{ content: string; usage?: { tokens: number } }> {
    this.assertApiKey();
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
    const data: any = await this.parseResponse(response);
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
    this.assertApiKey();
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
    const data: any = await this.parseResponse(response);
    const message = data.choices?.[0]?.message;
    return {
      content: message?.content || '',
      toolCalls: message?.tool_calls,
      usage: data.usage ? { tokens: data.usage.total_tokens } : undefined,
    };
  }
}
