import { EventEmitter } from 'events';
import { getGlobalLogger } from '@network-agents/observability';
export interface ArchitectureProposal {
  id: string;
  title: string;
  description: string;
  type: 'new_capability' | 'new_agent' | 'new_technology' | 'architecture_change' | 'constitutional_change';
  impact: {
    complexity: 'low' | 'medium' | 'high';
    cost: 'low' | 'medium' | 'high';
    risk: 'low' | 'medium' | 'high';
    reusability: 'low' | 'medium' | 'high';
  };
  dependencies: string[];
  alternatives: string[];
  proposedBy: string;
  createdAt: Date;
  status: 'pending' | 'reviewing' | 'approved' | 'rejected' | 'deferred';
  reviewedBy?: string;
  reviewedAt?: Date;
  decision?: string;
  decisionReason?: string;
}
export interface ArchitectureDecision {
  id: string;
  date: Date;
  context: string;
  decision: string;
  consequences: string[];
  alternatives: string[];
  status: 'active' | 'superseded' | 'deprecated';
}
export class ArchitectureCouncil extends EventEmitter {
  private proposals: Map<string, ArchitectureProposal> = new Map();
  private decisions: Map<string, ArchitectureDecision> = new Map();
  private logger = getGlobalLogger();
  constructor(private config: {
    autoApproveThreshold?: number;
    requireReviewForTypes?: string[];
  } = {}) {
    super();
    this.config.requireReviewForTypes = config.requireReviewForTypes || ['architecture_change', 'constitutional_change'];
    this.config.autoApproveThreshold = config.autoApproveThreshold || 80;
  }
  /**
   * Submete uma proposta para avaliação do conselho
   */
  submitProposal(proposal: Omit<ArchitectureProposal, 'id' | 'status' | 'createdAt'>): ArchitectureProposal {
    const id = `prop_${Date.now()}_${Math.random().toString(36).slice(2, 6)}`;
    const fullProposal: ArchitectureProposal = {
      ...proposal,
      id,
      status: 'pending',
      createdAt: new Date(),
    };
    this.proposals.set(id, fullProposal);
    this.logger.info(`[ArchitectureCouncil] Proposal submitted: ${id} - ${proposal.title}`);
    // Verifica se precisa de revisão
    if (this.requiresReview(fullProposal)) {
      this.emit('proposal:needs-review', fullProposal);
    } else {
      // Auto-approva se for baixo impacto
      this.autoApprove(fullProposal);
    }
    return fullProposal;
  }
  /**
   * Revisa uma proposta (aprovando ou rejeitando)
   */
  reviewProposal(
    proposalId: string,
    reviewer: string,
    approved: boolean,
    reason?: string
  ): ArchitectureProposal {
    const proposal = this.proposals.get(proposalId);
    if (!proposal) {
      throw new Error(`Proposal ${proposalId} not found`);
    }
    if (proposal.status !== 'pending' && proposal.status !== 'reviewing') {
      throw new Error(`Proposal ${proposalId} is not pending or reviewing`);
    }
    proposal.status = approved ? 'approved' : 'rejected';
    proposal.reviewedBy = reviewer;
    proposal.reviewedAt = new Date();
    proposal.decision = approved ? 'approved' : 'rejected';
    proposal.decisionReason = reason || (approved ? 'Approved by council' : 'Rejected by council');
    this.proposals.set(proposalId, proposal);
    this.logger.info(`[ArchitectureCouncil] Proposal ${proposalId} ${approved ? 'approved' : 'rejected'} by ${reviewer}`);
    // Registra a decisão
    if (approved) {
      this.registerDecision({
        id: `dec_${Date.now()}`,
        date: new Date(),
        context: proposal.description,
        decision: `Approved proposal: ${proposal.title}`,
        consequences: this.estimateConsequences(proposal),
        alternatives: proposal.alternatives,
        status: 'active',
      });
    }
    this.emit(`proposal:${proposal.status}`, proposal);
    return proposal;
  }
  /**
   * Registra uma decisão arquitetural (ADR)
   */
  registerDecision(decision: ArchitectureDecision): void {
    this.decisions.set(decision.id, decision);
    this.logger.info(`[ArchitectureCouncil] Decision registered: ${decision.id}`);
    this.emit('decision:registered', decision);
  }
  /**
   * Obtém todas as decisões arquiteturais
   */
  getDecisions(): ArchitectureDecision[] {
    return Array.from(this.decisions.values());
  }
  /**
   * Obtém decisão por ID
   */
  getDecision(id: string): ArchitectureDecision | undefined {
    return this.decisions.get(id);
  }
  /**
   * Obtém todas as propostas
   */
  getProposals(): ArchitectureProposal[] {
    return Array.from(this.proposals.values());
  }
  /**
   * Obtém proposta por ID
   */
  getProposal(id: string): ArchitectureProposal | undefined {
    return this.proposals.get(id);
  }
  /**
   * Obtém propostas pendentes
   */
  getPendingProposals(): ArchitectureProposal[] {
    return Array.from(this.proposals.values()).filter(
      (p) => p.status === 'pending' || p.status === 'reviewing'
    );
  }
  /**
   * Verifica se a proposta precisa de revisão
   */
  private requiresReview(proposal: ArchitectureProposal): boolean {
    // Tipos que exigem revisão obrigatória
    if (this.config.requireReviewForTypes?.includes(proposal.type)) {
      return true;
    }
    // Alto impacto exige revisão
    if (proposal.impact.complexity === 'high' || proposal.impact.cost === 'high' || proposal.impact.risk === 'high') {
      return true;
    }
    // Muitas dependências exige revisão
    if (proposal.dependencies.length > 3) {
      return true;
    }
    return false;
  }
  /**
   * Auto-aprova propostas de baixo impacto
   */
  private autoApprove(proposal: ArchitectureProposal): void {
    // Calcula score de confiança
    const score = this.calculateConfidenceScore(proposal);
    if (score >= (this.config.autoApproveThreshold || 80)) {
      proposal.status = 'approved';
      proposal.reviewedBy = 'system';
      proposal.reviewedAt = new Date();
      proposal.decision = 'approved';
      proposal.decisionReason = 'Auto-approved by system (low impact)';
      this.proposals.set(proposal.id, proposal);
      this.logger.info(`[ArchitectureCouncil] Proposal ${proposal.id} auto-approved (score: ${score})`);
      this.emit('proposal:auto-approved', proposal);
    } else {
      // Baixa confiança, precisa de revisão
      proposal.status = 'reviewing';
      this.proposals.set(proposal.id, proposal);
      this.emit('proposal:needs-review', proposal);
    }
  }
  /**
   * Calcula score de confiança para auto-aprovação
   */
  private calculateConfidenceScore(proposal: ArchitectureProposal): number {
    let score = 50;
    // Impacto baixo aumenta score
    if (proposal.impact.complexity === 'low') score += 15;
    if (proposal.impact.cost === 'low') score += 15;
    if (proposal.impact.risk === 'low') score += 15;
    if (proposal.impact.reusability === 'high') score += 10;
    // Poucas dependências aumenta score
    if (proposal.dependencies.length <= 1) score += 10;
    // Alternativas existentes aumenta score
    if (proposal.alternatives.length > 0) score += 10;
    return Math.min(score, 100);
  }
  /**
   * Estima consequências de uma proposta
   */
  private estimateConsequences(proposal: ArchitectureProposal): string[] {
    const consequences: string[] = [];
    if (proposal.impact.complexity === 'high') {
      consequences.push('Increased architectural complexity');
    }
    if (proposal.impact.cost === 'high') {
      consequences.push('Increased operational costs');
    }
    if (proposal.impact.risk === 'high') {
      consequences.push('Higher risk of architectural drift');
    }
    if (proposal.impact.reusability === 'high') {
      consequences.push('Increased reuse potential across domains');
    }
    if (proposal.dependencies.length > 2) {
      consequences.push('Increased dependency management overhead');
    }
    return consequences;
  }
  /**
   * Verifica se uma proposta está em conformidade com a Constituição
   */
  async checkConstitutionalCompliance(proposal: ArchitectureProposal): Promise<{
    compliant: boolean;
    violations: string[];
  }> {
    const violations: string[] = [];
    // Verifica princípios básicos (exemplo)
    // P-002: Estruturar em camadas
    if (proposal.type === 'architecture_change' && !proposal.description.includes('camada')) {
      violations.push('P-002: Estrutura em camadas não mencionada');
    }
    // P-005: Catálogo Universal de Capacidades
    if (proposal.type === 'new_capability' && !proposal.description.includes('catalog')) {
      violations.push('P-005: Nova capacidade deve ser catalogada');
    }
    // P-056: Pesquisa antes da construção
    if (proposal.alternatives.length === 0) {
      violations.push('P-056: Pesquisa antes da construção - alternativas não avaliadas');
    }
    return {
      compliant: violations.length === 0,
      violations,
    };
  }
}
