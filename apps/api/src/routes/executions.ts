import express from 'express';
import { ExecutionService } from '../services/ExecutionService';
import { ExecutionController } from '../controllers/ExecutionController';
export function createExecutionRoutes(executionService: ExecutionService) {
  const router = express.Router();
  const controller = new ExecutionController(executionService);
  router.get('/', (req, res) => controller.listExecutions(req, res));
  router.get('/:id', (req, res) => controller.getExecution(req, res));
  router.post('/:id/cancel', (req, res) => controller.cancelExecution(req, res));
  return router;
}
