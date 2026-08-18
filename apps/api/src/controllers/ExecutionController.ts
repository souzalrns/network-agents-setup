import { Request, Response } from 'express';
import { ExecutionService } from '../services/ExecutionService';
export class ExecutionController {
  constructor(private executionService: ExecutionService) {}
  async getExecution(req: Request, res: Response): Promise<void> {
    const { id } = req.params;
    const execution = await this.executionService.getExecution(id);
    if (!execution) {
      res.status(404).json({ error: 'Execution not found' });
      return;
    }
    res.json(execution);
  }
  async listExecutions(req: Request, res: Response): Promise<void> {
    const { domain, status, limit = '50', offset = '0' } = req.query;
    const executions = await this.executionService.listExecutions({
      domain: domain as string,
      status: status as string,
      limit: parseInt(limit as string),
      offset: parseInt(offset as string),
    });
    res.json({
      data: executions,
      pagination: {
        limit: parseInt(limit as string),
        offset: parseInt(offset as string),
        total: executions.length,
      },
    });
  }
  async cancelExecution(req: Request, res: Response): Promise<void> {
    const { id } = req.params;
    const cancelled = await this.executionService.cancelExecution(id);
    if (!cancelled) {
      res.status(404).json({ error: 'Execution not found or already completed' });
      return;
    }
    res.json({ success: true, message: 'Execution cancelled' });
  }
}
