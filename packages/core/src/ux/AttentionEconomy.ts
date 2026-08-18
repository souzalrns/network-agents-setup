import { EventEmitter } from 'events';
import { getGlobalLogger } from '@network-agents/observability';

// P-035: Economia de Atenção — orçamento de interrupções por usuário,
// cooldown entre interrupções e priorização, para evitar sobrecarregar o
// usuário com solicitações de HITL de baixo valor.

export interface AttentionBudget {
  userId: string;
  dailyBudget: number;
  used: number;
  lastInterruptionAt?: Date;
  resetAt: Date;
}

export class AttentionEconomy extends EventEmitter {
  private budgets: Map<string, AttentionBudget> = new Map();
  private logger = getGlobalLogger();

  constructor(
    private config: {
      dailyBudget?: number;
      cooldownMs?: number;
    } = {}
  ) {
    super();
    this.config.dailyBudget = config.dailyBudget ?? 10;
    this.config.cooldownMs = config.cooldownMs ?? 5 * 60 * 1000; // 5 minutos
  }

  private getOrCreateBudget(userId: string): AttentionBudget {
    let budget = this.budgets.get(userId);
    const now = new Date();
    if (!budget || budget.resetAt < now) {
      budget = {
        userId,
        dailyBudget: this.config.dailyBudget || 10,
        used: 0,
        resetAt: new Date(now.getTime() + 24 * 60 * 60 * 1000),
      };
      this.budgets.set(userId, budget);
    }
    return budget;
  }

  /**
   * Verifica se uma interrupção (HITL) pode ser enviada ao usuário agora.
   */
  canInterrupt(userId: string, priority: 'low' | 'medium' | 'high' | 'critical' = 'medium'): {
    allowed: boolean;
    reason: string;
  } {
    const budget = this.getOrCreateBudget(userId);

    // Interrupções críticas ignoram cooldown e orçamento
    if (priority === 'critical') {
      return { allowed: true, reason: 'Prioridade crítica ignora orçamento de atenção.' };
    }

    if (budget.used >= budget.dailyBudget) {
      return { allowed: false, reason: 'Orçamento diário de interrupções esgotado.' };
    }

    if (budget.lastInterruptionAt) {
      const elapsed = Date.now() - budget.lastInterruptionAt.getTime();
      const cooldown = this.config.cooldownMs || 5 * 60 * 1000;
      if (elapsed < cooldown && priority !== 'high') {
        return { allowed: false, reason: `Em cooldown por mais ${Math.ceil((cooldown - elapsed) / 1000)}s.` };
      }
    }

    return { allowed: true, reason: 'Dentro do orçamento e cooldown.' };
  }

  /**
   * Registra que uma interrupção foi enviada, consumindo orçamento.
   */
  recordInterruption(userId: string): void {
    const budget = this.getOrCreateBudget(userId);
    budget.used += 1;
    budget.lastInterruptionAt = new Date();
    this.budgets.set(userId, budget);
    this.logger.info(`[AttentionEconomy] Interrupção registrada para ${userId} (${budget.used}/${budget.dailyBudget})`);
    this.emit('interruption:recorded', budget);
  }

  resetBudget(userId: string): void {
    this.budgets.delete(userId);
  }

  getBudget(userId: string): AttentionBudget {
    return this.getOrCreateBudget(userId);
  }
}
