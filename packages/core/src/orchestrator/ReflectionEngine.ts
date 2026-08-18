// packages/core/src/orchestrator/ReflectionEngine.ts
import { EventEmitter } from 'events';
import { getGlobalLogger } from '@network-agents/observability';
import { ImmunologicalMemory } from '../immunity/ImmunologicalMemory';
import { SelfAwareness } from '../observability/SelfAwareness';
import { TokenEconomy } from '../economy/TokenEconomy';

export interface ReflectionResult {
  id: string;
  executionId: string;
  success: boolean;
  score: number; // 0-100
  strengths: string[];
  weaknesses: string[];
  improvements: string[];
  lessons: string[];
  recommendations: string[];
  timestamp: Date;
  metadata: Record<string, any>;
}

export class ReflectionEngine extends EventEmitter {
  private logger = getGlobalLogger();
  private reflections: Map<string, ReflectionResult> = new Map();

  constructor(
    private immunologicalMemory: ImmunologicalMemory,
    private selfAwareness: SelfAwareness,
    private tokenEconomy: TokenEconomy,
    private config: {
      minScoreForSuccess?: number;
      autoLearn?: boolean;
    } = {}
  ) {
    super();
    this.config.minScoreForSuccess = config.minScoreForSuccess || 70;
    this.config.autoLearn = config.autoLearn !== false;
    this.logger.info('[ReflectionEngine] Initialized');
  }

  /**
   * Executa reflexão sobre uma execução
   */
  async reflect(executionId: string, executionResult: any): Promise<ReflectionResult> {
    this.logger.info(`[ReflectionEngine] Reflecting on execution: ${executionId}`);

    const startTime = Date.now();

    // 1. Avalia o resultado
    const assessment = await this.assessExecution(executionResult);

    // 2. Identifica pontos fortes e fracos
    const { strengths, weaknesses } = this.identifyStrengthsWeaknesses(executionResult);

    // 3. Gera lições aprendidas
    const lessons = this.extractLessons(executionResult, assessment);

    // 4. Gera recomendações
    const recommendations = this.generateRecommendations(executionResult, assessment, weaknesses);

    // 5. Calcula score
    const score = this.calculateScore(executionResult, assessment);

    // 6. Cria resultado
    const result: ReflectionResult = {
      id: `ref_${Date.now()}_${Math.random().toString(36).slice(2, 6)}`,
      executionId,
      success: score >= (this.config.minScoreForSuccess || 70),
      score,
      strengths,
      weaknesses,
      improvements: this.identifyImprovements(executionResult, weaknesses),
      lessons,
      recommendations,
      timestamp: new Date(),
      metadata: {
        durationMs: Date.now() - startTime,
        executionResult: executionResult,
      },
    };

    this.reflections.set(result.id, result);

    // 7. Auto-aprendizagem
    if (this.config.autoLearn) {
      await this.learnFromReflection(result);
    }

    // 8. Registra evento na memória imunológica
    if (!result.success) {
      this.immunologicalMemory.registerEvent({
        type: 'failure',
        severity: score < 40 ? 'critical' : 'high',
        description: `Execution ${executionId} failed reflection with score ${score}`,
        rootCause: weaknesses.join(', '),
        impact: {
          components: ['execution'],
          durationMs: result.metadata.durationMs || 0,
          dataLoss: false,
          serviceDegradation: true,
        },
        response: {
          action: 'reflection_completed',
          executedBy: 'ReflectionEngine',
          durationMs: Date.now() - startTime,
          success: true,
        },
        learnings: lessons,
        recommendations: recommendations,
        status: 'resolved',
        metadata: { executionId, score },
      });
    }

    this.emit('reflection:completed', result);
    this.logger.info(`[ReflectionEngine] Reflection completed: ${result.id} (score: ${score})`);

    return result;
  }

