import { EventEmitter } from 'events';
import { getGlobalLogger } from '@network-agents/observability';
import { SelfAwareness } from './SelfAwareness';
import { TokenEconomy } from '../economy/TokenEconomy';
import { ImmunologicalMemory } from '../immunity/ImmunologicalMemory';
import { CognitiveRepository } from '../knowledge/CognitiveRepository';

export interface DashboardMetric {
  id: string;
  name: string;
  value: number;
  unit: string;
  trend: 'up' | 'down' | 'stable';
  change: number; // percentual
  threshold?: number;
  status: 'healthy' | 'warning' | 'critical';
  timestamp: Date;
}

export interface DashboardPanel {
  id: string;
  title: string;
  type: 'metric' | 'chart' | 'table' | 'status';
  metrics: DashboardMetric[];
  config: {
    refreshInterval: number;
    showTrend: boolean;
    showThreshold: boolean;
  };
}

export class MetricsDashboard extends EventEmitter {
  private logger = getGlobalLogger();
  private panels: Map<string, DashboardPanel> = new Map();
  private metrics: Map<string, DashboardMetric> = new Map();
  // Nota de fidelidade: no material original o setInterval abaixo era criado
  // sem nunca ser armazenado/limpo (vazamento de timer, impedindo o processo
  // de encerrar de forma limpa). Adicionado o handle + stop() para corrigir,
  // seguindo o mesmo padrão já usado em WorkerSupervisor e OpportunityRadar.
  private updateInterval: NodeJS.Timeout | null = null;

  constructor(
    private selfAwareness: SelfAwareness,
    private tokenEconomy: TokenEconomy,
    private immunologicalMemory: ImmunologicalMemory,
    private cognitiveRepository: CognitiveRepository
  ) {
    super();
    this.logger.info('[MetricsDashboard] Initialized');
    this.initializeDefaultPanels();
  }

  /**
   * Inicializa painéis padrão
   */
  private initializeDefaultPanels(): void {
    // P-080: Indicadores de Saúde Organizacional
    const healthPanel: DashboardPanel = {
      id: 'health_panel',
      title: 'Saúde Organizacional',
      type: 'status',
      metrics: [],
      config: {
        refreshInterval: 60,
        showTrend: true,
        showThreshold: true,
      },
    };

    // P-082: Dashboard de Métricas
    const metricsPanel: DashboardPanel = {
      id: 'metrics_panel',
      title: 'Métricas da Plataforma',
      type: 'chart',
      metrics: [],
      config: {
        refreshInterval: 30,
        showTrend: true,
        showThreshold: true,
      },
    };

    this.panels.set('health_panel', healthPanel);
    this.panels.set('metrics_panel', metricsPanel);

    // Inicia atualização automática
    this.updateInterval = setInterval(() => this.updateMetrics(), 60000);
    this.updateMetrics();

    this.logger.info('[MetricsDashboard] Default panels initialized');
  }

  /**
   * Atualiza todas as métricas
   */
  async updateMetrics(): Promise<void> {
    const state = this.selfAwareness.getState();

    // P-080: Indicadores de Saúde
    const healthMetrics = this.getHealthMetrics(state);
    for (const metric of healthMetrics) {
      this.metrics.set(metric.id, metric);
    }

    // P-082: Métricas da Plataforma
    const platformMetrics = this.getPlatformMetrics();
    for (const metric of platformMetrics) {
      this.metrics.set(metric.id, metric);
    }

    // Atualiza painéis
    this.updatePanels();

    this.emit('metrics:updated', Array.from(this.metrics.values()));
  }

  /**
   * Obtém métricas de saúde (P-080)
   */
  private getHealthMetrics(state: any): DashboardMetric[] {
    const health = state?.health || {
      operational: 50,
      architectural: 50,
      cognitive: 50,
      economic: 50,
      governance: 50,
      evolutionary: 50,
      overall: 50,
    };

    return [
      {
        id: 'health_operational',
        name: 'Saúde Operacional',
        value: health.operational || 50,
        unit: '%',
        trend: 'stable',
        change: 0,
        threshold: 70,
        status: this.getStatus(health.operational || 50),
        timestamp: new Date(),
      },
      {
        id: 'health_architectural',
        name: 'Saúde Arquitetural',
        value: health.architectural || 50,
        unit: '%',
        trend: 'stable',
        change: 0,
        threshold: 70,
        status: this.getStatus(health.architectural || 50),
        timestamp: new Date(),
      },
      {
        id: 'health_cognitive',
        name: 'Saúde Cognitiva',
        value: health.cognitive || 50,
        unit: '%',
        trend: 'stable',
        change: 0,
        threshold: 70,
        status: this.getStatus(health.cognitive || 50),
        timestamp: new Date(),
      },
      {
        id: 'health_economic',
        name: 'Saúde Econômica',
        value: health.economic || 50,
        unit: '%',
        trend: 'stable',
        change: 0,
        threshold: 70,
        status: this.getStatus(health.economic || 50),
        timestamp: new Date(),
      },
      {
        id: 'health_governance',
        name: 'Saúde da Governança',
        value: health.governance || 50,
        unit: '%',
        trend: 'stable',
        change: 0,
        threshold: 70,
        status: this.getStatus(health.governance || 50),
        timestamp: new Date(),
      },
      {
        id: 'health_evolutionary',
        name: 'Saúde Evolutiva',
        value: health.evolutionary || 50,
        unit: '%',
        trend: 'stable',
        change: 0,
        threshold: 70,
        status: this.getStatus(health.evolutionary || 50),
        timestamp: new Date(),
      },
      {
        id: 'health_overall',
        name: 'Saúde Geral',
        value: health.overall || 50,
        unit: '%',
        trend: 'stable',
        change: 0,
        threshold: 70,
        status: this.getStatus(health.overall || 50),
        timestamp: new Date(),
      },
    ];
  }

