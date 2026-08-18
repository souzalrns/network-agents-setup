import { PrismaClient } from '@prisma/client';
import { ExecutionRepository } from './repositories/ExecutionRepository';
import { ConversationRepository } from './repositories/ConversationRepository';
import { UserRepository } from './repositories/UserRepository';
import { CheckpointRepository } from './repositories/CheckpointRepository';
import { MetricsRepository } from './repositories/MetricsRepository';
import { RedisCache } from './cache/RedisCache';
export interface MemoryConfig {
  redisUrl?: string;
  cacheTTL?: number;
}
export class MemoryManager {
  private prisma: PrismaClient;
  private cache?: RedisCache;
  public executions: ExecutionRepository;
  public conversations: ConversationRepository;
  public users: UserRepository;
  public checkpoints: CheckpointRepository;
  public metrics: MetricsRepository;
  constructor(config: MemoryConfig = {}) {
    this.prisma = new PrismaClient();
    if (config.redisUrl) {
      this.cache = new RedisCache(config.redisUrl, config.cacheTTL || 3600);
    }
    this.executions = new ExecutionRepository(this.prisma);
    this.conversations = new ConversationRepository(this.prisma);
    this.users = new UserRepository(this.prisma);
    this.checkpoints = new CheckpointRepository(this.prisma);
    this.metrics = new MetricsRepository(this.prisma);
  }
  async getOrCreateUser(email: string, name?: string): Promise<any> {
    let user = await this.users.findByEmail(email);
    if (!user) {
      user = await this.users.create({ email, name });
    }
    return user;
  }
  async getOrCreateConversation(userId: string, title?: string): Promise<any> {
    const recent = await this.conversations.findRecent(userId, 3600000);
    if (recent.length > 0) {
      return recent[0];
    }
    return this.conversations.create(userId, title || 'Nova conversa');
  }
  async saveExecutionState(executionId: string, state: any): Promise<void> {
    await this.executions.update(executionId, state);
    if (this.cache) {
      await this.cache.set(`execution:${executionId}`, state, 300);
    }
  }
  async getExecutionState(executionId: string): Promise<any> {
    if (this.cache) {
      const cached = await this.cache.get(`execution:${executionId}`);
      if (cached) return cached;
    }
    const execution = await this.executions.findById(executionId);
    if (execution && this.cache) {
      await this.cache.set(`execution:${executionId}`, execution, 300);
    }
    return execution;
  }
  async addMessage(conversationId: string, role: string, content: string, metadata?: any): Promise<void> {
    await this.prisma.message.create({
      data: {
        conversationId,
        role,
        content,
        metadata,
        createdAt: new Date(),
      },
    });
    await this.prisma.conversation.update({
      where: { id: conversationId },
      data: {
        lastMessageAt: new Date(),
        messageCount: { increment: 1 },
      },
    });
  }
  async getConversationHistory(conversationId: string, limit: number = 50): Promise<any[]> {
    return this.prisma.message.findMany({
      where: { conversationId },
      orderBy: { createdAt: 'asc' },
      take: limit,
    });
  }
  snapshot(): Record<string, any> {
    return {
      timestamp: new Date().toISOString(),
      cache: this.cache ? 'available' : 'disabled',
    };
  }
  async disconnect(): Promise<void> {
    await this.prisma.$disconnect();
    if (this.cache) {
      await this.cache.disconnect();
    }
  }
}
