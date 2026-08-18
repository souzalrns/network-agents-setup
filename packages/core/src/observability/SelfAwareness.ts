import { EventEmitter } from 'events';
import { getGlobalLogger } from '@network-agents/observability';
export interface OrganizationalState {
  timestamp: Date;
  capabilities: {
    total: number;
    operational: number;
    empty: number;
    partiallyFilled: number;
    learning: number;
    specialist: number;
    legacy: number;
    byDomain: Record<string, number>;
  };
  agents: {
    total: number;
    active: number;
    idle: number;
    error: number;
    byLayer: Record<string, number>;
  };
  costs: {
    totalTokens: number;
    totalCost: number;
    byModel: Record<string, { tokens: number; cost: number }>;
    efficiency: number;
  };
  health: {
    operational: number;
    architectural: number;
    cognitive: number;
    economic: number;
    governance: number;
    evolutionary: number;
    overall: number;
  };
  gaps: Array<{
    id: string;
    description: string;
    domain: string;
    impact: 'low' | 'medium' | 'high';
    urgency: 'low' | 'medium' | 'high';
  }>;
  opportunities: Array<{
    id: string;
    description: string;
    potential: number;
    distance: number;
    priority: 'low' | 'medium' | 'high';
  }>;
  metrics: Record<string, number>;
}
export interface HealthIndicator {
  name: string;
  value: number;
  threshold: number;
  status: 'healthy' | 'warning' | 'critical';
  trend: 'improving' | 'stable' | 'declining';
}
export class SelfAwareness extends EventEmitter {
  private state: OrganizationalState | null = null;
  private healthHistory: OrganizationalState[] = [];
  private logger = getGlobalLogger();
  constructor(private config: {
    updateInterval?: number;
    historySize?: number;
  } = {}) {
    super();
    this.config.updateInterval = config.updateInterval || 60 * 1000; // 1 minuto
    this.config.historySize = config.historySize || 100;
    // Inicia atualização automática
    if (this.config.updateInterval > 0) {
      setInterval(() => this.updateState(), this.config.updateInterval);
    }
    this.logger.info('[SelfAwareness] Initialized');
  }
  /**
   * Atualiza o estado organizacional
   */
  async updateState(): Promise<OrganizationalState> {
    this.logger.debug('[SelfAwareness] Updating organizational state');
    const state: OrganizationalState = {
      timestamp: new Date(),
      capabilities: await this.getCapabilitiesState(),
      agents: await this.getAgentsState(),
      costs: await this.getCostsState(),
      health: await this.getHealthState(),
      gaps: await this.getGaps(),
      opportunities: await this.getOpportunities(),
      metrics: await this.getMetrics(),
    };
    this.state = state;
    this.healthHistory.push(state);
    // Mantém histórico limitado
    if (this.healthHistory.length > (this.config.historySize || 100)) {
      this.healthHistory = this.healthHistory.slice(-(this.config.historySize || 100));
    }
    this.emit('state:updated', state);
    this.logger.debug('[SelfAwareness] State updated');
    return state;
  }
  /**
   * Obtém estado atual
   */
  getState(): OrganizationalState | null {
    return this.state;
  }
  /**
   * Obtém histórico de saúde
   */
  getHealthHistory(limit?: number): OrganizationalState[] {
    const history = this.healthHistory;
    if (limit) {
      return history.slice(-limit);
    }
    return history;
  }
  /**
   * Obtém tendência de saúde
   */
  getHealthTrend(): {
    direction: 'improving' | 'stable' | 'declining';
    rate: number;
    indicators: HealthIndicator[];
  } {
    const history = this.healthHistory;
    if (history.length < 2) {
      return {
        direction: 'stable',
        rate: 0,
        indicators: [],
      };
    }
    const recent = history.slice(-10);
    const oldest = recent[0];
    const latest = recent[recent.length - 1];
    const indicators: HealthIndicator[] = [];
    // Calcula tendência para cada dimensão
    const dimensions = ['operational', 'architectural', 'cognitive', 'economic', 'governance', 'evolutionary'];
    for (const dim of dimensions) {
      const oldValue = oldest.health[dim as keyof typeof oldest.health] || 0;
      const newValue = latest.health[dim as keyof typeof latest.health] || 0;
      const trend = newValue - oldValue;
      const threshold = 70;
      indicators.push({
        name: dim,
        value: newValue,
        threshold,
        status: newValue >= 80 ? 'healthy' : newValue >= 60 ? 'warning' : 'critical',
        trend: trend > 5 ? 'improving' : trend < -5 ? 'declining' : 'stable',
      });
    }
    const overallTrend = (latest.health.overall || 0) - (oldest.health.overall || 0);
    return {
      direction: overallTrend > 2 ? 'improving' : overallTrend < -2 ? 'declining' : 'stable',
      rate: overallTrend,
      indicators,
    };
  }
  /**
   * Obtém recomendações baseadas no estado atual
   */
  getRecommendations(): Array<{
    id: string;
    category: string;
    description: string;
    priority: 'low' | 'medium' | 'high' | 'critical';
    action: string;
  }> {
    const recommendations: Array<{
      id: string;
      category: string;
      description: string;
      priority: 'low' | 'medium' | 'high' | 'critical';
      action: string;
    }> = [];
    if (!this.state) {
      return recommendations;
    }
    // Verifica capacidades vazias
    if (this.state.capabilities.empty > 0) {
      recommendations.push({
        id: `rec_${Date.now()}_1`,
        category: 'capabilities',
        description: `${this.state.capabilities.empty} capacidades estão vazias (estrutura criada sem conteúdo)`,
        priority: this.state.capabilities.empty > 5 ? 'high' : 'medium',
        action: 'Alimentar capacidades vazias com conteúdo relevante',
      });
    }
    // Verifica saúde
    if (this.state.health.overall < 60) {
      recommendations.push({
        id: `rec_${Date.now()}_2`,
        category: 'health',
        description: `Saúde organizacional em ${this.state.health.overall}% (abaixo do recomendado)`,
        priority: 'high',
        action: 'Revisar áreas críticas: ' + Object.entries(this.state.health)
          .filter(([key, value]) => key !== 'overall' && value < 60)
          .map(([key]) => key)
          .join(', '),
      });
    }
    // Verifica gaps
    for (const gap of this.state.gaps) {
      if (gap.urgency === 'high') {
        recommendations.push({
          id: `rec_${Date.now()}_${gap.id}`,
          category: 'gap',
          description: gap.description,
          priority: 'high',
          action: `Endereçar lacuna no domínio ${gap.domain}`,
        });
      }
    }
    // Verifica oportunidades
    const highPotential = this.state.opportunities.filter((o) => o.potential > 80);
    if (highPotential.length > 0) {
      recommendations.push({
        id: `rec_${Date.now()}_opportunities`,
        category: 'opportunity',
        description: `${highPotential.length} oportunidades de alto potencial identificadas`,
        priority: 'medium',
        action: 'Priorizar oportunidades com maior potencial',
      });
    }
    // Verifica custos
    if (this.state.costs.efficiency < 50) {
      recommendations.push({
        id: `rec_${Date.now()}_costs`,
        category: 'costs',
        description: `Eficiência de custos em ${this.state.costs.efficiency}% (baixa)`,
        priority: 'medium',
        action: 'Revisar consumo de tokens e otimizar modelos',
      });
    }
    return recommendations;
  }
  /**
   * Gera relatório de autopercepção
   */
  generateReport(): string {
    if (!this.state) {
      return 'Estado organizacional não disponível';
    }
    const lines: string[] = [];
    lines.push('='.repeat(60));
    lines.push('RELATÓRIO DE AUTOPERCEPÇÃO ORGANIZACIONAL');
    lines.push(`Data: ${this.state.timestamp.toISOString()}`);
    lines.push('='.repeat(60));
    lines.push('');
    // Capacidades
    lines.push('📊 CAPACIDADES');
    lines.push(`  Total: ${this.state.capabilities.total}`);
    lines.push(`  Operacionais: ${this.state.capabilities.operational}`);
    lines.push(`  Vazias: ${this.state.capabilities.empty}`);
    lines.push(`  Parcialmente preenchidas: ${this.state.capabilities.partiallyFilled}`);
    lines.push(`  Em aprendizado: ${this.state.capabilities.learning}`);
    lines.push(`  Especialistas: ${this.state.capabilities.specialist}`);
    lines.push(`  Legado: ${this.state.capabilities.legacy}`);
    lines.push('');
    // Agentes
    lines.push('🤖 AGENTES');
    lines.push(`  Total: ${this.state.agents.total}`);
    lines.push(`  Ativos: ${this.state.agents.active}`);
    lines.push(`  Ociosos: ${this.state.agents.idle}`);
    lines.push(`  Com erro: ${this.state.agents.error}`);
    lines.push('');
    // Saúde
    lines.push('❤️ SAÚDE ORGANIZACIONAL');
    const health = this.state.health;
    lines.push(`  Operacional: ${health.operational}%`);
    lines.push(`  Arquitetural: ${health.architectural}%`);
    lines.push(`  Cognitiva: ${health.cognitive}%`);
    lines.push(`  Econômica: ${health.economic}%`);
    lines.push(`  Governança: ${health.governance}%`);
    lines.push(`  Evolutiva: ${health.evolutionary}%`);
    lines.push(`  Geral: ${health.overall}%`);
    lines.push('');
    // Tendência
    const trend = this.getHealthTrend();
    lines.push('📈 TENDÊNCIA');
    lines.push(`  Direção: ${trend.direction}`);
    lines.push(`  Taxa: ${trend.rate > 0 ? '+' : ''}${trend.rate.toFixed(1)}%`);
    lines.push('');
    // Gaps
    if (this.state.gaps.length > 0) {
      lines.push('⚠️ LACUNAS IDENTIFICADAS');
      for (const gap of this.state.gaps) {
        lines.push(`  - ${gap.description} (${gap.urgency})`);
      }
      lines.push('');
    }
    // Oportunidades
    if (this.state.opportunities.length > 0) {
      lines.push('💡 OPORTUNIDADES');
      for (const opp of this.state.opportunities) {
        lines.push(`  - ${opp.description} (potencial: ${opp.potential}%, distância: ${opp.distance}%)`);
      }
      lines.push('');
    }
    // Recomendações
    const recommendations = this.getRecommendations();
    if (recommendations.length > 0) {
      lines.push('🎯 RECOMENDAÇÕES');
      for (const rec of recommendations) {
        lines.push(`  [${rec.priority}] ${rec.description}`);
        lines.push(`    → ${rec.action}`);
      }
      lines.push('');
    }
    lines.push('='.repeat(60));
    lines.push('FIM DO RELATÓRIO');
    return lines.join('\n');
  }
  /**
   * Obtém estado das capacidades
   */
  private async getCapabilitiesState(): Promise<OrganizationalState['capabilities']> {
    // Em produção, consulta o Catálogo Universal de Capacidades
    return {
      total: 100,
      operational: 65,
      empty: 8,
      partiallyFilled: 12,
      learning: 10,
      specialist: 3,
      legacy: 2,
      byDomain: {
        business: 20,
        medical: 25,
        marketing: 15,
        construction: 18,
        legal: 22,
      },
    };
  }
  /**
   * Obtém estado dos agentes
   */
  private async getAgentsState(): Promise<OrganizationalState['agents']> {
    // Em produção, consulta o status dos agentes
    return {
      total: 50,
      active: 35,
      idle: 12,
      error: 3,
      byLayer: {
        meta: 5,
        horizontal: 15,
        vertical: 30,
      },
    };
  }
  /**
   * Obtém estado de custos
   */
  private async getCostsState(): Promise<OrganizationalState['costs']> {
    // Em produção, consulta o TokenEconomy
    return {
      totalTokens: 1000000,
      totalCost: 10.50,
      byModel: {
        'gpt-4-turbo': { tokens: 400000, cost: 4.00 },
        'gpt-3.5-turbo': { tokens: 300000, cost: 0.60 },
        'claude-3-sonnet': { tokens: 200000, cost: 1.00 },
        'gemini-pro': { tokens: 100000, cost: 0.40 },
      },
      efficiency: 72,
    };
  }
  /**
   * Obtém estado de saúde
   */
  private async getHealthState(): Promise<OrganizationalState['health']> {
    // Em produção, calcula baseado em múltiplos fatores
    const operational = 85;
    const architectural = 78;
    const cognitive = 65;
    const economic = 72;
    const governance = 80;
    const evolutionary = 70;
    return {
      operational,
      architectural,
      cognitive,
      economic,
      governance,
      evolutionary,
      overall: (operational + architectural + cognitive + economic + governance + evolutionary) / 6,
    };
  }
  /**
   * Obtém gaps identificados
   */
  private async getGaps(): Promise<OrganizationalState['gaps']> {
    // Em produção, identifica lacunas automaticamente
    return [
      {
        id: 'gap_001',
        description: 'Capacidade de OCR para notas fiscais portuguesas não implementada',
        domain: 'legal',
        impact: 'high',
        urgency: 'high',
      },
      {
        id: 'gap_002',
        description: 'Memória de longo prazo com RAG não configurada',
        domain: 'general',
        impact: 'medium',
        urgency: 'medium',
      },
      {
        id: 'gap_003',
        description: 'Monitoramento de workers não implementado',
        domain: 'operations',
        impact: 'high',
        urgency: 'high',
      },
    ];
  }
  /**
   * Obtém oportunidades identificadas
   */
  private async getOpportunities(): Promise<OrganizationalState['opportunities']> {
    // Em produção, identifica oportunidades automaticamente
    return [
      {
        id: 'opp_001',
        description: 'Expansão para domínio de seguros',
        potential: 85,
        distance: 40,
        priority: 'high',
      },
      {
        id: 'opp_002',
        description: 'Criação de agente especializado em LGPD/GDPR',
        potential: 80,
        distance: 30,
        priority: 'high',
      },
      {
        id: 'opp_003',
        description: 'Integração com WhatsApp para atendimento',
        potential: 75,
        distance: 50,
        priority: 'medium',
      },
    ];
  }
  /**
   * Obtém métricas
   */
  private async getMetrics(): Promise<Record<string, number>> {
    return {
      responseTime: 1.2,
      tokenEfficiency: 0.8,
      reusability: 0.65,
      autonomy: 0.55,
      reliability: 0.90,
      complexity: 0.30,
    };
  }
}
