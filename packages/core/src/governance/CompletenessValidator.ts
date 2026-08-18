import { EventEmitter } from 'events';
import { getGlobalLogger } from '@network-agents/observability';
export interface Capability {
  id: string;
  name: string;
  type: 'rag' | 'vector_store' | 'knowledge_base' | 'pipeline' | 'agent' | 'skill' | 'mcp' | 'workflow';
  status: 'structure_created' | 'empty' | 'partially_filled' | 'operational' | 'learning' | 'specialist' | 'reference' | 'legacy';
  completeness: number; // 0-100
  contentSize?: number;
  lastIngestion?: Date;
  requiredContentTypes: string[];
  currentContentTypes: string[];
  validationRules: string[];
  metadata: Record<string, any>;
}
export interface IngestionTask {
  id: string;
  capabilityId: string;
  source: string;
  contentType: string;
  status: 'pending' | 'in_progress' | 'completed' | 'failed';
  startedAt?: Date;
  completedAt?: Date;
  error?: string;
  result?: string;
}
export class CompletenessValidator extends EventEmitter {
  private capabilities: Map<string, Capability> = new Map();
  private ingestionTasks: Map<string, IngestionTask> = new Map();
  private logger = getGlobalLogger();
  constructor(private config: {
    minCompletenessForOperational?: number;
    autoIngestEnabled?: boolean;
  } = {}) {
    super();
    this.config.minCompletenessForOperational = config.minCompletenessForOperational || 80;
    this.config.autoIngestEnabled = config.autoIngestEnabled !== false;
  }
  /**
   * Registra uma nova capacidade
   */
  registerCapability(capability: Omit<Capability, 'completeness' | 'status' | 'currentContentTypes'>): Capability {
    const id = `cap_${Date.now()}_${Math.random().toString(36).slice(2, 6)}`;
    
    const fullCapability: Capability = {
      ...capability,
      id,
      completeness: 0,
      status: 'structure_created',
      currentContentTypes: [],
    };
    this.capabilities.set(id, fullCapability);
    this.logger.info(`[CompletenessValidator] Capability registered: ${id} - ${capability.name}`);
    // Verifica se há conteúdo disponível para ingestão imediata
    if (this.config.autoIngestEnabled) {
      this.scheduleAutoIngestion(fullCapability);
    }
    this.emit('capability:registered', fullCapability);
    return fullCapability;
  }
  /**
   * Ingere conteúdo em uma capacidade
   */
  async ingestContent(
    capabilityId: string,
    source: string,
    contentType: string,
    content: any
  ): Promise<IngestionTask> {
    const capability = this.capabilities.get(capabilityId);
    if (!capability) {
      throw new Error(`Capability ${capabilityId} not found`);
    }
    // Verifica se o tipo de conteúdo é suportado
    if (!capability.requiredContentTypes.includes(contentType)) {
      throw new Error(`Content type ${contentType} not supported for ${capabilityId}`);
    }
    const taskId = `ingest_${Date.now()}_${Math.random().toString(36).slice(2, 6)}`;
    const task: IngestionTask = {
      id: taskId,
      capabilityId,
      source,
      contentType,
      status: 'in_progress',
      startedAt: new Date(),
    };
    this.ingestionTasks.set(taskId, task);
    this.emit('ingestion:started', task);
    try {
      // Processa a ingestão (simulação)
      await this.processIngestion(capability, content);
      // Atualiza a capacidade
      if (!capability.currentContentTypes.includes(contentType)) {
        capability.currentContentTypes.push(contentType);
      }
      capability.contentSize = (capability.contentSize || 0) + this.getContentSize(content);
      capability.lastIngestion = new Date();
      // Recalcula completude
      capability.completeness = this.calculateCompleteness(capability);
      capability.status = this.determineStatus(capability);
      this.capabilities.set(capabilityId, capability);
      task.status = 'completed';
      task.completedAt = new Date();
      task.result = `Ingested ${this.getContentSize(content)} units of ${contentType}`;
      this.logger.info(`[CompletenessValidator] Ingestion completed for ${capabilityId}`);
      this.emit('ingestion:completed', task);
      this.emit('capability:updated', capability);
      return task;
    } catch (error: any) {
      task.status = 'failed';
      task.error = error.message;
      this.emit('ingestion:failed', task);
      throw error;
    } finally {
      this.ingestionTasks.set(taskId, task);
    }
  }
  /**
   * Verifica a completude de uma capacidade
   */
  checkCompleteness(capabilityId: string): {
    completeness: number;
    missingContentTypes: string[];
    isOperational: boolean;
    recommendations: string[];
  } {
    const capability = this.capabilities.get(capabilityId);
    if (!capability) {
      throw new Error(`Capability ${capabilityId} not found`);
    }
    const missing = capability.requiredContentTypes.filter(
      (type) => !capability.currentContentTypes.includes(type)
    );
    const isOperational = capability.completeness >= (this.config.minCompletenessForOperational || 80);
    const recommendations: string[] = [];
    if (missing.length > 0) {
      recommendations.push(`Ingerir conteúdo dos tipos: ${missing.join(', ')}`);
    }
    if (capability.completeness < 50) {
      recommendations.push('A capacidade está abaixo de 50% de completude. Considere adicionar mais conteúdo.');
    }
    if (capability.status === 'structure_created') {
      recommendations.push('A capacidade está apenas com estrutura criada. Alimente-a para torná-la operacional.');
    }
    return {
      completeness: capability.completeness,
      missingContentTypes: missing,
      isOperational,
      recommendations,
    };
  }
  /**
   * Obtém todas as capacidades com baixa completude
   */
  getLowCompletenessCapabilities(threshold: number = 50): Capability[] {
    const all = Array.from(this.capabilities.values());
    return all.filter((c) => c.completeness < threshold);
  }
  /**
   * Obtém capacidades vazias (estrutura criada, mas sem conteúdo)
   */
  getEmptyCapabilities(): Capability[] {
    const all = Array.from(this.capabilities.values());
    return all.filter((c) => c.status === 'structure_created' || c.status === 'empty');
  }
  /**
   * Agenda ingestão automática para uma capacidade
   */
  private scheduleAutoIngestion(capability: Capability): void {
    // Verifica se há fontes disponíveis para ingestão
    // Esta é uma implementação simplificada
    this.logger.info(`[CompletenessValidator] Scheduling auto-ingestion for ${capability.id}`);
    
    // Em produção, isso buscaria fontes de dados configuradas
    // e iniciaria a ingestão automaticamente
  }
  /**
   * Processa a ingestão de conteúdo
   */
  private async processIngestion(capability: Capability, content: any): Promise<void> {
    // Simula processamento
    return new Promise((resolve) => {
      setTimeout(resolve, 500);
    });
  }
  /**
   * Calcula a completude da capacidade
   */
  private calculateCompleteness(capability: Capability): number {
    if (capability.requiredContentTypes.length === 0) {
      return 100;
    }
    const present = capability.currentContentTypes.length;
    const required = capability.requiredContentTypes.length;
    const baseScore = (present / required) * 100;
    // Ajusta baseado no tamanho do conteúdo (se disponível)
    let sizeScore = 0;
    if (capability.contentSize && capability.contentSize > 0) {
      sizeScore = Math.min(capability.contentSize / 100, 20);
    }
    return Math.min(baseScore + sizeScore, 100);
  }
  /**
   * Determina o status da capacidade
   */
  private determineStatus(capability: Capability): Capability['status'] {
    const completeness = capability.completeness;
    const threshold = this.config.minCompletenessForOperational || 80;
    if (completeness === 0) {
      return 'structure_created';
    }
    if (completeness < 30) {
      return 'empty';
    }
    if (completeness < threshold) {
      return 'partially_filled';
    }
    if (completeness >= threshold && completeness < 90) {
      return 'operational';
    }
    if (completeness >= 90 && completeness < 95) {
      return 'learning';
    }
    if (completeness >= 95) {
      return 'specialist';
    }
    return 'operational';
  }
  /**
   * Obtém o tamanho do conteúdo (simplificado)
   */
  private getContentSize(content: any): number {
    if (typeof content === 'string') {
      return content.length;
    }
    if (Array.isArray(content)) {
      return content.length;
    }
    if (typeof content === 'object') {
      return Object.keys(content).length;
    }
    return 1;
  }
  /**
   * Obtém todas as capacidades
   */
  getAllCapabilities(): Capability[] {
    return Array.from(this.capabilities.values());
  }
  /**
   * Obtém capacidade por ID
   */
  getCapability(id: string): Capability | undefined {
    return this.capabilities.get(id);
  }
  /**
   * Obtém tarefas de ingestão por capacidade
   */
  getIngestionTasks(capabilityId: string): IngestionTask[] {
    return Array.from(this.ingestionTasks.values()).filter(
      (t) => t.capabilityId === capabilityId
    );
  }
}
