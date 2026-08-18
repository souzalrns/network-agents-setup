import { EventEmitter } from 'events';
import { getGlobalLogger } from '@network-agents/observability';
import { HitlManager } from '../hitl/HitlManager';

export interface AttentionBudget {
  userId: string;
  maxInterruptionsPerHour: number;
  currentInterruptions: number;
  lastReset: Date;
  priority: 'low' | 'medium' | 'high' | 'critical';
  cooldownUntil?: Date;
}

export interface AttentionRequest {
  id: string;
  userId: string;
  title: string;
  description: string;
  priority: 'low' | 'medium' | 'high' | 'critical';
  estimatedAttentionCost: number; // minutos
  requiresImmediate: boolean;
}

export class AttentionEconomy extends EventEmitter {
  private logger = getGlobalLogger();
  private budgets: Map<string, AttentionBudget> = new Map();
  private requests: Map<string, AttentionRequest> = new Map();

  constructor(
    _hitlManager: HitlManager,
    private config: {
      defaultMaxInterruptionsPerHour?: number;
      cooldownAfterInterruption?: number; // minutos
      minPriorityForImmediate?: 'low' | 'medium' | 'high' | 'critical';
    } = {}
  ) {
    super();
    this.config.defaultMaxInterruptionsPerHour = config.defaultMaxInterruptionsPerHour || 5;
    this.config.cooldownAfterInterruption = config.cooldownAfterInterruption || 10;
    this.config.minPriorityForImmediate = config.minPriorityForImmediate || 'high';
    this.logger.info('[AttentionEconomy] Initialized');
  }

  /**
   * Registra um usuário no sistema de atenção
   */
  registerUser(userId: string): AttentionBudget {
    const budget: AttentionBudget = {
      userId,
      maxInterruptionsPerHour: this.config.defaultMaxInterruptionsPerHour || 5,
      currentInterruptions: 0,
      lastReset: new Date(),
      priority: 'medium',
    };

    this.budgets.set(userId, budget);
    this.logger.info(`[AttentionEconomy] User registered: ${userId}`);
    return budget;
  }

  /**
   * Verifica se um usuário pode ser interrompido
   */
  canInterrupt(userId: string, priority: 'low' | 'medium' | 'high' | 'critical'): {
    allowed: boolean;
    reason: string;
    waitTime?: number;
  } {
    const budget = this.budgets.get(userId);
    if (!budget) {
      return { allowed: false, reason: 'User not registered' };
    }

    // Reseta contador se passou 1 hora
    const oneHourAgo = new Date(Date.now() - 60 * 60 * 1000);
    if (budget.lastReset < oneHourAgo) {
      budget.currentInterruptions = 0;
      budget.lastReset = new Date();
      this.budgets.set(userId, budget);
    }

    // Verifica cooldown
    if (budget.cooldownUntil && budget.cooldownUntil > new Date()) {
      const waitTime = Math.ceil((budget.cooldownUntil.getTime() - Date.now()) / 60000);
      return {
        allowed: false,
        reason: `Em cooldown por ${waitTime} minutos`,
        waitTime,
      };
    }

    // Verifica prioridade
    const priorityLevels = { low: 0, medium: 1, high: 2, critical: 3 };
    const requestPriority = priorityLevels[priority];

    // Se for crítico, sempre permite
    if (priority === 'critical') {
      return { allowed: true, reason: 'Prioridade crítica' };
    }

    // Se o usuário tem prioridade alta, permite mais interrupções
    const maxInterruptions = budget.priority === 'high'
      ? budget.maxInterruptionsPerHour + 2
      : budget.priority === 'critical'
      ? budget.maxInterruptionsPerHour + 5
      : budget.maxInterruptionsPerHour;

    // Verifica se atingiu o limite
    if (budget.currentInterruptions >= maxInterruptions) {
      const waitMinutes = 60 - Math.floor((Date.now() - budget.lastReset.getTime()) / 60000);
      return {
        allowed: false,
        reason: `Limite de interrupções atingido (${budget.currentInterruptions}/${maxInterruptions})`,
        waitTime: waitMinutes,
      };
    }

    // Verifica se a prioridade é alta o suficiente
    if (requestPriority < priorityLevels[(this.config.minPriorityForImmediate || 'high')]) {
      return {
        allowed: false,
        reason: `Prioridade ${priority} abaixo do mínimo para interrupção`,
      };
    }

    return { allowed: true, reason: 'Interrupção permitida' };
  }

  /**
   * Registra uma interrupção
   */
  recordInterruption(userId: string, requestId: string): void {
    const budget = this.budgets.get(userId);
    if (!budget) return;

    budget.currentInterruptions++;
    budget.cooldownUntil = new Date(Date.now() + (this.config.cooldownAfterInterruption || 10) * 60 * 1000);
    this.budgets.set(userId, budget);

    this.logger.info(`[AttentionEconomy] Interruption recorded for ${userId} (${budget.currentInterruptions})`);
    this.emit('interruption:recorded', { userId, requestId, count: budget.currentInterruptions });
  }

  /**
   * Solicita atenção do usuário
   */
  requestAttention(userId: string, title: string, description: string, priority: 'low' | 'medium' | 'high' | 'critical'): {
    request: AttentionRequest;
    allowed: boolean;
    reason: string;
  } {
    const canInterrupt = this.canInterrupt(userId, priority);

    const request: AttentionRequest = {
      id: `att_${Date.now()}_${Math.random().toString(36).slice(2, 6)}`,
      userId,
      title,
      description,
      priority,
      estimatedAttentionCost: this.estimateAttentionCost(priority),
      requiresImmediate: priority === 'critical',
    };

    this.requests.set(request.id, request);

    this.logger.info(`[AttentionEconomy] Attention request: ${request.id} (${priority})`);

    if (!canInterrupt.allowed) {
      this.emit('attention:blocked', { request, reason: canInterrupt.reason });
      return {
        request,
        allowed: false,
        reason: canInterrupt.reason,
      };
    }

    this.recordInterruption(userId, request.id);
    this.emit('attention:requested', request);

    return {
      request,
      allowed: true,
      reason: 'Atenção solicitada com sucesso',
    };
  }

  /**
   * Estima custo de atenção
   */
  private estimateAttentionCost(priority: 'low' | 'medium' | 'high' | 'critical'): number {
    const costs: Record<string, number> = {
      low: 1,
      medium: 3,
      high: 5,
      critical: 10,
    };
    return costs[priority] || 3;
  }

  /**
   * Atualiza prioridade do usuário
   */
  updateUserPriority(userId: string, priority: 'low' | 'medium' | 'high' | 'critical'): void {
    const budget = this.budgets.get(userId);
    if (!budget) return;

    budget.priority = priority;
    this.budgets.set(userId, budget);

    this.logger.info(`[AttentionEconomy] User priority updated: ${userId} -> ${priority}`);
    this.emit('user:priority_updated', { userId, priority });
  }

  /**
   * Obtém estatísticas
   */
  getStats(): {
    totalUsers: number;
    totalRequests: number;
    blockedRequests: number;
    averageInterruptions: number;
  } {
    const budgets = Array.from(this.budgets.values());
    const requests = Array.from(this.requests.values());

    return {
      totalUsers: budgets.length,
      totalRequests: requests.length,
      blockedRequests: requests.filter((r) => !r.requiresImmediate).length,
      averageInterruptions: budgets.length > 0
        ? budgets.reduce((sum, b) => sum + b.currentInterruptions, 0) / budgets.length
        : 0,
    };
  }
}
