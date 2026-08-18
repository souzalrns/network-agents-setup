import { EventEmitter } from 'events';
import { getGlobalLogger } from '@network-agents/observability';
export enum TrustLevel {
  LEVEL_0 = 'level_0', // Apenas observa e informa
  LEVEL_1 = 'level_1', // Executa ações reversíveis previamente autorizadas
  LEVEL_2 = 'level_2', // Planeja e executa dentro de limites definidos
  LEVEL_3 = 'level_3', // Reorganiza processos e recursos autonomamente
  LEVEL_4 = 'level_4', // Propõe mudanças estruturais e executa as previamente aprovadas
  LEVEL_5 = 'level_5', // Atua como organização autoadaptativa plena
}
export interface TrustMetrics {
  reliability: number; // 0-100
  stability: number; // 0-100
  compliance: number; // 0-100
  quality: number; // 0-100
  learningCapacity: number; // 0-100
  decisionQuality: number; // 0-100
}
export interface Competence {
  id: string;
  name: string;
  description: string;
  domain: string;
  trustLevel: TrustLevel;
  metrics: TrustMetrics;
  certifiedAt?: Date;
  expiresAt?: Date;
  lastEvaluation?: Date;
  status: 'proposed' | 'in_evaluation' | 'certified' | 'suspended' | 'revoked';
  evidence: string[];
  history: Array<{
    date: Date;
    action: string;
    result: string;
  }>;
}
export interface AutonomyBoundary {
  financialLimit: number;
  operationalScope: string[];
  legalRestrictions: string[];
  ethicalConstraints: string[];
  riskTolerance: 'low' | 'medium' | 'high';
  escalationThreshold: number;
}
export class TrustManager extends EventEmitter {
  private competences: Map<string, Competence> = new Map();
  private logger = getGlobalLogger();
  private autonomyBoundaries: Map<string, AutonomyBoundary> = new Map();
  /**
   * Registra uma nova competência para certificação
   */
  proposeCompetence(params: {
    name: string;
    description: string;
    domain: string;
    initialTrustLevel?: TrustLevel;
    evidence?: string[];
  }): Competence {
    const id = `comp_${Date.now()}_${Math.random().toString(36).slice(2, 6)}`;
    
    const competence: Competence = {
      id,
      name: params.name,
      description: params.description,
      domain: params.domain,
      trustLevel: params.initialTrustLevel || TrustLevel.LEVEL_0,
      metrics: this.getDefaultMetrics(),
      status: 'proposed',
      evidence: params.evidence || [],
      history: [
        {
          date: new Date(),
          action: 'Proposed',
          result: 'Competence submitted for evaluation',
        },
      ],
    };
    this.competences.set(id, competence);
    this.logger.info(`[TrustManager] Competence proposed: ${id} - ${params.name}`);
    this.emit('competence:proposed', competence);
    return competence;
  }
  /**
   * Avalia uma competência para certificação
   */
  evaluateCompetence(competenceId: string): {
    passed: boolean;
    trustLevel: TrustLevel;
    metrics: TrustMetrics;
    reason: string;
  } {
    const competence = this.competences.get(competenceId);
    if (!competence) {
      throw new Error(`Competence ${competenceId} not found`);
    }
    // Calcula métricas baseadas em evidências
    const metrics = this.calculateMetrics(competence);
    competence.metrics = metrics;
    competence.lastEvaluation = new Date();
    // Determina se passa na certificação
    const passed = this.evaluatePass(metrics);
    let trustLevel = competence.trustLevel;
    if (passed) {
      // Avança um nível de confiança
      const levels = Object.values(TrustLevel);
      const currentIndex = levels.indexOf(competence.trustLevel);
      if (currentIndex < levels.length - 1) {
        trustLevel = levels[currentIndex + 1];
      }
      competence.trustLevel = trustLevel;
      competence.status = 'certified';
      competence.certifiedAt = new Date();
      competence.expiresAt = new Date(Date.now() + 180 * 24 * 60 * 60 * 1000); // 180 dias
      this.logger.info(`[TrustManager] Competence ${competenceId} certified at level ${trustLevel}`);
    } else {
      competence.status = 'in_evaluation';
      this.logger.warn(`[TrustManager] Competence ${competenceId} evaluation: ${passed ? 'passed' : 'failed'}`);
    }
    competence.history.push({
      date: new Date(),
      action: passed ? 'Certified' : 'Evaluation Failed',
      result: passed ? `Advanced to ${trustLevel}` : 'Needs improvement',
    });
    this.competences.set(competenceId, competence);
    this.emit(`competence:${passed ? 'certified' : 'failed'}`, competence);
    return {
      passed,
      trustLevel,
      metrics,
      reason: this.generateReason(metrics, passed),
    };
  }
  /**
   * Atualiza métricas de confiança de uma competência
   */
  updateTrustMetrics(competenceId: string, newMetrics: Partial<TrustMetrics>): void {
    const competence = this.competences.get(competenceId);
    if (!competence) {
      throw new Error(`Competence ${competenceId} not found`);
    }
    competence.metrics = {
      ...competence.metrics,
      ...newMetrics,
    };
    // Reavalia automaticamente se houver degradação significativa
    if (this.isDegrading(competence.metrics)) {
      competence.status = 'suspended';
      this.logger.warn(`[TrustManager] Competence ${competenceId} suspended due to metric degradation`);
      this.emit('competence:suspended', competence);
    }
    this.competences.set(competenceId, competence);
  }
  /**
   * Define limites de autonomia para uma competência
   */
  setAutonomyBoundary(
    competenceId: string,
    boundary: AutonomyBoundary
  ): void {
    this.autonomyBoundaries.set(competenceId, boundary);
    this.logger.info(`[TrustManager] Autonomy boundary set for ${competenceId}`);
    this.emit('autonomy:boundary_set', { competenceId, boundary });
  }
  /**
   * Verifica se uma ação está dentro dos limites de autonomia
   */
  checkAutonomy(competenceId: string, action: {
    type: string;
    financialImpact?: number;
    scope?: string;
    legalConcern?: boolean;
    ethicalConcern?: boolean;
  }): {
    allowed: boolean;
    reason: string;
    requiresEscalation: boolean;
  } {
    const boundary = this.autonomyBoundaries.get(competenceId);
    if (!boundary) {
      return {
        allowed: false,
        reason: 'No autonomy boundary defined for this competence',
        requiresEscalation: true,
      };
    }
    // Verifica limite financeiro
    if (action.financialImpact && action.financialImpact > boundary.financialLimit) {
      return {
        allowed: false,
        reason: `Financial impact (${action.financialImpact}) exceeds limit (${boundary.financialLimit})`,
        requiresEscalation: true,
      };
    }
    // Verifica escopo operacional
    if (action.scope && !boundary.operationalScope.includes(action.scope)) {
      return {
        allowed: false,
        reason: `Action scope "${action.scope}" not in allowed scope`,
        requiresEscalation: true,
      };
    }
    // Verifica preocupações legais/éticas
    if (action.legalConcern && !boundary.legalRestrictions.includes('legal_review')) {
      return {
        allowed: false,
        reason: 'Action has legal implications requiring review',
        requiresEscalation: true,
      };
    }
    if (action.ethicalConcern && !boundary.ethicalConstraints.includes('ethical_review')) {
      return {
        allowed: false,
        reason: 'Action has ethical implications requiring review',
        requiresEscalation: true,
      };
    }
    return {
      allowed: true,
      reason: 'Action within autonomy boundaries',
      requiresEscalation: false,
    };
  }
  /**
   * Escalada de confiança - quando a confiança é suficiente para autonomia
   */
  escalateTrust(competenceId: string): {
    canEscalate: boolean;
    newLevel?: TrustLevel;
    reason: string;
  } {
    const competence = this.competences.get(competenceId);
    if (!competence) {
      return {
        canEscalate: false,
        reason: 'Competence not found',
      };
    }
    if (competence.status !== 'certified') {
      return {
        canEscalate: false,
        reason: 'Competence must be certified before escalation',
      };
    }
    const metrics = competence.metrics;
    const score = this.calculateTrustScore(metrics);
    const levels = Object.values(TrustLevel);
    const currentIndex = levels.indexOf(competence.trustLevel);
    if (score >= 80 && currentIndex < levels.length - 1) {
      return {
        canEscalate: true,
        newLevel: levels[currentIndex + 1],
        reason: `Trust score ${score}% meets threshold for next level (${levels[currentIndex + 1]})`,
      };
    }
    return {
      canEscalate: false,
      reason: `Trust score ${score}% below threshold (80% required)`,
    };
  }
  /**
   * Obtém todas as competências certificadas
   */
  getCertifiedCompetences(domain?: string): Competence[] {
    const all = Array.from(this.competences.values());
    return all.filter(
      (c) => c.status === 'certified' && (!domain || c.domain === domain)
    );
  }
  /**
   * Obtém competência por ID
   */
  getCompetence(id: string): Competence | undefined {
    return this.competences.get(id);
  }
  /**
   * Obtém histórico de confiança de uma competência
   */
  getTrustHistory(competenceId: string): Competence['history'] {
    const competence = this.competences.get(competenceId);
    if (!competence) {
      throw new Error(`Competence ${competenceId} not found`);
    }
    return competence.history;
  }
  /**
   * Revoga uma certificação
   */
  revokeCertification(competenceId: string, reason: string): Competence {
    const competence = this.competences.get(competenceId);
    if (!competence) {
      throw new Error(`Competence ${competenceId} not found`);
    }
    competence.status = 'revoked';
    competence.history.push({
      date: new Date(),
      action: 'Revoked',
      result: reason,
    });
    this.competences.set(competenceId, competence);
    this.logger.warn(`[TrustManager] Competence ${competenceId} revoked: ${reason}`);
    this.emit('competence:revoked', competence);
    return competence;
  }
  /**
   * Obtém métricas padrão
   */
  private getDefaultMetrics(): TrustMetrics {
    return {
      reliability: 50,
      stability: 50,
      compliance: 50,
      quality: 50,
      learningCapacity: 50,
      decisionQuality: 50,
    };
  }
  /**
   * Calcula métricas baseadas em evidências
   */
  private calculateMetrics(competence: Competence): TrustMetrics {
    const metrics = { ...competence.metrics };
    // Ajusta baseado em evidências
    const evidenceCount = competence.evidence.length;
    if (evidenceCount > 0) {
      metrics.reliability = Math.min(metrics.reliability + evidenceCount * 2, 100);
      metrics.quality = Math.min(metrics.quality + evidenceCount * 1.5, 100);
    }
    // Ajusta baseado no histórico
    const successRate = this.calculateSuccessRate(competence.history);
    metrics.decisionQuality = Math.min(metrics.decisionQuality + successRate * 10, 100);
    metrics.stability = Math.min(metrics.stability + successRate * 5, 100);
    return metrics;
  }
  /**
   * Avalia se passa na certificação
   */
  private evaluatePass(metrics: TrustMetrics): boolean {
    const average = (
      metrics.reliability +
      metrics.stability +
      metrics.compliance +
      metrics.quality +
      metrics.learningCapacity +
      metrics.decisionQuality
    ) / 6;
    return average >= 65;
  }
  /**
   * Gera razão para a certificação
   */
  private generateReason(metrics: TrustMetrics, passed: boolean): string {
    const avg = (
      metrics.reliability +
      metrics.stability +
      metrics.compliance +
      metrics.quality +
      metrics.learningCapacity +
      metrics.decisionQuality
    ) / 6;
    if (passed) {
      return `Competence certified with average score ${avg.toFixed(1)}%. Metrics: reliability ${metrics.reliability}%, stability ${metrics.stability}%, compliance ${metrics.compliance}%, quality ${metrics.quality}%, learning ${metrics.learningCapacity}%, decision ${metrics.decisionQuality}%.`;
    }
    
    const weaknesses = [];
    if (metrics.reliability < 60) weaknesses.push('reliability');
    if (metrics.stability < 60) weaknesses.push('stability');
    if (metrics.compliance < 60) weaknesses.push('compliance');
    if (metrics.quality < 60) weaknesses.push('quality');
    if (metrics.learningCapacity < 60) weaknesses.push('learning capacity');
    if (metrics.decisionQuality < 60) weaknesses.push('decision quality');
    return `Competence failed certification. Weak areas: ${weaknesses.join(', ')}. Average score: ${avg.toFixed(1)}% (threshold: 65%).`;
  }
  /**
   * Calcula taxa de sucesso do histórico
   */
  private calculateSuccessRate(history: Competence['history']): number {
    const successful = history.filter(
      (h) => h.action === 'Certified' || h.action === 'Approved' || h.result.includes('success')
    ).length;
    return history.length > 0 ? successful / history.length : 0;
  }
  /**
   * Verifica se há degradação significativa nas métricas
   */
  private isDegrading(metrics: TrustMetrics): boolean {
    const avg = (
      metrics.reliability +
      metrics.stability +
      metrics.compliance +
      metrics.quality +
      metrics.learningCapacity +
      metrics.decisionQuality
    ) / 6;
    return avg < 50;
  }
  /**
   * Calcula score de confiança
   */
  private calculateTrustScore(metrics: TrustMetrics): number {
    return (
      metrics.reliability * 0.25 +
      metrics.stability * 0.15 +
      metrics.compliance * 0.20 +
      metrics.quality * 0.15 +
      metrics.learningCapacity * 0.10 +
      metrics.decisionQuality * 0.15
    );
  }
}
