import express from 'express';
import { HitlManager } from '@network-agents/core';
import { HitlController } from '../controllers/HitlController';
export function createHitlRoutes(hitlManager: HitlManager) {
  const router = express.Router();
  const controller = new HitlController(hitlManager);
  router.get('/pending', (req, res) => controller.listPending(req, res));
  router.get('/:id', (req, res) => controller.getRequest(req, res));
  router.get('/:id/checkpoint', (req, res) => controller.getCheckpoint(req, res));
  router.post('/:id/approve', (req, res) => controller.approveRequest(req, res));
  router.post('/:id/reject', (req, res) => controller.rejectRequest(req, res));
  router.get('/stats', (req, res) => controller.getStats(req, res));
  return router;
}
