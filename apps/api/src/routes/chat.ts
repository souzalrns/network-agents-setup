import express from 'express';
import { Orchestrator } from '@network-agents/core';
import { ExecutionService } from '../services/ExecutionService';
import { ChatController } from '../controllers/ChatController';
export function createChatRoutes(
  orchestrator: Orchestrator,
  executionService: ExecutionService
) {
  const router = express.Router();
  const controller = new ChatController(orchestrator, executionService);
  router.post('/', (req, res) => controller.processChat(req, res));
  router.post('/stream', (req, res) => controller.processChat(req, res));
  return router;
}
