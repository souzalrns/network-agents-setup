import { EventEmitter } from 'events';
import { getGlobalLogger } from '@network-agents/observability';

// P-004: Motor de Reflexão — auto-avaliação e aprendizado automático a partir
// dos resultados de execução (ciclo observação -> reflexão -> aprendizado).

export interface ReflectionScore {
  correctness: number; // 0-100
  efficiency: number; // 0-100
  alignment: number; // 0-100 (alinhamento com a intenção original)
  overall: number; // 0-100
}

export interface Reflection {
  id: string;
  executionId: string;
  input: string;
  output: string;
  success: boolean;
  score: ReflectionScore;
  insights: string[];
  learnings: string[];
  createdAt: Date;
}

export interface LearnedPattern {
  id: string;
  pattern: string;
  context: string;
  confidence: number;
  occurrences: number;
  firstSeen: Date;
  lastSeen: Date;
}

export class ReflectionEngine extends EventEmitter {
  private reflections: Map<string, Reflection> = new Map();
  private patterns: Map<string, LearnedPattern> = new Map();
  private logger = getGlobalLogger();

  constructor(
    private config: {
      minScoreForLearning?: number;
      maxReflectionsHistory?: number;
    } = {}
  ) {
    super();
    this.config.minScoreForLearning = config.minScoreForLearning ?? 60;
    this.config.maxReflectionsHistory = config.maxReflectionsHistory ?? 5000;
  }

  /**
   * Reflete sobre o resultado de uma execução, gera score e aprende com ele.
   */
  reflect(params: {
    executionId: string;
    input: string;
    output: string;
    success: boolean;
    errors?: string[];
    durationMs?: number;
    expectedDurationMs?: number;
  }): Reflection {
    const score = this.scoreExecution(params);
    const insights = this.generateInsights(params, score);
    const learnings = this.extractLearnings(params, score);

    const reflection: Reflection = {
      id: `refl_${Date.now()}_${Math.random().toString(36).slice(2, 6)}`,
      executionId: params.executionId,
      input: params.input,
      output: params.output,
      success: params.success,
      score,
      insights,
      learnings,
      createdAt: new Date(),
    };

    this.reflections.set(reflection.id, reflection);
    this.trimHistory();

    if (score.overall >= (this.config.minScoreForLearning || 60) && params.success) {
      this.learnFromReflection(reflection);
    }

    this.logger.info(`[ReflectionEngine] Reflection ${reflection.id} scored ${score.overall.toFixed(1)}`);
    this.emit('reflection:created', reflection);
    return reflection;
  }

  private scoreExecution(params: {
    success: boolean;
    errors?: string[];
    durationMs?: number;
    expectedDurationMs?: number;
  }): ReflectionScore {
    const correctness = params.success ? 100 - Math.min((params.errors?.length || 0) * 15, 60) : 20;
    let efficiency = 80;
    if (params.durationMs && params.expectedDurationMs) {
      const ratio = params.durationMs / params.expectedDurationMs;
      efficiency = ratio <= 1 ? 100 : Math.max(100 - (ratio - 1) * 50, 10);
    }
    const alignment = params.success ? 85 : 40;
    const overall = correctness * 0.4 + efficiency * 0.3 + alignment * 0.3;
    return { correctness, efficiency, alignment, overall };
  }

  private generateInsights(
    params: { success: boolean; errors?: string[] },
    score: ReflectionScore
  ): string[] {
    const insights: string[] = [];
    if (score.overall >= 85) insights.push('Execução de alta qualidade, considerar como referência.');
    if (score.efficiency < 50) insights.push('Execução ineficiente — investigar oportunidades de otimização.');
    if (!params.success) insights.push(`Falha na execução: ${(params.errors || []).join(', ') || 'motivo desconhecido'}.`);
    return insights;
  }

  private extractLearnings(params: { input: string; success: boolean }, score: ReflectionScore): string[] {
    const learnings: string[] = [];
    if (params.success && score.overall >= 70) {
      learnings.push(`Padrão bem-sucedido identificado para: "${params.input.slice(0, 80)}"`);
    }
    return learnings;
  }

  private learnFromReflection(reflection: Reflection): void {
    const key = reflection.input.slice(0, 60).toLowerCase().trim();
    const existing = this.patterns.get(key);
    if (existing) {
      existing.occurrences += 1;
      existing.lastSeen = new Date();
      existing.confidence = Math.min(existing.confidence + 2, 100);
      this.patterns.set(key, existing);
    } else {
      const pattern: LearnedPattern = {
        id: `pat_${Date.now()}_${Math.random().toString(36).slice(2, 6)}`,
        pattern: key,
        context: reflection.input,
        confidence: reflection.score.overall,
        occurrences: 1,
        firstSeen: new Date(),
        lastSeen: new Date(),
      };
      this.patterns.set(key, pattern);
      this.emit('pattern:learned', pattern);
    }
  }

  private trimHistory(): void {
    const max = this.config.maxReflectionsHistory || 5000;
    if (this.reflections.size <= max) return;
    const sorted = Array.from(this.reflections.values()).sort(
      (a, b) => a.createdAt.getTime() - b.createdAt.getTime()
    );
    const toRemove = sorted.slice(0, sorted.length - max);
    for (const r of toRemove) this.reflections.delete(r.id);
  }

  getReflections(executionId?: string): Reflection[] {
    const all = Array.from(this.reflections.values());
    return executionId ? all.filter((r) => r.executionId === executionId) : all;
  }

  getLearnedPatterns(minConfidence: number = 0): LearnedPattern[] {
    return Array.from(this.patterns.values()).filter((p) => p.confidence >= minConfidence);
  }

  getAverageScore(): number {
    const all = Array.from(this.reflections.values());
    if (all.length === 0) return 0;
    return all.reduce((sum, r) => sum + r.score.overall, 0) / all.length;
  }
}
