import { getGlobalLogger } from '@network-agents/observability';
import { CompletenessValidator, Capability, IngestionTask } from '../governance/CompletenessValidator';
import { SecurityManager } from '../security/SecurityManager';

// P-018/019: Orquestra a ingestão imediata de conteúdo em capacidades,
// aplicando verificações de segurança (data poisoning / RAG poisoning)
// antes de delegar ao CompletenessValidator, além de planejar a
// ingestão automática das capacidades vazias/incompletas.

export interface AutoIngestionPlan {
  capabilityId: string;
  capabilityName: string;
  missingContentTypes: string[];
  priority: 'low' | 'medium' | 'high';
}

export class IngestionOrchestrator {
  private logger = getGlobalLogger();

  constructor(
    private completenessValidator: CompletenessValidator,
    private securityManager: SecurityManager
  ) {}

  /**
   * Ingestão imediata de conteúdo com verificação de segurança prévia.
   */
  async ingestImmediately(
    capabilityId: string,
    source: string,
    contentType: string,
    content: any
  ): Promise<IngestionTask> {
    const poisoningCheck = this.securityManager.detectDataPoisoning(content);
    if (!poisoningCheck.safe) {
      this.logger.warn(`[IngestionOrchestrator] Ingestão bloqueada por data poisoning: ${poisoningCheck.reason}`);
      throw new Error(`Ingestão bloqueada por segurança: ${poisoningCheck.reason}`);
    }

    if (Array.isArray(content)) {
      const ragCheck = this.securityManager.detectRAGPoisoning(content);
      if (!ragCheck.safe) {
        this.logger.warn(`[IngestionOrchestrator] Ingestão bloqueada por RAG poisoning: ${ragCheck.issues.join(', ')}`);
        throw new Error(`Ingestão bloqueada por RAG poisoning: ${ragCheck.issues.join(', ')}`);
      }
    }

    this.logger.info(`[IngestionOrchestrator] Ingerindo conteúdo em ${capabilityId} a partir de ${source}`);
    return this.completenessValidator.ingestContent(capabilityId, source, contentType, content);
  }

  /**
   * Gera um plano de ingestão automática priorizado para capacidades
   * vazias ou com baixa completude.
   */
  planAutoIngestion(): AutoIngestionPlan[] {
    const empty = this.completenessValidator.getEmptyCapabilities();
    const lowCompleteness = this.completenessValidator.getLowCompletenessCapabilities(70);
    const merged = new Map<string, Capability>();
    [...empty, ...lowCompleteness].forEach((c) => merged.set(c.id, c));

    const plan: AutoIngestionPlan[] = Array.from(merged.values()).map((c) => {
      const missing = c.requiredContentTypes.filter((t) => !c.currentContentTypes.includes(t));
      const priority: 'low' | 'medium' | 'high' =
        c.completeness < 20 ? 'high' : c.completeness < 60 ? 'medium' : 'low';
      return {
        capabilityId: c.id,
        capabilityName: c.name,
        missingContentTypes: missing,
        priority,
      };
    });

    plan.sort((a, b) => this.priorityWeight(b.priority) - this.priorityWeight(a.priority));
    this.logger.info(`[IngestionOrchestrator] Plano de auto-ingestão gerado: ${plan.length} capacidade(s)`);
    return plan;
  }

  private priorityWeight(priority: 'low' | 'medium' | 'high'): number {
    return priority === 'high' ? 3 : priority === 'medium' ? 2 : 1;
  }
}
