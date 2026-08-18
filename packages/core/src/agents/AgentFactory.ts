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
