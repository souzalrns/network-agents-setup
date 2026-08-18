import { EventEmitter } from 'events';
import { getGlobalLogger } from '@network-agents/observability';
import { CompletenessValidator } from './CompletenessValidator';
import { ImmunologicalMemory } from '../immunity/ImmunologicalMemory';
import { SelfAwareness } from '../observability/SelfAwareness';
import { SecurityManager } from '../security/SecurityManager';

export interface IngestionPlan {
  capabilityId: string;
  requiredContent: string[];
  priority: 'high' | 'medium' | 'low';
  estimatedTime: number; // minutos
}

export class IngestionOrchestrator extends EventEmitter {
  private logger = getGlobalLogger();

  constructor(
    private completenessValidator: CompletenessValidator,
    private immunologicalMemory: ImmunologicalMemory,
    _selfAwareness: SelfAwareness,
    private securityManager: SecurityManager
  ) {
    super();
    this.logger.info('[IngestionOrchestrator] Initialized');
  }

  /**
   * Alimenta uma capacidade imediatamente (P-018)
   */
  async ingestImmediately(capabilityId: string, source: string, contentType: string, content: any): Promise<void> {
    this.logger.info(`[IngestionOrchestrator] Ingesting immediately: ${capabilityId}`);

    // 1. Verifica segurança do conteúdo
    const securityCheck = this.securityManager.detectDataPoisoning(content);
    if (!securityCheck.safe) {
      this.logger.warn('Content rejected due to security concerns', { reason: securityCheck.reason });
      throw new Error(`Content rejected: ${securityCheck.reason}`);
    }

    // 2. Verifica RAG poisoning
    const ragCheck = this.securityManager.detectRAGPoisoning([content]);
    if (!ragCheck.safe) {
      this.logger.warn('RAG poisoning detected', { issues: ragCheck.issues });
      throw new Error(`RAG poisoning detected: ${ragCheck.issues.join(', ')}`);
    }

    // 3. Realiza a ingestão
    const task = await this.completenessValidator.ingestContent(capabilityId, source, contentType, content);

    // 4. Verifica completude (P-019)
    const completeness = this.completenessValidator.checkCompleteness(capabilityId);

    // 5. Registra na memória imunológica
    if (completeness.isOperational) {
      this.immunologicalMemory.registerEvent({
        type: 'recovery',
        severity: 'low',
        description: `Capability ${capabilityId} successfully ingested and operational`,
        rootCause: 'ingestion_success',
        impact: {
          components: [capabilityId],
          durationMs: 0,
          dataLoss: false,
          serviceDegradation: false,
        },
        response: {
          action: 'ingested',
          executedBy: 'IngestionOrchestrator',
          durationMs: 0,
          success: true,
        },
        learnings: ['Conteúdo ingerido com sucesso'],
        recommendations: ['Monitorar qualidade do conteúdo'],
        status: 'resolved',
        metadata: { capabilityId, contentType, source },
      });
    } else {
      this.immunologicalMemory.registerEvent({
        type: 'vulnerability',
        severity: 'medium',
        description: `Capability ${capabilityId} partially ingested (${completeness.completeness}% complete)`,
        rootCause: 'partial_ingestion',
        impact: {
          components: [capabilityId],
          durationMs: 0,
          dataLoss: false,
          serviceDegradation: true,
        },
        response: {
          action: 'partial_ingestion',
          executedBy: 'IngestionOrchestrator',
          durationMs: 0,
          success: false,
        },
        learnings: ['Conteúdo insuficiente para completude'],
        recommendations: completeness.recommendations,
        status: 'open',
        metadata: { capabilityId, completeness: completeness.completeness },
      });
    }

    this.emit('ingestion:completed', { capabilityId, task, completeness });
  }

  /**
   * Gera plano de ingestão para capacidades vazias
   */
  generateIngestionPlan(): IngestionPlan[] {
    this.logger.info('[IngestionOrchestrator] Generating ingestion plan');

    const emptyCapabilities = this.completenessValidator.getEmptyCapabilities();
    const plans: IngestionPlan[] = [];

    for (const cap of emptyCapabilities) {
      const missingTypes = cap.requiredContentTypes.filter(
        (type) => !cap.currentContentTypes.includes(type)
      );

      // Determina prioridade baseada na criticidade
      let priority: 'high' | 'medium' | 'low' = 'medium';
      if (cap.type === 'knowledge_base' || cap.type === 'rag') {
        priority = 'high';
      }

      // Estima tempo baseado no tipo
      let estimatedTime = 10; // minutos
      if (cap.type === 'knowledge_base') estimatedTime = 30;
      if (cap.type === 'rag') estimatedTime = 45;

      plans.push({
        capabilityId: cap.id,
        requiredContent: missingTypes,
        priority,
        estimatedTime,
      });
    }

    this.emit('ingestion:plan', plans);
    return plans;
  }

  /**
   * Executa plano de ingestão automático
   */
  async executeIngestionPlan(plan: IngestionPlan): Promise<void> {
    this.logger.info(`[IngestionOrchestrator] Executing ingestion plan for ${plan.capabilityId}`);

    // Simula ingestão de conteúdo
    // Em produção, isso buscaria conteúdo de fontes configuradas
    for (const contentType of plan.requiredContent) {
      await this.ingestImmediately(
        plan.capabilityId,
        'auto_source',
        contentType,
        { content: `Auto-ingested ${contentType} content for ${plan.capabilityId}` }
      );
    }

    this.emit('ingestion:plan_executed', plan);
  }

  /**
   * Monitora completude de todas as capacidades
   */
  monitorCompleteness(): {
    total: number;
    operational: number;
    partiallyFilled: number;
    empty: number;
    recommendations: string[];
  } {
    const all = this.completenessValidator.getAllCapabilities();
    const total = all.length;
    const operational = all.filter((c) => c.status === 'operational' || c.status === 'learning' || c.status === 'specialist').length;
    const partiallyFilled = all.filter((c) => c.status === 'partially_filled').length;
    const empty = all.filter((c) => c.status === 'structure_created' || c.status === 'empty').length;

    // Gera recomendações
    const recommendations: string[] = [];
    if (empty > 0) {
      recommendations.push(`${empty} capacidades vazias precisam de conteúdo`);
    }
    if (partiallyFilled > 0) {
      recommendations.push(`${partiallyFilled} capacidades parcialmente preenchidas precisam de mais conteúdo`);
    }
    if (operational < total * 0.5) {
      recommendations.push('Menos de 50% das capacidades estão operacionais');
    }

    return { total, operational, partiallyFilled, empty, recommendations };
  }
}
