import { MemoryManager } from '@network-agents/memory';
export class ExecutionService {
  constructor(private memory: MemoryManager) {}
  async getExecution(id: string): Promise<any> {
    return this.memory.executions.findById(id);
  }
  async listExecutions(params: {
    domain?: string;
    status?: string;
    limit: number;
    offset: number;
  }): Promise<any[]> {
    const filters: any = {};
    if (params.domain) filters.domain = params.domain;
    if (params.status) filters.status = params.status;
    return this.memory.executions.list(params.limit, params.offset, filters);
  }
  async cancelExecution(id: string): Promise<boolean> {
    const execution = await this.memory.executions.findById(id);
    if (!execution || execution.status === 'completed' || execution.status === 'failed') {
      return false;
    }
    await this.memory.executions.update(id, { status: 'cancelled' });
    return true;
  }
  async getDetailedMetrics(params: {
    domain?: string;
    agentId?: string;
    startDate?: Date;
    endDate?: Date;
  }): Promise<any> {
    const executions = await this.memory.executions.list(1000, 0, {
      domain: params.domain,
      ...(params.startDate && { startedAt: { gte: params.startDate } }),
      ...(params.endDate && { startedAt: { lte: params.endDate } }),
    });
    const total = executions.length;
    const successful = executions.filter((e: any) => e.status === 'completed').length;
    const failed = executions.filter((e: any) => e.status === 'failed' || e.status === 'cancelled').length;
    const totalTokens = executions.reduce((sum: number, e: any) => sum + (e.totalTokens || 0), 0);
    const totalCost = executions.reduce((sum: number, e: any) => sum + (e.totalCost || 0), 0);
    const totalDuration = executions.reduce((sum: number, e: any) => sum + (e.durationMs || 0), 0);
    const byAgent: Record<string, any> = {};
    for (const exec of executions) {
      const agentId = exec.metadata?.agentId || 'unknown';
      if (!byAgent[agentId]) byAgent[agentId] = { total: 0, tokens: 0, cost: 0, duration: 0 };
      byAgent[agentId].total++;
      byAgent[agentId].tokens += exec.totalTokens || 0;
      byAgent[agentId].cost += exec.totalCost || 0;
      byAgent[agentId].duration += exec.durationMs || 0;
    }
    const byDomain: Record<string, any> = {};
    for (const exec of executions) {
      const domain = exec.domain || 'unknown';
      if (!byDomain[domain]) byDomain[domain] = { total: 0, tokens: 0, cost: 0, duration: 0 };
      byDomain[domain].total++;
      byDomain[domain].tokens += exec.totalTokens || 0;
      byDomain[domain].cost += exec.totalCost || 0;
      byDomain[domain].duration += exec.durationMs || 0;
    }
    const byStatus: Record<string, number> = {};
    for (const exec of executions) {
      byStatus[exec.status] = (byStatus[exec.status] || 0) + 1;
    }
    return {
      total,
      successful,
      failed,
      successRate: total > 0 ? (successful / total * 100).toFixed(2) + '%' : '0%',
      totalTokens,
      totalCost,
      averageDurationMs: total > 0 ? totalDuration / total : 0,
      byAgent,
      byDomain,
      byStatus,
    };
  }
  async getAgentStats(): Promise<any> {
    const executions = await this.memory.executions.list(1000, 0);
    const stats: Record<string, any> = {};
    for (const exec of executions) {
      const steps = exec.steps || [];
      for (const step of steps) {
        const agentId = step.agentId || 'unknown';
        if (!stats[agentId]) {
          stats[agentId] = { calls: 0, errors: 0, tokens: 0, duration: 0 };
        }
        stats[agentId].calls++;
        if (!step.success) stats[agentId].errors++;
        stats[agentId].tokens += step.tokens || 0;
        stats[agentId].duration += step.durationMs || 0;
      }
    }
    return stats;
  }
  async getHitlStats(): Promise<any> {
    // Será implementado com a tabela de HITL requests
    return { pending: 0, approved: 0, rejected: 0, expired: 0 };
  }
  async getCostMetrics(params: { startDate?: Date; endDate?: Date }): Promise<any> {
    const executions = await this.memory.executions.list(1000, 0, {
      ...(params.startDate && { startedAt: { gte: params.startDate } }),
      ...(params.endDate && { startedAt: { lte: params.endDate } }),
    });
    const totalCost = executions.reduce((sum: number, e: any) => sum + (e.totalCost || 0), 0);
    const totalTokens = executions.reduce((sum: number, e: any) => sum + (e.totalTokens || 0), 0);
    return { totalCost, totalTokens, executions: executions.length };
  }
  async getPerformanceMetrics(_window: string): Promise<any> {
    // Implementação simplificada
    const executions = await this.memory.executions.list(1000, 0);
    const durations = executions.map((e: any) => e.durationMs || 0).filter((d: number) => d > 0);
    if (durations.length === 0) {
      return { avg: 0, p50: 0, p95: 0, p99: 0 };
    }
    durations.sort((a, b) => a - b);
    const avg = durations.reduce((s, d) => s + d, 0) / durations.length;
    const p50 = durations[Math.floor(durations.length * 0.5)];
    const p95 = durations[Math.floor(durations.length * 0.95)];
    const p99 = durations[Math.floor(durations.length * 0.99)];
    return { avg, p50, p95, p99, count: durations.length };
  }
  async getTotalCount(): Promise<number> {
    return this.memory.executions.count();
  }
}
