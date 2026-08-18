import { getGlobalLogger } from '@network-agents/observability';
import { DeliberationEngine, DeliberationContext, DeliberationResult } from './DeliberationEngine';
import { ArchitectureCouncil } from './ArchitectureCouncil';
import { SecurityManager } from '../security/SecurityManager';
import { TokenEconomy } from '../economy/TokenEconomy';
import { HitlManager } from '../hitl/HitlManager';

// P-008/009: Orquestra o fluxo completo de deliberação — decide o nível
// (operacional/tático/estratégico/constitucional) e encaminha para o
// destino correto (execução direta, aprovação humana via HITL, ou o
// Conselho de Arquitetura), com checagens de segurança e economia de
// tokens ao longo do caminho.

export interface DeliberationOutcome {
  decision: 'approved' | 'rejected' | 'pending';
  result: DeliberationResult;
  hitlRequestId?: string;
  proposalId?: string;
  reason: string;
}

export class DeliberationOrchestrator {
  private logger = getGlobalLogger();

  constructor(
    private deliberationEngine: DeliberationEngine,
    private architectureCouncil: ArchitectureCouncil,
    private securityManager: SecurityManager,
    private tokenEconomy: TokenEconomy,
    private hitlManager: HitlManager
  ) {}

  /**
   * Delibera sobre uma ação/decisão proposta e a encaminha adequadamente.
   */
  async deliberate(
    context: DeliberationContext,
    proposal?: {
      title: string;
      description: string;
      type: 'new_capability' | 'new_agent' | 'new_technology' | 'architecture_change' | 'constitutional_change';
      agentId: string;
      alternatives?: string[];
      dependencies?: string[];
    }
  ): Promise<DeliberationOutcome> {
    // 1. Verifica segurança do conteúdo da deliberação
    const securityCheck = this.securityManager.detectPromptInjection(context.intent);
    if (!securityCheck.safe) {
      this.logger.warn('[DeliberationOrchestrator] Deliberação bloqueada por questão de segurança');
      return {
        decision: 'rejected',
        result: this.deliberationEngine.assessLevel(context),
        reason: `Bloqueado por segurança: ${securityCheck.reason}`,
      };
    }

    // 2. Avalia o nível de deliberação necessário
    const result = this.deliberationEngine.assessLevel(context);
    this.logger.info(`[DeliberationOrchestrator] Nível avaliado: ${result.level} (score de confiança ${result.confidence})`);

    // 3. Nível operacional — executa diretamente
    if (result.approvalScope === 'none') {
      return { decision: 'approved', result, reason: 'Deliberação operacional, aprovação automática.' };
    }

    // 4. Nível tático — requer aprovação humana (HITL)
    if (result.approvalScope === 'human') {
      const hitlRequest = await this.hitlManager.requestApproval({
        agentId: proposal?.agentId || 'orchestrator',
        domain: context.domain,
        category: 'decision' as any,
        priority: 'medium' as any,
        title: proposal?.title || `Decisão tática: ${context.intent}`,
        description: result.reasoning,
        context: { intent: context.intent, criteria: context.criteria },
        proposedAction: result.suggestedAction,
        alternatives: result.alternatives,
      });
      return {
        decision: 'pending',
        result,
        hitlRequestId: hitlRequest.id,
        reason: 'Aguardando aprovação humana (nível tático).',
      };
    }

    // 5. Nível estratégico ou constitucional — submete ao Conselho de Arquitetura
    const councilProposal = this.architectureCouncil.submitProposal({
      title: proposal?.title || `Decisão estratégica: ${context.intent}`,
      description: proposal?.description || result.reasoning,
      type: proposal?.type || (result.level === 'constitutional' ? 'constitutional_change' : 'architecture_change'),
      impact: {
        complexity: context.criteria.impact >= 7 ? 'high' : context.criteria.impact >= 4 ? 'medium' : 'low',
        cost: context.criteria.cost >= 7 ? 'high' : context.criteria.cost >= 4 ? 'medium' : 'low',
        risk: context.criteria.risk >= 7 ? 'high' : context.criteria.risk >= 4 ? 'medium' : 'low',
        reusability: 'medium',
      },
      dependencies: proposal?.dependencies || [],
      alternatives: proposal?.alternatives || result.alternatives,
      proposedBy: proposal?.agentId || 'orchestrator',
    });

    // Reserva orçamento simbólico para acompanhamento da deliberação
    this.tokenEconomy.allocateBudget(`deliberation_${councilProposal.id}`, 2000);

    return {
      decision: councilProposal.status === 'approved' ? 'approved' : 'pending',
      result,
      proposalId: councilProposal.id,
      reason: `Encaminhado ao Conselho de Arquitetura (status: ${councilProposal.status}).`,
    };
  }
}
