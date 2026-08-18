import express from 'express';
import { ExecutionService } from '../services/ExecutionService';
import { MetricsController } from '../controllers/MetricsController';
import { getGlobalMetrics } from '@network-agents/observability';
export function createMetricsRoutes(executionService: ExecutionService) {
  const router = express.Router();
  const controller = new MetricsController(executionService);
  const metrics = getGlobalMetrics();
  router.get('/prometheus', (req, res) => {
    const allMetrics = metrics.getMetrics();
    let output = '';
    for (const m of allMetrics) {
      const labels = m.labels
        ? `{${Object.entries(m.labels).map(([k, v]) => `${k}="${v}"`).join(',')}}`
        : '';
      output += `# HELP ${m.name} ${m.description || ''}\n`;
      output += `# TYPE ${m.name} ${m.type}\n`;
      output += `${m.name}${labels} ${m.value}\n`;
    }
    res.set('Content-Type', 'text/plain');
    res.send(output);
  });
  router.get('/', (req, res) => controller.getMetrics(req, res));
  router.get('/agents', (req, res) => controller.getAgentMetrics(req, res));
  router.get('/hitl', (req, res) => controller.getHitlMetrics(req, res));
  router.get('/costs', (req, res) => controller.getCostMetrics(req, res));
  router.get('/performance', (req, res) => controller.getPerformanceMetrics(req, res));
  return router;
}
