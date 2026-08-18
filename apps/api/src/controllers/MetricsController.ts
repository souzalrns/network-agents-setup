import { Request, Response } from 'express';
import { ExecutionService } from '../services/ExecutionService';
export class MetricsController {
  constructor(private executionService: ExecutionService) {}
  async getMetrics(req: Request, res: Response): Promise<void> {
    const { domain, agentId, startDate, endDate } = req.query;
    const metrics = await this.executionService.getDetailedMetrics({
      domain: domain as string,
      agentId: agentId as string,
      startDate: startDate ? new Date(startDate as string) : undefined,
      endDate: endDate ? new Date(endDate as string) : undefined,
    });
    res.json(metrics);
  }
  async getAgentMetrics(_req: Request, res: Response): Promise<void> {
    const stats = await this.executionService.getAgentStats();
    res.json(stats);
  }
  async getHitlMetrics(_req: Request, res: Response): Promise<void> {
    const stats = await this.executionService.getHitlStats();
    res.json(stats);
  }
  async getCostMetrics(req: Request, res: Response): Promise<void> {
    const { startDate, endDate } = req.query;
    const costs = await this.executionService.getCostMetrics({
      startDate: startDate ? new Date(startDate as string) : undefined,
      endDate: endDate ? new Date(endDate as string) : undefined,
    });
    res.json(costs);
  }
  async getPerformanceMetrics(req: Request, res: Response): Promise<void> {
    const { window = '1h' } = req.query;
    const performance = await this.executionService.getPerformanceMetrics(window as string);
    res.json(performance);
  }
}
