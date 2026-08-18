import { EventEmitter } from 'events';
import { getGlobalLogger } from '@network-agents/observability';
import { ArchitectureCouncil, ArchitectureProposal } from './ArchitectureCouncil';
import { TokenEconomy } from '../economy/TokenEconomy';
import { SelfAwareness } from '../observability/SelfAwareness';
import { OpportunityRadar } from '../opportunity/OpportunityRadar';
import { SecurityManager } from '../security/SecurityManager';

export interface CouncilDecision {
  id: string;
  council: 'architecture' | 'evolution' | 'efficiency';
  proposalId: string;
  decision: 'approved' | 'rejected' | 'deferred';
  reasoning: string;
  timestamp: Date;
  metadata: Record<string, any>;
}

export class CouncilsOrchestrator extends EventEmitter {
  private logger = getGlobalLogger();
  private decisions: Map<string, CouncilDecision> = new Map();

  constructor(
    private architectureCouncil: ArchitectureCouncil,
    private tokenEconomy: TokenEconomy,
    private selfAwareness: SelfAwareness,
    private opportunityRadar: OpportunityRadar,
    _securityManager: SecurityManager
  ) {
    super();
    this.logger.info('[CouncilsOrchestrator] Initialized');
  }

  // ===== P-010: Conselho de Arquitetura =====

  /**
   * Submete uma proposta ao Conselho de Arquitetura
   */
  async submitToArchitectureCouncil(proposal: Omit<ArchitectureProposal, 'id' | 'status' | 'createdAt'>): Promise<{
    proposal: ArchitectureProposal;
    decision: CouncilDecision;
  }> {
    this.logger.info(`[CouncilsOrchestrator] Submitting to Architecture Council: ${proposal.title}`);

    // 1. Submete proposta
    const submitted = this.architectureCouncil.submitProposal(proposal);

    // 2. Verifica compliance constitucional
    const compliance = await this.architectureCouncil.checkConstitutionalCompliance(submitted);

    if (!compliance.compliant) {
      const decision: CouncilDecision = {
        id: `dec_${Date.now()}_${Math.random().toString(36).slice(2, 6)}`,
        council: 'architecture',
        proposalId: submitted.id,
        decision: 'rejected',
        reasoning: `Violações constitucionais: ${compliance.violations.join(', ')}`,
        timestamp: new Date(),
        metadata: { violations: compliance.violations },
      };
      this.decisions.set(decision.id, decision);
      this.emit('council:architecture:rejected', decision);
      return { proposal: submitted, decision };
    }

    // 3. Revisa a proposta
    const reviewed = await this.architectureCouncil.reviewProposal(
      submitted.id,
      'system',
      true,
      'Aprovado pelo Conselho de Arquitetura'
    );

    const decision: CouncilDecision = {
      id: `dec_${Date.now()}_${Math.random().toString(36).slice(2, 6)}`,
      council: 'architecture',
      proposalId: submitted.id,
      decision: reviewed.status === 'approved' ? 'approved' : 'rejected',
      reasoning: reviewed.decisionReason || 'Decisão do conselho',
      timestamp: new Date(),
      metadata: { reviewed },
    };

    this.decisions.set(decision.id, decision);
    this.emit('council:architecture:decision', decision);

    return { proposal: submitted, decision };
  }

  // ===== P-011: Conselho de Evolução Tecnológica =====

  /**
   * Analisa novas tecnologias e tendências
   */
  async analyzeTechnologyTrends(): Promise<{
    trends: Array<{
      name: string;
      description: string;
      potential: number;
      risk: number;
      recommendation: 'adopt' | 'evaluate' | 'monitor' | 'ignore';
    }>;
    decisions: CouncilDecision[];
  }> {
    this.logger.info('[CouncilsOrchestrator] Analyzing technology trends');

    const trends: Array<{
      name: string;
      description: string;
      potential: number;
      risk: number;
      recommendation: 'adopt' | 'evaluate' | 'monitor' | 'ignore';
    }> = [];

    const decisions: CouncilDecision[] = [];

    // 1. Busca oportunidades do radar
    const opportunities = this.opportunityRadar.getOpportunities({
      source: 'github',
      status: 'new',
    });

    for (const opp of opportunities.slice(0, 5)) {
      // Análise de cada oportunidade
      const risk = this.assessTechnologyRisk(opp);
      const potential = opp.potential || 50;

      let recommendation: 'adopt' | 'evaluate' | 'monitor' | 'ignore' = 'monitor';
      if (potential > 80 && risk < 30) {
        recommendation = 'adopt';
      } else if (potential > 60 && risk < 50) {
        recommendation = 'evaluate';
      } else if (potential > 40) {
        recommendation = 'monitor';
      } else {
        recommendation = 'ignore';
      }

      trends.push({
        name: opp.title,
        description: opp.description,
        potential,
        risk,
        recommendation,
      });

      // Registra decisão
      const decision: CouncilDecision = {
        id: `dec_${Date.now()}_${Math.random().toString(36).slice(2, 6)}`,
        council: 'evolution',
        proposalId: opp.id,
        decision: recommendation === 'adopt' ? 'approved' : 'deferred',
        reasoning: `Tecnologia ${opp.title}: potencial ${potential}%, risco ${risk}%`,
        timestamp: new Date(),
        metadata: { opportunity: opp, recommendation },
      };
      decisions.push(decision);
      this.decisions.set(decision.id, decision);
    }

    this.emit('council:evolution:analysis', { trends, decisions });

    return { trends, decisions };
  }

