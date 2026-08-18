// packages/core/src/orchestrator/DeliberationOrchestrator.ts
import { EventEmitter } from 'events';
import { getGlobalLogger } from '@network-agents/observability';
import { DeliberationEngine, DeliberationLevel } from '../governance/DeliberationEngine';
import { ArchitectureCouncil } from '../governance/ArchitectureCouncil';
import { SecurityManager } from '../security/SecurityManager';
import { TokenEconomy } from '../economy/TokenEconomy';
import { HitlManager } from '../hitl/HitlManager';
import { HitlCategory, HitlPriority } from '@network-agents/shared';

export interface DeliberationRequest {
  id: string;
  intent: string;
  domain: string;
  input: string;
  context: Record<string, any>;
  criteria: {
    impact: number;
    uncertainty: number;
    risk: number;
    reversibility: number;
    cost: number;
    dependencies: number;
  };
}

export interface DeliberationOutcome {
  approved: boolean;
  level: DeliberationLevel;
  action: string;
  reasoning: string;
  requiresHitl: boolean;
  hitlRequestId?: string;
  metadata: Record<string, any>;
}

export class DeliberationOrchestrator extends EventEmitter {
  private logger = getGlobalLogger();
  private deliberations: Map<string, DeliberationOutcome> = new Map();

  constructor(
    private deliberationEngine: DeliberationEngine,
    private architectureCouncil: ArchitectureCouncil,
    private securityManager: SecurityManager,
    _tokenEconomy: TokenEconomy,
    private hitlManager: HitlManager
  ) {
    super();
    this.logger.info('[DeliberationOrchestrator] Initialized');
  }

  /**
   * Processa uma deliberação completa
   */
  async deliberate(request: DeliberationRequest): Promise<DeliberationOutcome> {
    this.logger.info(`[DeliberationOrchestrator] Deliberating: ${request.id}`);

    // 1. Verifica segurança
    const securityCheck = this.securityManager.detectPromptInjection(request.input);
    if (!securityCheck.safe) {
      this.logger.warn('Security check failed', { reason: securityCheck.reason });
      return {
        approved: false,
        level: DeliberationLevel.OPERATIONAL,
        action: 'blocked',
        reasoning: `Security violation: ${securityCheck.reason}`,
        requiresHitl: false,
        metadata: { blocked: true, reason: securityCheck.reason },
      };
    }

    // 2. Avalia nível de deliberação
    const assessment = this.deliberationEngine.assessLevel({
      intent: request.intent,
      domain: request.domain,
      criteria: request.criteria,
    });

    this.logger.info(`[DeliberationOrchestrator] Assessment: ${assessment.level} (confidence: ${assessment.confidence})`);

    // 3. Escalada inteligente
    const escalation = this.deliberationEngine.escalate({
      intent: request.intent,
      domain: request.domain,
      criteria: request.criteria,
    });

    this.logger.info(`[DeliberationOrchestrator] Escalation: ${escalation.target} (urgency: ${escalation.urgency})`);

    // 4. Aprovação baseada no nível
    let approved = false;
    let reasoning = assessment.reasoning;
    let requiresHitl = false;
    let hitlRequestId: string | undefined;

    switch (assessment.level) {
      case DeliberationLevel.OPERATIONAL:
        // Execução automática
        approved = true;
        reasoning = 'Decisão operacional aprovada automaticamente.';
        break;

      case DeliberationLevel.TACTICAL: {
        // Requer aprovação humana (HITL)
        requiresHitl = true;
        const hitlRequest = await this.hitlManager.requestApproval({
          agentId: 'deliberation_orchestrator',
          domain: request.domain,
          category: HitlCategory.APPROVAL,
          priority: HitlPriority.MEDIUM,
          title: `Aprovação necessária: ${request.intent}`,
          description: `Deliberação tática: ${assessment.suggestedAction}`,
          context: { request, assessment },
          proposedAction: assessment.suggestedAction,
          alternatives: assessment.alternatives,
          risks: ['Impacto moderado'],
          impacts: ['Decisão requer supervisão humana'],
          expiresInMinutes: 60,
          metadata: { deliberationId: request.id },
        });
        hitlRequestId = hitlRequest.id;
        approved = false; // Aguarda aprovação humana
        reasoning = `Aguardando aprovação humana (HITL ${hitlRequest.id})`;
        break;
      }

      case DeliberationLevel.STRATEGIC: {
        // Requer aprovação do Conselho de Arquitetura
        const proposal = this.architectureCouncil.submitProposal({
          title: `Decisão Estratégica: ${request.intent}`,
          description: request.input,
          type: 'architecture_change',
          impact: {
            complexity: 'high',
            cost: 'high',
            risk: 'high',
            reusability: 'medium',
          },
          dependencies: [],
          alternatives: assessment.alternatives,
          proposedBy: 'deliberation_orchestrator',
        });
        approved = proposal.status === 'approved';
        reasoning = proposal.decisionReason || 'Aguardando análise do Conselho de Arquitetura';
        break;
      }

      case DeliberationLevel.CONSTITUTIONAL:
        // Requer processo constitucional formal
        approved = false;
        reasoning = 'Decisão constitucional requer processo formal de reforma.';
        this.emit('constitutional:needed', { request, assessment });
        break;

      default:
        approved = false;
        reasoning = 'Nível de deliberação não reconhecido.';
    }

    // 5. Registra resultado
    const outcome: DeliberationOutcome = {
      approved,
      level: assessment.level,
      action: assessment.suggestedAction,
      reasoning,
      requiresHitl,
      hitlRequestId,
      metadata: {
        requestId: request.id,
        confidence: assessment.confidence,
        escalation: escalation,
        alternatives: assessment.alternatives,
      },
    };

    this.deliberations.set(request.id, outcome);
    this.emit('deliberation:completed', outcome);

    this.logger.info(`[DeliberationOrchestrator] Deliberation completed: ${request.id} (approved: ${approved})`);

    return outcome;
  }

