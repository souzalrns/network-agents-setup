export interface Agent {
  id: string;
  name: string;
  layer: 'meta' | 'horizontal' | 'vertical' | 'personal';
  visibility: 'public' | 'private';
  domain?: string;
  description: string;
  capabilities: string[];
  systemPrompt?: string;
  tools?: string[];
  dependencies?: string[];
  /** F1: variação configurável (jurisdição, framework, especialidade...) sem multiplicar agentes. */
  profile?: Record<string, unknown>;
}
export interface AgentConfig {
  id: string;
  layer: Agent['layer'];
  visibility: Agent['visibility'];
  domain?: string;
  description: string;
  systemPrompt?: string;
  tools?: string[];
  profile?: Record<string, unknown>;
}
export interface AgentResponse {
  agentId: string;
  content: string;
  confidence?: number;
  metadata?: Record<string, any>;
  timestamp: Date;
}