  /**
   * Avalia risco de uma tecnologia
   */
  private assessTechnologyRisk(opportunity: any): number {
    let risk = 30; // Base

    // Tecnologias não maduras aumentam risco
    if (opportunity.metadata?.stars && opportunity.metadata.stars < 100) {
      risk += 20;
    }

    // Poucas atualizações aumentam risco
    if (opportunity.metadata?.lastUpdate) {
      const daysSinceUpdate = (Date.now() - new Date(opportunity.metadata.lastUpdate).getTime()) / (1000 * 60 * 60 * 24);
      if (daysSinceUpdate > 180) risk += 20;
    }

    // Muitas dependências aumentam risco
    if (opportunity.technologies && opportunity.technologies.length > 3) {
      risk += 10;
    }

    return Math.min(risk, 100);
  }

  // ===== P-012: Conselho de Eficiência Cognitiva =====

  /**
   * Analisa eficiência da plataforma
   */
  async analyzeEfficiency(): Promise<{
    metrics: {
      tokenEfficiency: number;
      costEfficiency: number;
      reusability: number;
      autonomy: number;
      overall: number;
    };
    recommendations: string[];
    decisions: CouncilDecision[];
  }> {
    this.logger.info('[CouncilsOrchestrator] Analyzing efficiency');

    const state = this.selfAwareness.getState();
    const decisions: CouncilDecision[] = [];

    // Calcula métricas
    const costReport = this.tokenEconomy.getCostReport();

    const tokenEfficiency = costReport.efficiency || 50;
    const costEfficiency = costReport.totalCost > 0 ? 100 - (costReport.totalCost / 1000) * 10 : 50;
    const reusability = this.calculateReusability(state);
    const autonomy = this.calculateAutonomy(state);
    const overall = (tokenEfficiency + costEfficiency + reusability + autonomy) / 4;

    // Gera recomendações
    const recommendations: string[] = [];

    if (tokenEfficiency < 50) {
      recommendations.push('Consumo de tokens acima do esperado. Otimizar prompts e usar cache.');
    }

    if (costEfficiency < 50) {
      recommendations.push('Custos elevados. Revisar modelo de IA e reduzir chamadas desnecessárias.');
    }

    if (reusability < 50) {
      recommendations.push('Baixa reutilização de capacidades. Incentivar reuso e criar catálogo.');
    }

    if (autonomy < 50) {
      recommendations.push('Baixa autonomia. Implementar mais automações e reduzir intervenção humana.');
    }

    // Registra decisões
    const decision: CouncilDecision = {
      id: `dec_${Date.now()}_${Math.random().toString(36).slice(2, 6)}`,
      council: 'efficiency',
      proposalId: 'efficiency_analysis',
      decision: overall > 70 ? 'approved' : 'deferred',
      reasoning: `Eficiência geral: ${overall.toFixed(1)}%`,
      timestamp: new Date(),
      metadata: {
        tokenEfficiency,
        costEfficiency,
        reusability,
        autonomy,
        overall,
        recommendations,
      },
    };
    decisions.push(decision);
    this.decisions.set(decision.id, decision);

    this.emit('council:efficiency:analysis', { metrics: { tokenEfficiency, costEfficiency, reusability, autonomy, overall }, recommendations });

    return {
      metrics: { tokenEfficiency, costEfficiency, reusability, autonomy, overall },
      recommendations,
      decisions,
    };
  }

  /**
   * Calcula índice de reutilização
   */
  private calculateReusability(state: any): number {
    if (!state) return 50;
    const total = state.capabilities?.total || 100;
    const reused = state.capabilities?.reused || 50;
    return total > 0 ? (reused / total) * 100 : 50;
  }

  /**
   * Calcula índice de autonomia
   */
  private calculateAutonomy(state: any): number {
    if (!state) return 50;
    const health = state.health || {};
    const operational = health.operational || 50;
    const governance = health.governance || 50;
    return (operational + governance) / 2;
  }

  /**
   * Obtém decisões por conselho
   */
  getDecisionsByCouncil(council: 'architecture' | 'evolution' | 'efficiency'): CouncilDecision[] {
    return Array.from(this.decisions.values()).filter(
      (d) => d.council === council
    );
  }

  /**
   * Obtém decisão por ID
   */
  getDecision(id: string): CouncilDecision | undefined {
    return this.decisions.get(id);
  }

  /**
   * Obtém estatísticas dos conselhos
   */
  getStats(): {
    architecture: { total: number; approved: number; rejected: number };
    evolution: { total: number; approved: number; rejected: number };
    efficiency: { total: number; approved: number; rejected: number };
  } {
    const architecture = this.getDecisionsByCouncil('architecture');
    const evolution = this.getDecisionsByCouncil('evolution');
    const efficiency = this.getDecisionsByCouncil('efficiency');

    return {
      architecture: {
        total: architecture.length,
        approved: architecture.filter((d) => d.decision === 'approved').length,
        rejected: architecture.filter((d) => d.decision === 'rejected').length,
      },
      evolution: {
        total: evolution.length,
        approved: evolution.filter((d) => d.decision === 'approved').length,
        rejected: evolution.filter((d) => d.decision === 'rejected').length,
      },
      efficiency: {
        total: efficiency.length,
        approved: efficiency.filter((d) => d.decision === 'approved').length,
        rejected: efficiency.filter((d) => d.decision === 'rejected').length,
      },
    };
  }
}
