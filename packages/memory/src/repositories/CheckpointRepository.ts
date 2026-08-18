import { PrismaClient } from '@prisma/client';
export class CheckpointRepository {
  constructor(private prisma: PrismaClient) {}
  async create(data: {
    executionId: string;
    hitlRequestId: string;
    stepIndex: number;
    state: any;
    memorySnapshot: any;
  }): Promise<any> {
    return this.prisma.checkpoint.create({ data });
  }
  async findByExecution(executionId: string): Promise<any[]> {
    return this.prisma.checkpoint.findMany({
      where: { executionId },
      orderBy: { createdAt: 'desc' },
    });
  }
  async findByHitlRequest(hitlRequestId: string): Promise<any> {
    return this.prisma.checkpoint.findFirst({
      where: { hitlRequestId },
    });
  }
  async deleteByHitlRequest(hitlRequestId: string): Promise<any> {
    return this.prisma.checkpoint.deleteMany({
      where: { hitlRequestId },
    });
  }
  async deleteByExecution(executionId: string): Promise<any> {
    return this.prisma.checkpoint.deleteMany({
      where: { executionId },
    });
  }
}
