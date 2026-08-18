import { PrismaClient } from '@prisma/client';
export class MetricsRepository {
  constructor(private prisma: PrismaClient) {}
  async record(data: {
    agentId?: string;
    executions?: number;
    tokens?: number;
    cost?: number;
    durationMs?: number;
    errors?: number;
  }): Promise<any> {
    return this.prisma.metrics.create({
      data: {
        agentId: data.agentId,
        executions: data.executions || 0,
        tokens: data.tokens || 0,
        cost: data.cost || 0,
        durationMs: data.durationMs || 0,
        errors: data.errors || 0,
      },
    });
  }
  async getByAgent(agentId: string, startDate?: Date, endDate?: Date): Promise<any[]> {
    const where: any = { agentId };
    if (startDate) where.date = { gte: startDate };
    if (endDate) where.date = { lte: endDate };
    return this.prisma.metrics.findMany({
      where,
      orderBy: { date: 'asc' },
    });
  }
  async getSummary(startDate?: Date, endDate?: Date): Promise<any> {
    const where: any = {};
    if (startDate) where.date = { gte: startDate };
    if (endDate) where.date = { lte: endDate };
    const metrics = await this.prisma.metrics.findMany({ where });
    const totalExecutions = metrics.reduce((sum, m) => sum + m.executions, 0);
    const totalTokens = metrics.reduce((sum, m) => sum + m.tokens, 0);
    const totalCost = metrics.reduce((sum, m) => sum + m.cost, 0);
    const totalDuration = metrics.reduce((sum, m) => sum + m.durationMs, 0);
    const totalErrors = metrics.reduce((sum, m) => sum + m.errors, 0);
    return { totalExecutions, totalTokens, totalCost, totalDuration, totalErrors, count: metrics.length };
  }
  async deleteOld(days: number): Promise<any> {
    const cutoff = new Date(Date.now() - days * 24 * 60 * 60 * 1000);
    return this.prisma.metrics.deleteMany({
      where: { date: { lt: cutoff } },
    });
  }
}
