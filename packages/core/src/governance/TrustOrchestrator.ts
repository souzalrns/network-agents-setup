import { getGlobalLogger } from '@network-agents/observability';
import { TrustManager } from './TrustManager';
import { SecurityManager } from '../security/SecurityManager';
import { SelfAwareness } from '../observability/SelfAwareness';

// P-014/015: Orquestra a certificação de competências combinando a
// avaliação de confiança (TrustManager), a postura de segurança
// (SecurityManager) e a autopercepção do sistema (SelfAwareness) em um
// único parecer de certificação, além de expor a escalada de confiança.

export interface CompetenceAssessment {
  competenceId: string;
  passed: boolean;
  trustLevel: string;
  trustScore: number;
  securityScore: number;
  healthScore: number;
  combinedScore: number;
  reason: string;
  metrics: {
    reliability: number;
    stability: number;
    compliance: number;
    quality: number;
    learningCapacity: number;
    decisionQuality: number;
  };
}

export class TrustOrchestrator {
  private logger = getGlobalLogger();

  constructor(
    private trustManager: TrustManager,
    private securityManager: SecurityManager,
    private selfAwareness: SelfAwareness
  ) {}

  /**
   * Avalia uma competência combinando confiança, segurança e saúde do sistema.
   */
  async assessCompetence(competenceId: string): Promise<CompetenceAssessment> {
    const evaluation = this.trustManager.evaluateCompetence(competenceId);

    const securityStatus = this.securityManager.getSecurityStatus();
    const securityScore = Math.max(0, 100 - securityStatus.criticalEvents * 10);

    const state = this.selfAwareness.getState();
    const healthScore = (state as any)?.health?.overall ?? (state as any)?.health ?? 70;

    const trustScore =
      (evaluation.metrics.reliability +
        evaluation.metrics.stability +
        evaluation.metrics.compliance +
        evaluation.metrics.quality +
        evaluation.metrics.learningCapacity +
        evaluation.metrics.decisionQuality) /
      6;

    const combinedScore = trustScore * 0.5 + securityScore * 0.25 + healthScore * 0.25;

    this.logger.info(
      `[TrustOrchestrator] Competência ${competenceId} avaliada: combinedScore=${combinedScore.toFixed(1)}`
    );

    return {
      competenceId,
      passed: evaluation.passed && combinedScore >= 60,
      trustLevel: evaluation.trustLevel,
      trustScore,
      securityScore,
      healthScore: typeof healthScore === 'number' ? healthScore : 70,
      combinedScore,
      reason: evaluation.reason,
      metrics: evaluation.metrics,
    };
  }

  /**
   * Tenta escalar o nível de confiança de uma competência, considerando
   * também a postura de segurança atual do sistema.
   */
  escalateTrust(competenceId: string): {
    canEscalate: boolean;
    newLevel?: string;
    reason: string;
  } {
    const securityStatus = this.securityManager.getSecurityStatus();
    if (securityStatus.criticalEvents > 0) {
      return {
        canEscalate: false,
        reason: `Escalada bloqueada: ${securityStatus.criticalEvents} evento(s) crítico(s) de segurança em aberto.`,
      };
    }
    return this.trustManager.escalateTrust(competenceId);
  }
}
