import { Request, Response } from 'express';
import { AgentFactory } from '@network-agents/core';
export class AgentController {
  constructor(private agentFactory: AgentFactory) {}
  async listAgents(req: Request, res: Response): Promise<void> {
    const { layer, domain, visibility } = req.query;
    let agents = this.agentFactory.getAllAgents();
    if (layer) {
      agents = agents.filter((a) => a.layer === layer);
    }
    if (domain) {
      agents = agents.filter((a) => a.domain === domain);
    }
    if (visibility) {
      agents = agents.filter((a) => a.visibility === visibility);
    }
    res.json(
      agents.map((a) => ({
        id: a.id,
        name: a.name,
        layer: a.layer,
        visibility: a.visibility,
        domain: a.domain,
        description: a.description,
        capabilities: a.capabilities || [],
        tools: a.tools || [],
      }))
    );
  }
  async getAgent(req: Request, res: Response): Promise<void> {
    const { id } = req.params;
    const agent = this.agentFactory.getAgent(id);
    if (!agent) {
      res.status(404).json({ error: `Agent ${id} not found` });
      return;
    }
    res.json({
      id: agent.id,
      name: agent.name,
      layer: agent.layer,
      visibility: agent.visibility,
      domain: agent.domain,
      description: agent.description,
      capabilities: agent.capabilities || [],
      tools: agent.tools || [],
    });
  }
  async getAgentsByDomain(req: Request, res: Response): Promise<void> {
    const { domain } = req.params;
    const agents = this.agentFactory.getAgentsByDomain(domain);
    res.json(
      agents.map((a) => ({
        id: a.id,
        name: a.name,
        layer: a.layer,
        visibility: a.visibility,
        domain: a.domain,
        description: a.description,
        capabilities: a.capabilities || [],
        tools: a.tools || [],
      }))
    );
  }
}