  /**
   * Aprova uma deliberação tática (HITL)
   */
  async approveTactical(requestId: string, responderId: string, comment?: string): Promise<DeliberationOutcome> {
    const outcome = this.deliberations.get(requestId);
    if (!outcome) {
      throw new Error(`Deliberation ${requestId} not found`);
    }

    if (!outcome.hitlRequestId) {
      throw new Error(`Deliberation ${requestId} has no HITL request`);
    }

    await this.hitlManager.approveRequest(outcome.hitlRequestId, responderId, comment);

    outcome.approved = true;
    outcome.reasoning = `Aprovado por ${responderId}: ${comment || 'Sem comentários'}`;
    outcome.requiresHitl = false;

    this.deliberations.set(requestId, outcome);
    this.emit('deliberation:approved', outcome);

    return outcome;
  }

  /**
   * Rejeita uma deliberação tática (HITL)
   */
  async rejectTactical(requestId: string, responderId: string, comment?: string): Promise<DeliberationOutcome> {
    const outcome = this.deliberations.get(requestId);
    if (!outcome) {
      throw new Error(`Deliberation ${requestId} not found`);
    }

    if (!outcome.hitlRequestId) {
      throw new Error(`Deliberation ${requestId} has no HITL request`);
    }

    await this.hitlManager.rejectRequest(outcome.hitlRequestId, responderId, comment);

    outcome.approved = false;
    outcome.reasoning = `Rejeitado por ${responderId}: ${comment || 'Sem comentários'}`;
    outcome.requiresHitl = false;

    this.deliberations.set(requestId, outcome);
    this.emit('deliberation:rejected', outcome);

    return outcome;
  }

  /**
   * Obtém deliberação por ID
   */
  getDeliberation(id: string): DeliberationOutcome | undefined {
    return this.deliberations.get(id);
  }

  /**
   * Obtém estatísticas
   */
  getStats(): {
    total: number;
    approved: number;
    rejected: number;
    pending: number;
  } {
    const deliberations = Array.from(this.deliberations.values());
    const total = deliberations.length;
    const approved = deliberations.filter((d) => d.approved).length;
    const rejected = deliberations.filter((d) => !d.approved && !d.requiresHitl).length;
    const pending = deliberations.filter((d) => d.requiresHitl).length;

    return { total, approved, rejected, pending };
  }
}