  /**
   * Obtém métricas da plataforma (P-082)
   */
  private getPlatformMetrics(): DashboardMetric[] {
    const costReport = this.tokenEconomy.getCostReport();
    const immunologyStats = this.immunologicalMemory.getStats();
    const repositoryStats = this.cognitiveRepository.getStats();

    return [
      {
        id: 'metrics_tokens',
        name: 'Tokens Consumidos',
        value: costReport.totalTokens || 0,
        unit: 'tokens',
        trend: 'stable',
        change: 0,
        threshold: 1000000,
        status: (costReport.totalTokens || 0) < 1000000 ? 'healthy' : 'warning',
        timestamp: new Date(),
      },
      {
        id: 'metrics_cost',
        name: 'Custo Total',
        value: costReport.totalCost || 0,
        unit: '€',
        trend: 'stable',
        change: 0,
        threshold: 100,
        status: (costReport.totalCost || 0) < 100 ? 'healthy' : 'warning',
        timestamp: new Date(),
      },
      {
        id: 'metrics_efficiency',
        name: 'Eficiência de Tokens',
        value: costReport.efficiency || 50,
        unit: '%',
        trend: 'stable',
        change: 0,
        threshold: 70,
        status: this.getStatus(costReport.efficiency || 50),
        timestamp: new Date(),
      },
      {
        id: 'metrics_immunology_entropy',
        name: 'Entropia Cognitiva',
        value: immunologyStats.entropy || 0,
        unit: '%',
        trend: 'down',
        change: 0,
        threshold: 50,
        status: (immunologyStats.entropy || 0) < 50 ? 'healthy' : 'warning',
        timestamp: new Date(),
      },
      {
        id: 'metrics_repository_assets',
        name: 'Ativos Cognitivos',
        value: repositoryStats.totalAssets || 0,
        unit: 'itens',
        trend: 'up',
        change: 0,
        threshold: 10,
        status: (repositoryStats.totalAssets || 0) > 10 ? 'healthy' : 'warning',
        timestamp: new Date(),
      },
      {
        id: 'metrics_repository_reusability',
        name: 'Reusabilidade Média',
        value: repositoryStats.avgReusability || 0,
        unit: '%',
        trend: 'stable',
        change: 0,
        threshold: 70,
        status: this.getStatus(repositoryStats.avgReusability || 0),
        timestamp: new Date(),
      },
    ];
  }

  /**
   * Atualiza os painéis
   */
  private updatePanels(): void {
    const allMetrics = Array.from(this.metrics.values());

    // Health Panel
    const healthPanel = this.panels.get('health_panel');
    if (healthPanel) {
      healthPanel.metrics = allMetrics.filter((m) => m.id.startsWith('health_'));
      this.panels.set('health_panel', healthPanel);
    }

    // Metrics Panel
    const metricsPanel = this.panels.get('metrics_panel');
    if (metricsPanel) {
      metricsPanel.metrics = allMetrics.filter((m) => m.id.startsWith('metrics_'));
      this.panels.set('metrics_panel', metricsPanel);
    }
  }

  /**
   * Obtém status baseado no valor
   */
  private getStatus(value: number): 'healthy' | 'warning' | 'critical' {
    if (value >= 80) return 'healthy';
    if (value >= 50) return 'warning';
    return 'critical';
  }

  /**
   * Obtém painel por ID
   */
  getPanel(id: string): DashboardPanel | undefined {
    return this.panels.get(id);
  }

  /**
   * Obtém todos os painéis
   */
  getPanels(): DashboardPanel[] {
    return Array.from(this.panels.values());
  }

  /**
   * Obtém métrica por ID
   */
  getMetric(id: string): DashboardMetric | undefined {
    return this.metrics.get(id);
  }

  /**
   * Obtém todas as métricas
   */
  getMetrics(): DashboardMetric[] {
    return Array.from(this.metrics.values());
  }

  /**
   * Gera relatório de dashboard
   */
  generateReport(): string {
    const metrics = this.getMetrics();
    const healthMetrics = metrics.filter((m) => m.id.startsWith('health_'));
    const platformMetrics = metrics.filter((m) => m.id.startsWith('metrics_'));

    const lines: string[] = [];
    lines.push('='.repeat(60));
    lines.push('📊 RELATÓRIO DE DASHBOARD');
    lines.push(`Data: ${new Date().toISOString()}`);
    lines.push('='.repeat(60));
    lines.push('');

    lines.push('❤️ SAÚDE ORGANIZACIONAL (P-080)');
    for (const metric of healthMetrics) {
      const status = metric.status === 'healthy' ? '✅' : metric.status === 'warning' ? '⚠️' : '❌';
      lines.push(`  ${status} ${metric.name}: ${metric.value.toFixed(1)}%`);
    }
    lines.push('');

    lines.push('📈 MÉTRICAS DA PLATAFORMA (P-082)');
    for (const metric of platformMetrics) {
      const status = metric.status === 'healthy' ? '✅' : metric.status === 'warning' ? '⚠️' : '❌';
      lines.push(`  ${status} ${metric.name}: ${metric.value.toFixed(1)} ${metric.unit}`);
    }
    lines.push('');

    lines.push('='.repeat(60));
    lines.push('FIM DO RELATÓRIO');

    return lines.join('\n');
  }

  /**
   * Para a atualização automática do dashboard
   */
  stop(): void {
    if (this.updateInterval) {
      clearInterval(this.updateInterval);
      this.updateInterval = null;
    }
    this.logger.info('[MetricsDashboard] Stopped');
  }
}
