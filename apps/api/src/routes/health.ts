import express from 'express';
import { getGlobalMetrics } from '@network-agents/observability';
export function createHealthRoutes() {
  const router = express.Router();
  router.get('/', (req, res) => {
    res.json({
      status: 'healthy',
      timestamp: new Date().toISOString(),
      version: '1.0.0',
    });
  });
  router.get('/ready', (req, res) => {
    res.json({ status: 'ready' });
  });
  router.get('/metrics', (req, res) => {
    const metrics = getGlobalMetrics().getMetrics();
    res.json(metrics);
  });
  return router;
}
