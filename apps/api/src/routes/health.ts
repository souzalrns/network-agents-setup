import express from 'express';
import { getGlobalMetrics } from '@network-agents/observability';
export function createHealthRoutes() {
  const router = express.Router();
  router.get('/', (_req, res) => {
    res.json({
      status: 'healthy',
      timestamp: new Date().toISOString(),
      version: '1.0.0',
    });
  });
  router.get('/ready', (_req, res) => {
    res.json({ status: 'ready' });
  });
  router.get('/metrics', (_req, res) => {
    const metrics = getGlobalMetrics().getMetrics();
    res.json(metrics);
  });
  return router;
}
