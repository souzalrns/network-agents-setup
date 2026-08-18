import express from 'express';
import { AgentFactory } from '@network-agents/core';
import { AgentController } from '../controllers/AgentController';
export function createAgentRoutes(agentFactory: AgentFactory) {
  const router = express.Router();
  const controller = new AgentController(agentFactory);
  router.get('/', (req, res) => controller.listAgents(req, res));
  router.get('/:id', (req, res) => controller.getAgent(req, res));
  router.get('/domain/:domain', (req, res) => controller.getAgentsByDomain(req, res));
  return router;
}
