import { EventEmitter } from 'events';
import { getGlobalLogger } from '@network-agents/observability';
import { TrustManager, Competence } from './TrustManager';
import { SelfAwareness } from '../observability/SelfAwareness';
import { ImmunologicalMemory } from '../immunity/ImmunologicalMemory';
import { SecurityManager } from '../security/SecurityManager';

export interface TrustAssessment {
  competenceId: string;
  domain: string;
  level: string;
  score: number;
  status: 'certified' | 'pending' | 'suspended' | 'revoked';
  recommendations: string[];
  timestamp: Date;
}

export class TrustOrchestrator extends EventEmitter {
  private logger = getGlobalLogger();
  private assessments: Map<string, TrustAssessment> = new Map();

  constructor(
    private trustManager: TrustManager,
    private selfAwareness: SelfAwareness,
    private immunologicalMemory: ImmunologicalMemory,
    private securityManager: SecurityManager
  ) {
    super();
    this.logger.info('[TrustOrchestrator] Initialized');
  }

  /**
   * Avalia uma competência para certificação (P-015)
   */
  async assessCompetence(competenceId: string): Promise<TrustAssessment> {
    this.logger.info(`[TrustOrchestrator] Assessing competence: ${competenceId}`);

    // 1. Obtém competência
    const competence = this.trustManager.getCompetence(competenceId);
    if (!competence) {
      throw new Error(`Competence ${competenceId} not found`);
    }

    // 2. Avalia métricas de confiança
    const evaluation = this.trustManager.evaluateCompetence(competenceId);

    // 3. Verifica segurança
    const securityStatus = this.securityManager.getSecurityStatus();

    // 4. Verifica saúde organizacional
    const state = this.selfAwareness.getState();
    const health = state?.health?.overall || 50;

    // 5. Calcula score final
    const score = this.calculateFinalScore(evaluation, securityStatus, health);

    // 6. Determina status
    let status: 'certified' | 'pending' | 'suspended' | 'revoked';
    if (evaluation.passed && score >= 70) {
      status = 'certified';
    } else if (score >= 40) {
      status = 'pending';
    } else {
      status = 'suspended';
    }

    // 7. Gera recomendações
    const recommendations = this.generateTrustRecommendations(evaluation, score);

    // 8. Registra na memória imunológica
    if (status === 'certified') {
      this.immunologicalMemory.registerEvent({
        type: 'recovery',
        severity: 'low',
        description: `Competência ${competence.name} certificada com score ${score}%`,
        rootCause: 'certification_success',
        impact: {
          components: ['trust'],
          durationMs: 0,
          dataLoss: false,
          serviceDegradation: false,
        },
        response: {
          action: 'certified',
          executedBy: 'TrustOrchestrator',
          durationMs: 0,
          success: true,
        },
        learnings: ['Certificação bem-sucedida'],
        recommendations: ['Manter métricas de confiança'],
        status: 'resolved',
        metadata: { competenceId, score },
      });
    } else {
      this.immunologicalMemory.registerEvent({
        type: 'vulnerability',
        severity: 'medium',
        description: `Competência ${competence.name} não certificada (score: ${score}%)`,
        rootCause: 'certification_failure',
        impact: {
          components: ['trust'],
          durationMs: 0,
          dataLoss: false,
          serviceDegradation: true,
        },
        response: {
          action: 'pending',
          executedBy: 'TrustOrchestrator',
          durationMs: 0,
          success: false,
        },
        learnings: ['Necessário melhorar métricas'],
        recommendations: recommendations,
        status: 'open',
        metadata: { competenceId, score },
      });
    }

    // 9. Cria assessment
    const assessment: TrustAssessment = {
      competenceId,
      domain: competence.domain,
      level: evaluation.trustLevel,
      score,
      status,
      recommendations,
      timestamp: new Date(),
    };

    this.assessments.set(competenceId, assessment);
    this.emit('trust:assessed', assessment);

    this.logger.info(`[TrustOrchestrator] Assessment complete: ${competenceId} (${status})`);

    return assessment;
  }

  /**
   * Calcula score final
   */
  private calculateFinalScore(evaluation: any, securityStatus: any, health: number): number {
    let score = 0;

    // Métricas de confiança (60%)
    const metricScore = (
      (evaluation.metrics?.reliability || 0) * 0.2 +
      (evaluation.metrics?.stability || 0) * 0.15 +
      (evaluation.metrics?.compliance || 0) * 0.15 +
      (evaluation.metrics?.quality || 0) * 0.15 +
      (evaluation.metrics?.learningCapacity || 0) * 0.1 +
      (evaluation.metrics?.decisionQuality || 0) * 0.15
    );
    score += metricScore * 0.6;

    // Segurança (20%)
    const securityScore = Math.min(100, securityStatus.mfaEnabled * 10 + 50);
    score += securityScore * 0.2;

    // Saúde organizacional (20%)
    score += health * 0.2;

    return Math.max(0, Math.min(100, score));
  }

  /**
   * Gera recomendações de confiança
   */
  private generateTrustRecommendations(evaluation: any, score: number): string[] {
    const recommendations: string[] = [];

    if (score < 70) {
      recommendations.push('Melhorar métricas de confiança para alcançar certificação.');
    }

    if (evaluation.metrics?.reliability < 60) {
      recommendations.push('Aumentar confiabilidade com mais evidências.');
    }

    if (evaluation.metrics?.stability < 60) {
      recommendations.push('Melhorar estabilidade com testes e monitoramento.');
    }

    if (evaluation.metrics?.compliance < 60) {
      recommendations.push('Garantir conformidade com políticas e regulamentações.');
    }

    if (evaluation.metrics?.quality < 60) {
      recommendations.push('Melhorar qualidade com revisões e auditorias.');
    }

    return recommendations;
  }

  /**
   * Escalada de confiança (P-014)
   */
  async escalateTrust(competenceId: string): Promise<{
    escalated: boolean;
    newLevel: string;
    reason: string;
  }> {
    this.logger.info(`[TrustOrchestrator] Escalating trust for: ${competenceId}`);

    const result = this.trustManager.escalateTrust(competenceId);

    if (result.canEscalate && result.newLevel) {
      this.logger.info(`[TrustOrchestrator] Trust escalated to ${result.newLevel} for ${competenceId}`);
      this.emit('trust:escalated', { competenceId, newLevel: result.newLevel });
    }

    return {
      escalated: result.canEscalate,
      newLevel: result.newLevel || 'no_change',
      reason: result.reason,
    };
  }

  /**
   * Obtém avaliação por competência
   */
  getAssessment(competenceId: string): TrustAssessment | undefined {
    return this.assessments.get(competenceId);
  }

  /**
   * Obtém todas as avaliações
   */
  getAssessments(): TrustAssessment[] {
    return Array.from(this.assessments.values());
  }

  /**
   * Obtém competências certificadas
   */
  getCertifiedCompetences(domain?: string): Competence[] {
    return this.trustManager.getCertifiedCompetences(domain);
  }
}
