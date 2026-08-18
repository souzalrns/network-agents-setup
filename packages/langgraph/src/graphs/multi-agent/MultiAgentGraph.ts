import { StateGraph } from '../base/StateGraph';
import { GraphState } from '../../state/StateManager';
import { AgentFactory } from '@network-agents/core';
import { LLMService } from '@network-agents/core';
export class MultiAgentGraph extends StateGraph {
  constructor(
    private agentFactory: AgentFactory,
    private llm: LLMService
  ) {
    super();
    this.addNode('orchestrate', this.orchestrate.bind(this));
    this.addNode('delegate', this.delegate.bind(this));
    this.addNode('collaborate', this.collaborate.bind(this));
    this.addNode('synthesize', this.synthesize.bind(this));
    this.addEdge('orchestrate', this.orchestrateEdge.bind(this));
    this.addEdge('delegate', this.delegateEdge.bind(this));
    this.addEdge('collaborate', this.collaborateEdge.bind(this));
    this.setEntryPoint('orchestrate');
  }
  private async orchestrate(state: GraphState): Promise<Partial<GraphState>> {
    const domainAgents = this.agentFactory.getAgentsByDomain(state.domain || 'general');
    const selectedAgents = await this.selectAgents(state.input, domainAgents);
    return {
      context: { ...state.context, selectedAgents },
      metadata: { ...state.metadata, totalAgents: selectedAgents.length },
    };
  }
  private async delegate(state: GraphState): Promise<Partial<GraphState>> {
    const agents = state.context.selectedAgents || [];
    const tasks: Array<{ agent: any; prompt: string }> = [];
    for (const agent of agents) {
      const prompt = await this.generatePromptForAgent(state.input, agent);
      tasks.push({ agent, prompt });
    }
    return { context: { ...state.context, tasks } };
  }
  private async collaborate(state: GraphState): Promise<Partial<GraphState>> {
    const tasks = state.context.tasks || [];
    const results: Map<string, any> = new Map();
    const promises = tasks.map(async ({ agent, prompt }) => {
      const result = await this.executeAgent(agent.id, prompt);
      results.set(agent.id, result);
      return result;
    });
    await Promise.all(promises);
    return { results, status: 'executing' };
  }
  private async synthesize(state: GraphState): Promise<Partial<GraphState>> {
    const results = state.results;
    const synthesis = await this.synthesizeResults(results);
    return {
      results: new Map([...results, ['synthesis', synthesis]]),
      status: 'completed',
      metadata: { ...state.metadata, synthesis },
    };
  }
  private async orchestrateEdge(state: GraphState): Promise<string> {
    return 'delegate';
  }
  private async delegateEdge(state: GraphState): Promise<string> {
    return 'collaborate';
  }
  private async collaborateEdge(state: GraphState): Promise<string> {
    return 'synthesize';
  }
  private async selectAgents(input: string, agents: any[]): Promise<any[]> {
    const prompt = `
      Selecione os agentes mais adequados para a seguinte tarefa:
      Tarefa: ${input}
      Agentes disponíveis: ${agents.map((a) => `- ${a.id}: ${a.description}`).join('\n')}
      Retorne uma lista de IDs dos agentes selecionados (máximo 5).
    `;
    const response = await this.llm.chat({
      system: 'Você é um orquestrador de agentes.',
      messages: [{ role: 'user', content: prompt }],
      temperature: 0.1,
    });
    try {
      const ids = JSON.parse(response.content);
      return agents.filter((a) => ids.includes(a.id));
    } catch {
      return agents.slice(0, 3);
    }
  }
  private async generatePromptForAgent(input: string, agent: any): Promise<string> {
    return `Tarefa para ${agent.id} (${agent.description}):
      Input: ${input}
      Execute esta tarefa considerando sua especialidade.
      Forneça uma resposta detalhada e fundamentada.`;
  }
  private async executeAgent(agentId: string, prompt: string): Promise<any> {
    const agent = this.agentFactory.getAgent(agentId);
    if (!agent) {
      throw new Error(`Agent ${agentId} not found`);
    }
    const response = await this.llm.chat({
      system: agent.systemPrompt || `Você é ${agent.id}, ${agent.description}`,
      messages: [{ role: 'user', content: prompt }],
      temperature: 0.3,
    });
    return response.content;
  }
  private async synthesizeResults(results: Map<string, any>): Promise<string> {
    const entries = Array.from(results.entries())
      .map(([id, result]) => `[${id}]: ${result}`)
      .join('\n\n');
    const response = await this.llm.chat({
      system: 'Você é um sintetizador de conhecimento. Combine os seguintes resultados em uma resposta coerente e completa.',
      messages: [{ role: 'user', content: entries }],
      temperature: 0.2,
    });
    return response.content;
  }
}
