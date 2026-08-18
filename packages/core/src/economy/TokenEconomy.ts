import { EventEmitter } from 'events';
import { getGlobalLogger } from '@network-agents/observability';
export interface TokenBudget {
  allocated: number;
  used: number;
  reserved: number;
  limit: number;
  period: 'daily' | 'weekly' | 'monthly';
  resetAt: Date;
}
export interface TokenCost {
  model: string;
  inputTokens: number;
  outputTokens: number;
  totalTokens: number;
  estimatedCost: number;
  timestamp: Date;
}
export interface CostOptimization {
  strategy: 'cache' | 'compress' | 'reuse' | 'smaller_model' | 'batch' | 'summarize';
  estimatedSavings: number;
  impact: 'low' | 'medium' | 'high';
  appliesTo: string[];
  description: string;
}
export class TokenEconomy extends EventEmitter {
  // Público (em vez de privado) para permitir inspeção direta em testes unitários
  // (ex.: tests/unit/TokenEconomy.test.ts faz `economy.budgets.get(...)`).
  public budgets: Map<string, TokenBudget> = new Map();
  private costs: TokenCost[] = [];
  private logger = getGlobalLogger();
  private cache: Map<string, { result: any; timestamp: Date; tokens: number }> = new Map();
  constructor(private config: {
    defaultBudget?: number;
    cacheTTL?: number;
    minSavingsForOptimization?: number;
  } = {}) {
    super();
    this.config.defaultBudget = config.defaultBudget || 1000000;
    this.config.cacheTTL = config.cacheTTL || 3600;
    this.config.minSavingsForOptimization = config.minSavingsForOptimization || 1000;
  }
  /**
   * Aloca orçamento para uma execução
   */
  allocateBudget(executionId: string, requestedTokens: number): TokenBudget {
    const budget: TokenBudget = {
      allocated: requestedTokens,
      used: 0,
      reserved: 0,
      limit: this.config.defaultBudget!,
      period: 'daily',
      resetAt: new Date(Date.now() + 24 * 60 * 60 * 1000),
    };
    this.budgets.set(executionId, budget);
    this.logger.info(`[TokenEconomy] Budget allocated for ${executionId}: ${requestedTokens} tokens`);
    this.emit('budget:allocated', { executionId, budget });
    return budget;
  }
  /**
   * Registra consumo de tokens
   */
  recordUsage(executionId: string, cost: TokenCost): void {
    const budget = this.budgets.get(executionId);
    if (!budget) {
      this.logger.warn(`[TokenEconomy] No budget found for ${executionId}`);
      return;
    }
    budget.used += cost.totalTokens;
    this.budgets.set(executionId, budget);
    this.costs.push(cost);
    this.logger.debug(`[TokenEconomy] Usage recorded: ${cost.totalTokens} tokens (${cost.model})`);
    this.emit('usage:recorded', { executionId, cost });
    // Verifica se atingiu limite
    if (budget.used > budget.limit) {
      this.emit('budget:exceeded', { executionId, budget });
      this.logger.warn(`[TokenEconomy] Budget exceeded for ${executionId}: ${budget.used}/${budget.limit}`);
    }
  }
  /**
   * Calcula custo estimado para uma tarefa
   */
  estimateCost(model: string, inputTokens: number, outputTokens: number): TokenCost {
    const costPerToken = this.getCostPerToken(model);
    const totalTokens = inputTokens + outputTokens;
    const estimatedCost = totalTokens * costPerToken;
    return {
      model,
      inputTokens,
      outputTokens,
      totalTokens,
      estimatedCost,
      timestamp: new Date(),
    };
  }
  /**
   * Obtém estratégias de otimização disponíveis
   */
  getOptimizations(executionId: string): CostOptimization[] {
    const budget = this.budgets.get(executionId);
    if (!budget) {
      return [];
    }
    const optimizations: CostOptimization[] = [];
    // Cache de resultados
    if (this.cache.size > 0) {
      optimizations.push({
        strategy: 'cache',
        estimatedSavings: this.estimateCacheSavings(),
        impact: 'medium',
        appliesTo: ['repeat_queries', 'similar_requests'],
        description: 'Reutilizar resultados cacheados para evitar processamento repetido',
      });
    }
    // Compressão de contexto
    if (budget.used > budget.allocated * 0.5) {
      optimizations.push({
        strategy: 'compress',
        estimatedSavings: budget.used * 0.3,
        impact: 'high',
        appliesTo: ['long_context', 'large_documents'],
        description: 'Comprimir contexto para reduzir tokens de entrada',
      });
    }
    // Modelo menor
    if (budget.used > budget.limit * 0.7) {
      optimizations.push({
        strategy: 'smaller_model',
        estimatedSavings: budget.used * 0.5,
        impact: 'high',
        appliesTo: ['simple_tasks', 'classification'],
        description: 'Usar modelo menor para tarefas que não exigem modelo premium',
      });
    }
    // Reutilização de conhecimento
    optimizations.push({
      strategy: 'reuse',
      estimatedSavings: this.estimateReuseSavings(executionId),
      impact: 'medium',
      appliesTo: ['knowledge_base', 'rag'],
      description: 'Reutilizar conhecimento já processado em vez de reprocessar',
    });
    // Sumarização
    if (budget.used > budget.allocated * 0.6) {
      optimizations.push({
        strategy: 'summarize',
        estimatedSavings: budget.used * 0.4,
        impact: 'medium',
        appliesTo: ['long_documents', 'conversations'],
        description: 'Sumarizar conteúdo extenso antes de processar',
      });
    }
    // Filtra otimizações com economia significativa
    return optimizations.filter(
      (o) => o.estimatedSavings >= (this.config.minSavingsForOptimization || 1000)
    );
  }
  /**
   * Aplica otimizações a uma execução
   */
  applyOptimizations(executionId: string, strategies: CostOptimization['strategy'][]): {
    applied: string[];
    estimatedSavings: number;
    warnings: string[];
  } {
    const budget = this.budgets.get(executionId);
    if (!budget) {
      throw new Error(`No budget found for ${executionId}`);
    }
    const applied: string[] = [];
    let estimatedSavings = 0;
    const warnings: string[] = [];
    for (const strategy of strategies) {
      switch (strategy) {
        case 'cache':
          this.enableCache(executionId);
          applied.push('cache');
          estimatedSavings += this.estimateCacheSavings();
          break;
        case 'compress':
          this.enableCompression(executionId);
          applied.push('compress');
          estimatedSavings += budget.used * 0.3;
          break;
        case 'smaller_model':
          this.setSmallerModel(executionId);
          applied.push('smaller_model');
          estimatedSavings += budget.used * 0.5;
          warnings.push('Modelo menor pode reduzir qualidade em tarefas complexas');
          break;
        case 'reuse':
          this.enableReuse(executionId);
          applied.push('reuse');
          estimatedSavings += this.estimateReuseSavings(executionId);
          break;
        case 'summarize':
          this.enableSummarization(executionId);
          applied.push('summarize');
          estimatedSavings += budget.used * 0.4;
          warnings.push('Sumarização pode perder detalhes importantes');
          break;
        default:
          warnings.push(`Estratégia ${strategy} não reconhecida`);
      }
    }
    this.logger.info(`[TokenEconomy] Optimizations applied to ${executionId}: ${applied.join(', ')}`);
    this.emit('optimizations:applied', { executionId, applied, estimatedSavings });
    return { applied, estimatedSavings, warnings };
  }
  /**
   * Obtém métricas de economia
   */
  getSavingsMetrics(executionId: string): {
    totalSavings: number;
    savingsByStrategy: Record<string, number>;
    efficiency: number;
  } {
    const budget = this.budgets.get(executionId);
    if (!budget) {
      return { totalSavings: 0, savingsByStrategy: {}, efficiency: 0 };
    }
    const totalTokens = this.costs
      .filter((c) => c.model.includes(executionId))
      .reduce((sum, c) => sum + c.totalTokens, 0);
    const efficiency = budget.allocated > 0 ? (budget.used / budget.allocated) * 100 : 0;
    return {
      totalSavings: budget.allocated - budget.used,
      savingsByStrategy: {
        cache: this.estimateCacheSavings(),
        compress: budget.used * 0.3,
        smaller_model: budget.used * 0.5,
        reuse: this.estimateReuseSavings(executionId),
        summarize: budget.used * 0.4,
      },
      efficiency,
    };
  }
  /**
   * Pesquisa antes da construção - verifica se já existe capacidade equivalente
   */
  async searchBeforeBuild(query: {
    type: string;
    description: string;
    domain?: string;
    requirements?: string[];
  }): Promise<{
    exists: boolean;
    alternatives: Array<{
      id: string;
      name: string;
      description: string;
      similarity: number;
      costToReuse: number;
    }>;
    recommendation: 'reuse' | 'adapt' | 'build' | 'external';
    reason: string;
  }> {
    this.logger.info(`[TokenEconomy] Search before build: ${query.description}`);
    // Simula busca em capacidades existentes
    // Em produção, isso consultaria o Catálogo Universal de Capacidades
    const alternatives = this.searchExistingCapabilities(query);
    if (alternatives.length === 0) {
      return {
        exists: false,
        alternatives: [],
        recommendation: 'build',
        reason: 'Nenhuma capacidade equivalente encontrada. Recomenda-se construir nova.',
      };
    }
    const best = alternatives[0];
    if (best.similarity > 0.8) {
      return {
        exists: true,
        alternatives,
        recommendation: 'reuse',
        reason: `Capacidade "${best.name}" encontrada com ${(best.similarity * 100).toFixed(0)}% de similaridade. Reutilização recomendada.`,
      };
    }
    if (best.similarity > 0.5) {
      return {
        exists: true,
        alternatives,
        recommendation: 'adapt',
        reason: `Capacidade "${best.name}" encontrada com ${(best.similarity * 100).toFixed(0)}% de similaridade. Adaptação recomendada.`,
      };
    }
    return {
      exists: true,
      alternatives,
      recommendation: 'external',
      reason: 'Capacidades similares encontradas, mas com baixa similaridade. Considere solução externa.',
    };
  }
  /**
   * Habilita cache para uma execução
   */
  private enableCache(executionId: string): void {
    // Em produção, ativaria cache para esta execução
    this.emit('cache:enabled', { executionId });
  }
  /**
   * Habilita compressão de contexto
   */
  private enableCompression(executionId: string): void {
    this.emit('compression:enabled', { executionId });
  }
  /**
   * Usa modelo menor
   */
  private setSmallerModel(executionId: string): void {
    this.emit('model:downscaled', { executionId });
  }
  /**
   * Habilita reutilização de conhecimento
   */
  private enableReuse(executionId: string): void {
    this.emit('reuse:enabled', { executionId });
  }
  /**
   * Habilita sumarização
   */
  private enableSummarization(executionId: string): void {
    this.emit('summarize:enabled', { executionId });
  }
  /**
   * Busca capacidades existentes (simulação)
   */
  private searchExistingCapabilities(query: any): Array<{
    id: string;
    name: string;
    description: string;
    similarity: number;
    costToReuse: number;
  }> {
    // Simulação de busca
    // Em produção, consultaria o Catálogo Universal de Capacidades
    return [
      {
        id: 'cap_001',
        name: 'OCR de Notas Fiscais',
        description: 'Extrai dados de notas fiscais usando OCR',
        similarity: 0.85,
        costToReuse: 100,
      },
      {
        id: 'cap_002',
        name: 'Analisador de Contratos',
        description: 'Analisa contratos e identifica cláusulas críticas',
        similarity: 0.60,
        costToReuse: 200,
      },
      {
        id: 'cap_003',
        name: 'Gerador de Relatórios Financeiros',
        description: 'Gera relatórios financeiros a partir de dados',
        similarity: 0.40,
        costToReuse: 150,
      },
    ].filter((alt) => {
      // Filtra por domínio se especificado
      if (query.domain && !alt.description.includes(query.domain)) {
        return false;
      }
      return true;
    });
  }
  /**
   * Estima economia com cache
   */
  private estimateCacheSavings(): number {
    return this.cache.size * 500; // 500 tokens por cache hit
  }
  /**
   * Estima economia com reutilização
   */
  private estimateReuseSavings(executionId: string): number {
    const budget = this.budgets.get(executionId);
    return budget ? budget.used * 0.2 : 0;
  }
  /**
   * Obtém custo por token por modelo
   */
  private getCostPerToken(model: string): number {
    const costs: Record<string, number> = {
      'gpt-4-turbo': 0.00001,
      'gpt-4': 0.00003,
      'gpt-3.5-turbo': 0.000002,
      'claude-3-opus': 0.000015,
      'claude-3-sonnet': 0.000005,
      'gemini-pro': 0.000004,
      'gemini-ultra': 0.000012,
    };
    return costs[model] || 0.00001;
  }
  /**
   * Obtém relatório de custos
   */
  getCostReport(period?: 'daily' | 'weekly' | 'monthly'): {
    totalTokens: number;
    totalCost: number;
    byModel: Record<string, { tokens: number; cost: number }>;
    byExecution: Record<string, { tokens: number; cost: number }>;
    savings: number;
    efficiency: number;
  } {
    const report = {
      totalTokens: 0,
      totalCost: 0,
      byModel: {} as Record<string, { tokens: number; cost: number }>,
      byExecution: {} as Record<string, { tokens: number; cost: number }>,
      savings: 0,
      efficiency: 0,
    };
    for (const cost of this.costs) {
      report.totalTokens += cost.totalTokens;
      report.totalCost += cost.estimatedCost;
      if (!report.byModel[cost.model]) {
        report.byModel[cost.model] = { tokens: 0, cost: 0 };
      }
      report.byModel[cost.model].tokens += cost.totalTokens;
      report.byModel[cost.model].cost += cost.estimatedCost;
    }
    // Calcula eficiência
    const totalBudget = Array.from(this.budgets.values()).reduce(
      (sum, b) => sum + b.allocated,
      0
    );
    report.efficiency = totalBudget > 0 ? (report.totalTokens / totalBudget) * 100 : 0;
    return report;
  }
  /**
   * Limpa cache antigo
   */
  cleanCache(maxAge?: number): void {
    const now = Date.now();
    const ttl = maxAge || this.config.cacheTTL || 3600;
    for (const [key, value] of this.cache) {
      if (now - value.timestamp.getTime() > ttl * 1000) {
        this.cache.delete(key);
      }
    }
    this.logger.info(`[TokenEconomy] Cache cleaned. Remaining: ${this.cache.size} entries`);
  }
  /**
   * Obtém estatísticas de cache
   */
  getCacheStats(): {
    size: number;
    hits: number;
    misses: number;
    hitRate: number;
  } {
    return {
      size: this.cache.size,
      hits: 0,
      misses: 0,
      hitRate: 0,
    };
  }
}
