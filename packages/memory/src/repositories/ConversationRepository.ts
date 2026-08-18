import { PrismaClient } from '@prisma/client';
export class ConversationRepository {
  constructor(private prisma: PrismaClient) {}
  async create(userId: string, title?: string): Promise<any> {
    return this.prisma.conversation.create({
      data: { userId, title },
    });
  }
  async findById(id: string): Promise<any> {
    return this.prisma.conversation.findUnique({
      where: { id },
      include: { messages: true, executions: true },
    });
  }
  async findByUser(userId: string): Promise<any[]> {
    return this.prisma.conversation.findMany({
      where: { userId },
      orderBy: { lastMessageAt: 'desc' },
    });
  }
  async findRecent(userId: string, ms: number): Promise<any[]> {
    const cutoff = new Date(Date.now() - ms);
    return this.prisma.conversation.findMany({
      where: { userId, lastMessageAt: { gte: cutoff } },
      orderBy: { lastMessageAt: 'desc' },
      take: 1,
    });
  }
  async update(id: string, data: any): Promise<any> {
    return this.prisma.conversation.update({
      where: { id },
      data,
    });
  }
  async delete(id: string): Promise<any> {
    return this.prisma.conversation.delete({ where: { id } });
  }
}
