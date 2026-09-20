import { Agent, AgentConfig } from '@network-agents/shared';
export class AgentFactory {
  private agents: Map<string, Agent> = new Map();
  constructor(private config: { publicMode: boolean }) {}
  registerAgent(config: AgentConfig): void {
    if (this.config.publicMode && config.visibility === 'private') {
      console.log(`[SKIP] Agent ${config.id} is private and PUBLIC_MODE is enabled.`);
      return;
    }
    const agent: Agent = {
      id: config.id,
      name: config.id,
      layer: config.layer,
      visibility: config.visibility,
      domain: config.domain,
      description: config.description,
      capabilities: [],
      systemPrompt: config.systemPrompt,
      tools: config.tools || [],
      profile: config.profile,
    };
    this.agents.set(config.id, agent);
    console.log(`[REGISTER] Agent ${config.id} loaded (layer: ${config.layer})`);
  }
  getAgent(id: string): Agent | undefined {
    return this.agents.get(id);
  }
  getAllAgents(): Agent[] {
    return Array.from(this.agents.values());
  }
  getAgentsByDomain(domain: string): Agent[] {
    return this.getAllAgents().filter((a) => a.domain === domain);
  }
  getAgentsByLayer(layer: Agent['layer']): Agent[] {
    return this.getAllAgents().filter((a) => a.layer === layer);
  }
  getAgentsByVisibility(visibility: Agent['visibility']): Agent[] {
    return this.getAllAgents().filter((a) => a.visibility === visibility);
  }
}

/**
 * F1: resolve o `systemPrompt` (ou `description`, na falta dele) de um agente
 * substituindo placeholders `{{chave}}` pelos valores do `profile`. Permite
 * que o mesmo agente registado produza saídas diferenciadas por perfil
 * (jurisdição, framework, especialidade...) sem precisar de uma entrada
 * separada em `AGENT_CONFIGS` por variante.
 */
export function resolveAgentPrompt(agent: Agent, profile?: Record<string, unknown>): string {
  const template = agent.systemPrompt ?? agent.description;
  const effectiveProfile = profile ?? agent.profile;
  if (!effectiveProfile) return template;
  return Object.entries(effectiveProfile).reduce(
    (text, [key, value]) => text.split(`{{${key}}}`).join(String(value)),
    template
  );
}