  /**
   * Avalia a execução
   */
  private async assessExecution(executionResult: any): Promise<any> {
    const assessment: any = {
      success: executionResult.success || false,
      stepsCompleted: executionResult.steps?.filter((s: any) => s.success).length || 0,
      stepsFailed: executionResult.steps?.filter((s: any) => !s.success).length || 0,
      totalSteps: executionResult.steps?.length || 0,
      durationMs: executionResult.metadata?.durationMs || 0,
      tokensUsed: executionResult.metadata?.totalTokens || 0,
      cost: executionResult.metadata?.totalCost || 0,
      errors: executionResult.errors || [],
    };

    // Calcula eficiência
    assessment.efficiency = assessment.totalSteps > 0
      ? (assessment.stepsCompleted / assessment.totalSteps) * 100
      : 0;

    // Avalia custo-benefício
    assessment.costBenefit = assessment.tokensUsed > 0
      ? assessment.stepsCompleted / assessment.tokensUsed
      : 0;

    return assessment;
  }

  /**
   * Identifica pontos fortes e fracos
   */
  private identifyStrengthsWeaknesses(executionResult: any): {
    strengths: string[];
    weaknesses: string[];
  } {
    const strengths: string[] = [];
    const weaknesses: string[] = [];

    if (executionResult.success) {
      strengths.push('Execução bem-sucedida');
    } else {
      weaknesses.push('Falha na execução');
    }

    const steps = executionResult.steps || [];
    for (const step of steps) {
      if (step.success) {
        strengths.push(`Passo ${step.id} executado com sucesso`);
      } else {
        weaknesses.push(`Passo ${step.id} falhou: ${step.error || 'erro desconhecido'}`);
      }
    }

    // Análise de performance
    if (executionResult.metadata?.durationMs) {
      if (executionResult.metadata.durationMs < 1000) {
        strengths.push('Execução rápida (< 1s)');
      } else if (executionResult.metadata.durationMs > 10000) {
        weaknesses.push('Execução lenta (> 10s)');
      }
    }

    // Análise de tokens
    if (executionResult.metadata?.totalTokens) {
      if (executionResult.metadata.totalTokens < 1000) {
        strengths.push('Baixo consumo de tokens');
      } else if (executionResult.metadata.totalTokens > 10000) {
        weaknesses.push('Alto consumo de tokens');
      }
    }

    return { strengths, weaknesses };
  }

  /**
   * Extrai lições aprendidas
   */
  private extractLessons(executionResult: any, assessment: any): string[] {
    const lessons: string[] = [];

    if (executionResult.success) {
      lessons.push('Estratégia de execução foi eficaz');
    } else {
      lessons.push('A execução falhou. Revisar planejamento.');
    }

    if (assessment.efficiency > 80) {
      lessons.push('Alta eficiência na execução das etapas');
    } else if (assessment.efficiency < 50) {
      lessons.push('Baixa eficiência. Otimizar fluxo de execução.');
    }

    if (executionResult.errors && executionResult.errors.length > 0) {
      lessons.push(`Erros identificados: ${executionResult.errors.join(', ')}`);
    }

    return lessons;
  }

  /**
   * Gera recomendações
   */
  private generateRecommendations(executionResult: any, assessment: any, weaknesses: string[]): string[] {
    const recommendations: string[] = [];

    if (!executionResult.success) {
      recommendations.push('Revisar o plano de execução para corrigir falhas');
    }

    if (assessment.efficiency < 50) {
      recommendations.push('Otimizar a sequência de etapas para melhorar eficiência');
    }

    if (assessment.tokensUsed > 10000) {
      recommendations.push('Reduzir consumo de tokens usando modelos menores ou cache');
    }

    if (executionResult.errors && executionResult.errors.length > 0) {
      recommendations.push(`Corrigir os erros: ${executionResult.errors.join(', ')}`);
    }

    if (weaknesses.length > 0) {
      recommendations.push(`Endereçar pontos fracos: ${weaknesses.join(', ')}`);
    }

    if (recommendations.length === 0) {
      recommendations.push('Manter a estratégia atual. Execução bem-sucedida.');
    }

    return recommendations;
  }

