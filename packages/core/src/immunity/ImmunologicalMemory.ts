import { EventEmitter } from 'events';
import { getGlobalLogger } from '@network-agents/observability';
export interface ImmunologicalEvent {
  id: string;
  type: 'incident' | 'failure' | 'recovery' | 'vulnerability' | 'attack' | 'anomaly';
  severity: 'low' | 'medium' | 'high' | 'critical';
  description: string;
  rootCause: string;
  impact: {
    components: string[];
    durationMs: number;
    dataLoss: boolean;
    serviceDegradation: boolean;
  };
  response: {
    action: string;
    executedBy: string;
    durationMs: number;
    success: boolean;
  };
  learnings: string[];
  recommendations: string[];
  timestamp: Date;
  resolvedAt?: Date;
  status: 'open' | 'investigating' | 'resolved' | 'archived';
  recurrenceCount: number;
  similarEvents: string[];
  metadata: Record<string, any>;
}
export interface ImmunologicalMemory {
  events: ImmunologicalEvent[];
  patterns: ImmunologicalPattern[];
  antibodies: ImmunologicalAntibody[];
}
export interface ImmunologicalPattern {
  id: string;
  name: string;
  description: string;
  symptoms: string[];
  probability: number;
  severity: 'low' | 'medium' | 'high' | 'critical';
  recommendedAction: string;
  triggeredBy: string[];
  createdAt: Date;
  lastTriggered: Date;
  triggerCount: number;
}
export interface ImmunologicalAntibody {
  id: string;
  name: string;
  description: string;
  targetPattern: string;
  action: string;
  effectiveness: number;
  deployedAt: Date;
  lastUsed: Date;
  useCount: number;
  successRate: number;
  metadata: Record<string, any>;
}
export interface EntropyMetrics {
  totalEntropy: number; // 0-100
  byCategory: {
    duplicateCapabilities: number;
    abandonedAssets: number;
    undocumentedKnowledge: number;
    contradictoryInformation: number;
    obsoleteTechnology: number;
    lostTraceability: number;
    lowReusability: number;
    isolatedKnowledge: number;
  };
  trends: {
    weekly: number;
    monthly: number;
    quarterly: number;
  };
  recommendations: string[];
}
export class ImmunologicalMemory extends EventEmitter {
  private events: Map<string, ImmunologicalEvent> = new Map();
  private patterns: Map<string, ImmunologicalPattern> = new Map();
  private antibodies: Map<string, ImmunologicalAntibody> = new Map();
  private entropyHistory: EntropyMetrics[] = [];
  private logger = getGlobalLogger();
  constructor(private config: {
    maxEvents?: number;
    autoArchiveAfter?: number;
    entropyThreshold?: number;
  } = {}) {
    super();
    this.config.maxEvents = config.maxEvents || 10000;
    this.config.autoArchiveAfter = config.autoArchiveAfter || 90; // dias
    this.config.entropyThreshold = config.entropyThreshold || 50;
    this.logger.info('[ImmunologicalMemory] Initialized');
  }
  // ===== Registro de Eventos =====
  /**
   * Registra um evento imunológico
   */
  registerEvent(data: Omit<ImmunologicalEvent, 'id' | 'timestamp' | 'recurrenceCount' | 'similarEvents'>): ImmunologicalEvent {
    const id = `imm_${Date.now()}_${Math.random().toString(36).slice(2, 6)}`;
    // Verifica se é recorrência
    const similar = this.findSimilarEvents(data);
    const recurrenceCount = similar.length;
    const event: ImmunologicalEvent = {
      ...data,
      id,
      timestamp: new Date(),
      recurrenceCount: recurrenceCount + 1,
      similarEvents: similar.map((e) => e.id),
      status: 'open',
    };
    this.events.set(id, event);
    // Atualiza padrões
    this.updatePatterns(event);
    this.logger.info(`[ImmunologicalMemory] Event registered: ${id} - ${event.type} (${event.severity})`);
    this.emit('event:registered', event);
    // Verifica se precisa criar anticorpo
    if (event.recurrenceCount > 2) {
      this.createAntibody(event);
    }
    return event;
  }
  /**
   * Atualiza um evento
   */
  updateEvent(id: string, updates: Partial<ImmunologicalEvent>): ImmunologicalEvent {
    const event = this.events.get(id);
    if (!event) {
      throw new Error(`Event ${id} not found`);
    }
    // Se está sendo resolvido
    if (updates.status === 'resolved' && !event.resolvedAt) {
      updates.resolvedAt = new Date();
    }
    const updated = { ...event, ...updates };
    this.events.set(id, updated);
    this.emit('event:updated', updated);
    return updated;
  }
  /**
   * Encontra eventos similares
   */
  private findSimilarEvents(data: any): ImmunologicalEvent[] {
    const events = Array.from(this.events.values());
    return events.filter((e) => {
      // Mesmo tipo e severidade similar
      if (e.type !== data.type) return false;
      
      // Mesma causa raiz
      if (e.rootCause === data.rootCause) return true;
      
      // Descrições similares
      const similarity = this.calculateSimilarity(e.description, data.description);
      return similarity > 0.7;
    });
  }
  /**
   * Calcula similaridade entre textos
   */
  private calculateSimilarity(a: string, b: string): number {
    const wordsA = new Set(a.toLowerCase().split(' '));
    const wordsB = new Set(b.toLowerCase().split(' '));
    const intersection = new Set([...wordsA].filter((x) => wordsB.has(x)));
    const union = new Set([...wordsA, ...wordsB]);
    return intersection.size / union.size;
  }
  // ===== Padrões Imunológicos =====
  /**
   * Atualiza padrões baseado em eventos
   */
  private updatePatterns(event: ImmunologicalEvent): void {
    // Procura padrão existente
    let pattern = Array.from(this.patterns.values()).find(
      (p) => p.symptoms.includes(event.type) || p.symptoms.includes(event.rootCause)
    );
    if (pattern) {
      // Atualiza padrão existente
      pattern.lastTriggered = new Date();
      pattern.triggerCount++;
      pattern.probability = Math.min(100, pattern.probability + 5);
      if (!pattern.symptoms.includes(event.description.slice(0, 50))) {
        pattern.symptoms.push(event.description.slice(0, 50));
      }
      this.patterns.set(pattern.id, pattern);
    } else {
      // Cria novo padrão
      const newPattern: ImmunologicalPattern = {
        id: `pat_${Date.now()}_${Math.random().toString(36).slice(2, 6)}`,
        name: `Pattern: ${event.type} - ${event.rootCause}`,
        description: `Padrão identificado a partir de evento ${event.id}`,
        symptoms: [event.type, event.rootCause, event.description.slice(0, 50)],
        probability: 30,
        severity: event.severity,
        recommendedAction: `Investigar e aplicar medidas corretivas para ${event.type}`,
        triggeredBy: [event.id],
        createdAt: new Date(),
        lastTriggered: new Date(),
        triggerCount: 1,
      };
      this.patterns.set(newPattern.id, newPattern);
    }
  }
  /**
   * Obtém padrões ativos
   */
  getActivePatterns(): ImmunologicalPattern[] {
    return Array.from(this.patterns.values()).filter(
      (p) => p.probability > 20 && p.triggerCount > 0
    );
  }
  /**
   * Detecta se um evento corresponde a um padrão
   */
  detectPattern(event: Partial<ImmunologicalEvent>): ImmunologicalPattern | null {
    const patterns = this.getActivePatterns();
    for (const pattern of patterns) {
      const matches = pattern.symptoms.some((symptom) => {
        if (!event.description) return false;
        return event.description.includes(symptom) || symptom.includes(event.type || '');
      });
      if (matches) {
        return pattern;
      }
    }
    return null;
  }
  // ===== Anticorpos =====
  /**
   * Cria um anticorpo para um evento recorrente
   */
  private createAntibody(event: ImmunologicalEvent): ImmunologicalAntibody {
    const antibody: ImmunologicalAntibody = {
      id: `ab_${Date.now()}_${Math.random().toString(36).slice(2, 6)}`,
      name: `Anticorpo para ${event.type}`,
      description: `Resposta automática para ${event.rootCause}`,
      targetPattern: event.rootCause,
      action: this.generateAction(event),
      effectiveness: 60,
      deployedAt: new Date(),
      lastUsed: new Date(),
      useCount: 0,
      successRate: 0,
      metadata: {
        createdFrom: event.id,
        type: event.type,
        severity: event.severity,
      },
    };
    this.antibodies.set(antibody.id, antibody);
    this.logger.info(`[ImmunologicalMemory] Antibody created: ${antibody.id}`);
    this.emit('antibody:created', antibody);
    return antibody;
  }
  /**
   * Gera ação para anticorpo
   */
  private generateAction(event: ImmunologicalEvent): string {
    const actions: Record<string, string> = {
      'incident': 'Isolar componente afetado e iniciar procedimento de recuperação',
      'failure': 'Reiniciar serviço e verificar logs',
      'recovery': 'Validar integridade dos dados e restaurar serviços',
      'vulnerability': 'Aplicar patch de segurança e verificar dependências',
      'attack': 'Bloquear fonte e iniciar investigação forense',
      'anomaly': 'Ajustar thresholds e monitorar comportamento',
    };
    return actions[event.type] || 'Investigar e aplicar medidas corretivas';
  }
  /**
   * Usa um anticorpo
   */
  useAntibody(antibodyId: string, success: boolean): void {
    const antibody = this.antibodies.get(antibodyId);
    if (!antibody) {
      throw new Error(`Antibody ${antibodyId} not found`);
    }
    antibody.lastUsed = new Date();
    antibody.useCount++;
    const totalSuccess = antibody.successRate * (antibody.useCount - 1) + (success ? 100 : 0);
    antibody.successRate = totalSuccess / antibody.useCount;
    antibody.effectiveness = Math.min(100, antibody.effectiveness + (success ? 5 : -5));
    this.antibodies.set(antibodyId, antibody);
    this.emit('antibody:used', { antibodyId, success });
  }
  /**
   * Obtém anticorpos disponíveis
   */
  getAvailableAntibodies(threshold: number = 50): ImmunologicalAntibody[] {
    return Array.from(this.antibodies.values()).filter(
      (a) => a.effectiveness >= threshold
    );
  }
  // ===== Entropia Cognitiva =====
  /**
   * Calcula entropia cognitiva atual
   */
  calculateEntropy(): EntropyMetrics {
    const events = Array.from(this.events.values());
    const totalEvents = events.length;
    // Categorias de entropia
    const duplicateCapabilities = events.filter((e) => e.type === 'incident' && e.description.includes('duplicado')).length;
    const abandonedAssets = events.filter((e) => e.type === 'vulnerability' && e.description.includes('abandonado')).length;
    const undocumentedKnowledge = events.filter((e) => e.type === 'anomaly' && e.description.includes('documentação')).length;
    const contradictoryInformation = events.filter((e) => e.type === 'failure' && e.description.includes('contraditório')).length;
    const obsoleteTechnology = events.filter((e) => e.type === 'vulnerability' && e.description.includes('obsoleto')).length;
    const lostTraceability = events.filter((e) => e.type === 'incident' && e.description.includes('rastreabilidade')).length;
    const lowReusability = events.filter((e) => e.type === 'failure' && e.description.includes('reutilização')).length;
    const isolatedKnowledge = events.filter((e) => e.type === 'anomaly' && e.description.includes('isolado')).length;
    const totalIssues = duplicateCapabilities + abandonedAssets + undocumentedKnowledge + 
                        contradictoryInformation + obsoleteTechnology + lostTraceability + 
                        lowReusability + isolatedKnowledge;
    // Calcula entropia total (0-100)
    const totalEntropy = totalEvents > 0 ? (totalIssues / totalEvents) * 100 : 0;
    // Calcula trends
    const weekly = this.calculateEntropyTrend(7);
    const monthly = this.calculateEntropyTrend(30);
    const quarterly = this.calculateEntropyTrend(90);
    // Gera recomendações
    const recommendations = this.generateEntropyRecommendations({
      duplicateCapabilities,
      abandonedAssets,
      undocumentedKnowledge,
      contradictoryInformation,
      obsoleteTechnology,
      lostTraceability,
      lowReusability,
      isolatedKnowledge,
    });
    return {
      totalEntropy,
      byCategory: {
        duplicateCapabilities,
        abandonedAssets,
        undocumentedKnowledge,
        contradictoryInformation,
        obsoleteTechnology,
        lostTraceability,
        lowReusability,
        isolatedKnowledge,
      },
      trends: { weekly, monthly, quarterly },
      recommendations,
    };
  }
  /**
   * Calcula tendência de entropia
   */
  private calculateEntropyTrend(days: number): number {
    const cutoff = new Date(Date.now() - days * 24 * 60 * 60 * 1000);
    const recent = Array.from(this.events.values()).filter(
      (e) => e.timestamp > cutoff
    );
    if (recent.length === 0) return 0;
    const issues = recent.filter((e) => 
      e.type === 'incident' || e.type === 'failure' || e.type === 'vulnerability'
    ).length;
    return (issues / recent.length) * 100;
  }
  /**
   * Gera recomendações de entropia
   */
  private generateEntropyRecommendations(categories: any): string[] {
    const recommendations: string[] = [];
    if (categories.duplicateCapabilities > 5) {
      recommendations.push('Muitas capacidades duplicadas. Considere consolidar e padronizar.');
    }
    if (categories.abandonedAssets > 3) {
      recommendations.push('Ativos abandonados identificados. Considere revisar e descontinuar.');
    }
    if (categories.undocumentedKnowledge > 5) {
      recommendations.push('Conhecimento não documentado. Considere implementar política de documentação.');
    }
    if (categories.contradictoryInformation > 3) {
      recommendations.push('Informações contraditórias. Considere revisar fontes e validar dados.');
    }
    if (categories.obsoleteTechnology > 2) {
      recommendations.push('Tecnologias obsoletas em uso. Considere plano de atualização.');
    }
    if (categories.lostTraceability > 3) {
      recommendations.push('Perda de rastreabilidade. Considere implementar auditoria contínua.');
    }
    if (categories.lowReusability > 5) {
      recommendations.push('Baixa reutilização. Considere criar catálogo de capacidades reutilizáveis.');
    }
    if (categories.isolatedKnowledge > 3) {
      recommendations.push('Conhecimento isolado. Considere promover compartilhamento entre domínios.');
    }
    if (recommendations.length === 0) {
      recommendations.push('Entropia cognitiva sob controle. Continue monitorando.');
    }
    return recommendations;
  }
  /**
   * Reduz entropia automaticamente
   */
  reduceEntropy(): {
    actions: string[];
    reducedBy: number;
  } {
    const initialEntropy = this.calculateEntropy().totalEntropy;
    const actions: string[] = [];
    // Arquiva eventos antigos
    const cutoff = new Date(Date.now() - (this.config.autoArchiveAfter || 90) * 24 * 60 * 60 * 1000);
    const toArchive = Array.from(this.events.values()).filter(
      (e) => e.timestamp < cutoff && e.status === 'resolved'
    );
    for (const event of toArchive) {
      event.status = 'archived';
      this.events.set(event.id, event);
      actions.push(`Arquivado evento ${event.id}`);
    }
    // Consolida padrões similares
    const patterns = Array.from(this.patterns.values());
    const patternGroups: Record<string, ImmunologicalPattern[]> = {};
    for (const pattern of patterns) {
      const key = pattern.symptoms.slice(0, 2).join('|');
      if (!patternGroups[key]) patternGroups[key] = [];
      patternGroups[key].push(pattern);
    }
    for (const group of Object.values(patternGroups)) {
      if (group.length > 1) {
        const main = group[0];
        for (let i = 1; i < group.length; i++) {
          const toMerge = group[i];
          main.probability = Math.max(main.probability, toMerge.probability);
          main.triggerCount += toMerge.triggerCount;
          main.symptoms = [...new Set([...main.symptoms, ...toMerge.symptoms])];
          this.patterns.delete(toMerge.id);
          actions.push(`Consolidado padrão ${toMerge.id} em ${main.id}`);
        }
        this.patterns.set(main.id, main);
      }
    }
    // Recalcula entropia
    const finalEntropy = this.calculateEntropy().totalEntropy;
    const reducedBy = initialEntropy - finalEntropy;
    this.logger.info(`[ImmunologicalMemory] Entropy reduced by ${reducedBy.toFixed(1)}%`);
    this.emit('entropy:reduced', { initial: initialEntropy, final: finalEntropy, actions });
    return {
      actions,
      reducedBy,
    };
  }
  // ===== Relatórios =====
  /**
   * Gera relatório imunológico completo
   */
  generateReport(): string {
    const events = Array.from(this.events.values());
    const activeEvents = events.filter((e) => e.status === 'open' || e.status === 'investigating');
    const resolvedEvents = events.filter((e) => e.status === 'resolved');
    const archivedEvents = events.filter((e) => e.status === 'archived');
    const patterns = this.getActivePatterns();
    const antibodies = this.getAvailableAntibodies();
    const entropy = this.calculateEntropy();
    const lines: string[] = [];
    lines.push('='.repeat(60));
    lines.push('🛡️ RELATÓRIO IMUNOLÓGICO ORGANIZACIONAL');
    lines.push(`Data: ${new Date().toISOString()}`);
    lines.push('='.repeat(60));
    lines.push('');
    lines.push('📊 EVENTOS');
    lines.push(`  Total: ${events.length}`);
    lines.push(`  Ativos: ${activeEvents.length}`);
    lines.push(`  Resolvidos: ${resolvedEvents.length}`);
    lines.push(`  Arquivados: ${archivedEvents.length}`);
    lines.push('');
    if (activeEvents.length > 0) {
      lines.push('⚠️ EVENTOS ATIVOS');
      for (const event of activeEvents.slice(0, 10)) {
        lines.push(`  [${event.severity}] ${event.type}: ${event.description.slice(0, 60)}...`);
      }
      if (activeEvents.length > 10) {
        lines.push(`  ... e mais ${activeEvents.length - 10} eventos`);
      }
      lines.push('');
    }
    lines.push('📋 PADRÕES');
    lines.push(`  Total: ${patterns.length}`);
    for (const pattern of patterns.slice(0, 5)) {
      lines.push(`  - ${pattern.name} (probabilidade: ${pattern.probability}%)`);
    }
    if (patterns.length > 5) {
      lines.push(`  ... e mais ${patterns.length - 5} padrões`);
    }
    lines.push('');
    lines.push('💉 ANTICORPOS');
    lines.push(`  Total: ${antibodies.length}`);
    for (const ab of antibodies.slice(0, 5)) {
      lines.push(`  - ${ab.name} (eficácia: ${ab.effectiveness}%, usos: ${ab.useCount})`);
    }
    if (antibodies.length > 5) {
      lines.push(`  ... e mais ${antibodies.length - 5} anticorpos`);
    }
    lines.push('');
    lines.push('🌀 ENTROPIA COGNITIVA');
    lines.push(`  Total: ${entropy.totalEntropy.toFixed(1)}%`);
    lines.push(`  Tendência semanal: ${entropy.trends.weekly.toFixed(1)}%`);
    lines.push(`  Tendência mensal: ${entropy.trends.monthly.toFixed(1)}%`);
    lines.push(`  Tendência trimestral: ${entropy.trends.quarterly.toFixed(1)}%`);
    lines.push('');
    lines.push('  Por categoria:');
    lines.push(`    Capacidades duplicadas: ${entropy.byCategory.duplicateCapabilities}`);
    lines.push(`    Ativos abandonados: ${entropy.byCategory.abandonedAssets}`);
    lines.push(`    Conhecimento não documentado: ${entropy.byCategory.undocumentedKnowledge}`);
    lines.push(`    Informações contraditórias: ${entropy.byCategory.contradictoryInformation}`);
    lines.push(`    Tecnologias obsoletas: ${entropy.byCategory.obsoleteTechnology}`);
    lines.push(`    Perda de rastreabilidade: ${entropy.byCategory.lostTraceability}`);
    lines.push(`    Baixa reutilização: ${entropy.byCategory.lowReusability}`);
    lines.push(`    Conhecimento isolado: ${entropy.byCategory.isolatedKnowledge}`);
    lines.push('');
    if (entropy.recommendations.length > 0) {
      lines.push('💡 RECOMENDAÇÕES DE ENTROPIA');
      for (const rec of entropy.recommendations) {
        lines.push(`  • ${rec}`);
      }
      lines.push('');
    }
    lines.push('='.repeat(60));
    lines.push('FIM DO RELATÓRIO');
    return lines.join('\n');
  }
  /**
   * Obtém estatísticas gerais
   */
  getStats(): {
    totalEvents: number;
    activeEvents: number;
    resolvedEvents: number;
    patterns: number;
    antibodies: number;
    entropy: number;
    health: 'healthy' | 'warning' | 'critical';
  } {
    const events = Array.from(this.events.values());
    const active = events.filter((e) => e.status === 'open' || e.status === 'investigating');
    const resolved = events.filter((e) => e.status === 'resolved');
    const entropy = this.calculateEntropy();
    let health: 'healthy' | 'warning' | 'critical' = 'healthy';
    if (entropy.totalEntropy > (this.config.entropyThreshold || 50)) {
      health = 'warning';
    }
    if (entropy.totalEntropy > 80) {
      health = 'critical';
    }
    if (active.length > 10) {
      health = health === 'healthy' ? 'warning' : health;
    }
    if (active.length > 50) {
      health = 'critical';
    }
    return {
      totalEvents: events.length,
      activeEvents: active.length,
      resolvedEvents: resolved.length,
      patterns: this.patterns.size,
      antibodies: this.antibodies.size,
      entropy: entropy.totalEntropy,
      health,
    };
  }
  /**
   * Limpa memória (arquiva eventos antigos)
   */
  cleanup(): void {
    const result = this.reduceEntropy();
    this.logger.info(`[ImmunologicalMemory] Cleanup completed: ${result.actions.length} actions`);
  }
}
