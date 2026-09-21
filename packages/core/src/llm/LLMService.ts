import { getGlobalTracer } from '@network-agents/observability';

export interface ChatMessage {
  role: 'system' | 'user' | 'assistant' | 'tool';
  content: string;
  tool_call_id?: string;
  // S33: tool_calls do assistant que motivaram uma resposta role:'tool' --
  // a API da OpenAI exige a mensagem assistant original (com estes IDs) de
  // volta na conversa antes de aceitar as respostas 'tool' correspondentes.
  toolCalls?: any[];
}
export interface ChatOptions {
  system?: string;
  messages: ChatMessage[];
  temperature?: number;
  maxTokens?: number;
  model?: string;
  tools?: any[];
}
export interface TokenUsage {
  tokens: number;
  promptTokens?: number;
  completionTokens?: number;
}
export interface LLMProvider {
  chat(options: ChatOptions): Promise<{ content: string; usage?: TokenUsage }>;
  chatWithTools?(options: ChatOptions): Promise<{
    content: string;
    toolCalls?: any[];
    usage?: TokenUsage;
  }>;
}

/** D2: gen_ai.client — únicos atributos estáveis da convenção OTel GenAI (o resto continua em Development). */
/** S33: mapeia ChatMessage -> formato de mensagem da API da OpenAI,
 * preservando `tool_call_id` (mensagens role:'tool') e `tool_calls`
 * (mensagens role:'assistant' que pediram uma tool) -- antes descartados,
 * o que faria a API da OpenAI rejeitar (400) qualquer roda de tool-calling
 * real (nunca exercitado em produção, ver S33/STATUS.md). */
function toOpenAiMessage(m: ChatMessage): Record<string, any> {
  const msg: Record<string, any> = { role: m.role, content: m.content };
  if (m.tool_call_id) msg.tool_call_id = m.tool_call_id;
  if (m.toolCalls) msg.tool_calls = m.toolCalls;
  return msg;
}

function setGenAiAttributes(
  spanId: string,
  model: string | undefined,
  usage: TokenUsage | undefined
): void {
  const tracer = getGlobalTracer();
  if (model) tracer.setAttribute(spanId, 'gen_ai.request.model', model);
  if (usage?.promptTokens !== undefined) {
    tracer.setAttribute(spanId, 'gen_ai.usage.input_tokens', usage.promptTokens);
  }
  if (usage?.completionTokens !== undefined) {
    tracer.setAttribute(spanId, 'gen_ai.usage.output_tokens', usage.completionTokens);
  }
}

export class LLMService {
  constructor(private provider: LLMProvider) {}
  async chat(options: ChatOptions): Promise<{ content: string; usage?: TokenUsage }> {
    const tracer = getGlobalTracer();
    const spanId = tracer.startSpan('gen_ai.client.chat');
    try {
      const result = await this.provider.chat(options);
      setGenAiAttributes(spanId, options.model, result.usage);
      tracer.endSpan(spanId, 'ok');
      return result;
    } catch (error) {
      tracer.endSpan(spanId, 'error', error as Error);
      throw error;
    }
  }
  async chatWithTools(options: ChatOptions): Promise<{
    content: string;
    toolCalls?: any[];
    usage?: TokenUsage;
  }> {
    const tracer = getGlobalTracer();
    const spanId = tracer.startSpan('gen_ai.client.chat_with_tools');
    try {
      const result = this.provider.chatWithTools
        ? await this.provider.chatWithTools(options)
        : await this.provider.chat(options).then((r) => ({ content: r.content, usage: r.usage }));
      setGenAiAttributes(spanId, options.model, result.usage);
      tracer.endSpan(spanId, 'ok');
      return result;
    } catch (error) {
      tracer.endSpan(spanId, 'error', error as Error);
      throw error;
    }
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

  async chat(options: ChatOptions): Promise<{ content: string; usage?: TokenUsage }> {
    this.assertApiKey();
    const messages = [];
    if (options.system) {
      messages.push({ role: 'system', content: options.system });
    }
    messages.push(...options.messages.map(toOpenAiMessage));
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
      usage: data.usage
        ? {
            tokens: data.usage.total_tokens,
            promptTokens: data.usage.prompt_tokens,
            completionTokens: data.usage.completion_tokens,
          }
        : undefined,
    };
  }
  async chatWithTools(options: ChatOptions): Promise<{
    content: string;
    toolCalls?: any[];
    usage?: TokenUsage;
  }> {
    this.assertApiKey();
    const messages = [];
    if (options.system) {
      messages.push({ role: 'system', content: options.system });
    }
    messages.push(...options.messages.map(toOpenAiMessage));
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
      usage: data.usage
        ? {
            tokens: data.usage.total_tokens,
            promptTokens: data.usage.prompt_tokens,
            completionTokens: data.usage.completion_tokens,
          }
        : undefined,
    };
  }
}