  /**
   * Calcula score da reflexão
   */
  private calculateScore(executionResult: any, assessment: any): number {
    let score = 50; // Base

    // Sucesso
    if (executionResult.success) score += 20;

    // Eficiência
    if (assessment.efficiency > 80) score += 10;
    else if (assessment.efficiency > 60) score += 5;
    else if (assessment.efficiency < 40) score -= 10;

    // Sem erros
    if (!executionResult.errors || executionResult.errors.length === 0) {
      score += 10;
    } else {
      score -= 5 * Math.min(executionResult.errors.length, 3);
    }

    // Duração
    if (assessment.durationMs < 1000) score += 5;
    else if (assessment.durationMs > 10000) score -= 5;

    // Tokens
    if (assessment.tokensUsed < 1000) score += 5;
    else if (assessment.tokensUsed > 10000) score -= 5;

    return Math.max(0, Math.min(100, score));
  }

  /**
   * Identifica melhorias
   */
  private identifyImprovements(executionResult: any, weaknesses: string[]): string[] {
    const improvements: string[] = [];

    if (executionResult.success) {
      improvements.push('Manter a estratégia atual e documentar para reutilização');
    }

    for (const weakness of weaknesses) {
      if (weakness.includes('falhou')) {
        improvements.push(`Corrigir a falha em ${weakness}`);
      }
      if (weakness.includes('lenta')) {
        improvements.push('Otimizar performance');
      }
      if (weakness.includes('alto consumo')) {
        improvements.push('Reduzir consumo de tokens');
      }
    }

    if (improvements.length === 0) {
      improvements.push('Nenhuma melhoria identificada');
    }

    return improvements;
  }

  /**
   * Aprende com a reflexão
   */
  private async learnFromReflection(result: ReflectionResult): Promise<void> {
    if (result.success) {
      // Aprende com sucesso
      this.logger.info(`[ReflectionEngine] Learning from success: ${result.id}`);

      // Atualiza métricas de sucesso
      this.tokenEconomy.recordUsage('reflection', {
        model: 'reflection_engine',
        inputTokens: 0,
        outputTokens: 0,
        totalTokens: 0,
        estimatedCost: 0,
        timestamp: new Date(),
      });

      // Atualiza autopercepção
      await this.selfAwareness.updateState();

      this.emit('learning:success', result);
    } else {
      // Aprende com falha
      this.logger.warn(`[ReflectionEngine] Learning from failure: ${result.id}`);

      // Registra falha na memória imunológica
      this.immunologicalMemory.registerEvent({
        type: 'failure',
        severity: 'high',
        description: `Aprendizado de falha: ${result.weaknesses.join(', ')}`,
        rootCause: result.weaknesses.join(', '),
        impact: {
          components: ['learning'],
          durationMs: 0,
          dataLoss: false,
          serviceDegradation: true,
        },
        response: {
          action: 'learned_from_failure',
          executedBy: 'ReflectionEngine',
          durationMs: 0,
          success: true,
        },
        learnings: result.lessons,
        recommendations: result.recommendations,
        status: 'resolved',
        metadata: { reflectionId: result.id },
      });

      this.emit('learning:failure', result);
    }
  }

  /**
   * Obtém reflexão por ID
   */
  getReflection(id: string): ReflectionResult | undefined {
    return this.reflections.get(id);
  }

  /**
   * Obtém reflexões por execução
   */
  getReflectionsByExecution(executionId: string): ReflectionResult[] {
    return Array.from(this.reflections.values()).filter(
      (r) => r.executionId === executionId
    );
  }

  /**
   * Obtém estatísticas
   */
  getStats(): {
    total: number;
    successful: number;
    failed: number;
    averageScore: number;
  } {
    const reflections = Array.from(this.reflections.values());
    const total = reflections.length;
    const successful = reflections.filter((r) => r.success).length;
    const failed = reflections.filter((r) => !r.success).length;
    const averageScore = total > 0
      ? reflections.reduce((sum, r) => sum + r.score, 0) / total
      : 0;

    return { total, successful, failed, averageScore };
  }
}
