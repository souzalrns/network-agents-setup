import { Request, Response } from 'express';
import { HitlManager } from '@network-agents/core';
export class HitlController {
  constructor(private hitlManager: HitlManager) {}
  async listPending(req: Request, res: Response): Promise<void> {
    const { domain } = req.query;
    const requests = this.hitlManager.getPendingRequests(domain as string);
    res.json(requests);
  }
  async getRequest(req: Request, res: Response): Promise<void> {
    const { id } = req.params;
    const request = this.hitlManager.getRequest(id);
    if (!request) {
      res.status(404).json({ error: 'Request not found' });
      return;
    }
    res.json(request);
  }
  async approveRequest(req: Request, res: Response): Promise<void> {
    const { id } = req.params;
    const { comment, responderId } = req.body;
    if (!responderId) {
      res.status(400).json({ error: 'responderId is required' });
      return;
    }
    try {
      const request = await this.hitlManager.approveRequest(id, responderId, comment);
      res.json(request);
    } catch (error: any) {
      res.status(400).json({ error: error.message });
    }
  }
  async rejectRequest(req: Request, res: Response): Promise<void> {
    const { id } = req.params;
    const { comment, responderId } = req.body;
    if (!responderId) {
      res.status(400).json({ error: 'responderId is required' });
      return;
    }
    try {
      const request = await this.hitlManager.rejectRequest(id, responderId, comment);
      res.json(request);
    } catch (error: any) {
      res.status(400).json({ error: error.message });
    }
  }
  async getCheckpoint(req: Request, res: Response): Promise<void> {
    const { id } = req.params;
    const checkpoint = this.hitlManager.getCheckpoint(id);
    if (!checkpoint) {
      res.status(404).json({ error: 'Checkpoint not found' });
      return;
    }
    res.json(checkpoint);
  }
  async getStats(_req: Request, res: Response): Promise<void> {
    const pending = this.hitlManager.getPendingRequests();
    res.json({
      totalPending: pending.length,
      byPriority: {
        critical: pending.filter((r) => r.priority === 'critical').length,
        high: pending.filter((r) => r.priority === 'high').length,
        medium: pending.filter((r) => r.priority === 'medium').length,
        low: pending.filter((r) => r.priority === 'low').length,
      },
      byCategory: {
        financial: pending.filter((r) => r.category === 'financial').length,
        legal: pending.filter((r) => r.category === 'legal').length,
        medical: pending.filter((r) => r.category === 'medical').length,
        strategic: pending.filter((r) => r.category === 'strategic').length,
        approval: pending.filter((r) => r.category === 'approval').length,
      },
    });
  }
}
