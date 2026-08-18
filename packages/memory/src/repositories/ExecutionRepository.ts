import { PrismaClient } from '@prisma/client';
export class ExecutionRepository {
  constructor(private prisma: PrismaClient) {}
  async create(data: any): Promise<any> {
    return this.prisma.execution.create({ data });
  }
  async update(id: string, data: any): Promise<any> {
    return this.prisma.execution.update({
      where: { id },
      data: { ...data, updatedAt: new Date() },
    });
  }
  async findById(id: string): Promise<any> {
    return this.prisma.execution.findUnique({
      where: { id },
      include: { user: true, conversation: true, checkpoints: true, logs: true },
    });
  }
  async findByUser(userId: string, limit: number = 50, offset: number = 0): Promise<any[]> {
    return this.prisma.execution.findMany({
      where: { userId },
      orderBy: { startedAt: 'desc' },
      skip: offset,
      take: limit,
    });
  }
  async list(limit: number = 50, offset: number = 0, filters?: any): Promise<any[]> {
    return this.prisma.execution.findMany({
      where: filters,
      orderBy: { startedAt: 'desc' },
      skip: offset,
      take: limit,
    });
  }
  async count(filters?: any): Promise<number> {
    return this.prisma.execution.count({ where: filters });
  }
  async getMetrics(agentId?: string, startDate?: Date, endDate?: Date): Promise<any> {
    const where: any = {};
    if (agentId) where.agentId = agentId;
    if (startDate) where.startedAt = { gte: startDate };
    if (endDate) where.startedAt = { lte: endDate };
    const executions = await this.prisma.execution.findMany({
      where,
      select: { status: true, totalTokens: true, totalCost: true, durationMs: true },
    });
    const total = executions.length;
    const successful = executions.filter((e: any) => e.status === 'completed').length;
    const failed = executions.filter((e: any) => e.status === 'failed' || e.status === 'cancelled').length;
    const totalTokens = executions.reduce((sum: number, e: any) => sum + (e.totalTokens || 0), 0);
    const totalCost = executions.reduce((sum: number, e: any) => sum + (e.totalCost || 0), 0);
    const totalDuration = executions.reduce((sum: number, e: any) => sum + (e.durationMs || 0), 0);
    return { total, successful, failed, totalTokens, totalCost, averageDurationMs: total > 0 ? totalDuration / total : 0 };
  }
}
