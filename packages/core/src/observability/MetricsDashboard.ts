import { EventEmitter } from 'events';
import { getGlobalLogger } from '@network-agents/observability';
import { SelfAwareness } from './SelfAwareness';
import { TokenEconomy } from '../economy/TokenEconomy';
import { TrustManager } from '../governance/TrustManager';
import { ImmunologicalMemory } from '../immunity/ImmunologicalMemory';
import { OpportunityRadar } from '../opportunity/OpportunityRadar';

// P-080/082: Dashboard de Métricas — agrega saúde do sistema e métricas
// de plataforma em painéis, com atualização automática opcional e um
// gerador de relatório em texto.

export interface DashboardPanel {
  id: string;
  title: string;
  value: number | string;
  unit?: string;
  status: 'ok' | 'warning' | 'critical';
}

export interface Dashboard {
  panels: DashboardPanel[];
  generatedAt: Date;
}

export class MetricsDashboard extends EventEmitter {
  private logger = getGlobalLogger();
  private refreshInterval?: NodeJS.Timeout;
  private lastDashboard?: Dashboard;

  constructor(
    private selfAwareness: SelfAwareness,
    private tokenEconomy: TokenEconomy,
    private trustManager: TrustManager,
    private immunologicalMemory: ImmunologicalMemory,
    private opportunityRadar?: OpportunityRadar,
    private config: { autoRefreshMs?: number } = {}
  ) {
    super();
    if (this.config.autoRefreshMs && this.config.autoRefreshMs > 0) {
      this.refreshInterval = setInterval(() => this.getDashboard(), this.config.autoRefreshMs);
    }
  }

  getDashboard(): Dashboard {
    const state = this.selfAwareness.getState();
    const health = (state as any)?.health?.overall ?? (state as any)?.health ?? 0;
    const costReport = this.tokenEconomy.getCostReport();
    const immunityStats = this.immunologicalMemory.getStats();
    const certified = this.trustManager.getCertifiedCompetences();
    const opportunities = this.opportunityRadar?.getOpportunities({ status: 'new' }).length ?? 0;

    const panels: DashboardPanel[] = [
      {
        id: 'health',
        title: 'Saúde do Sistema',
        value: typeof health === 'number' ? Number(health.toFixed(1)) : health,
        unit: '%',
        status: typeof health === 'number' ? (health >= 70 ? 'ok' : health >= 40 ? 'warning' : 'critical') : 'ok',
      },
      {
        id: 'total_tokens',
        title: 'Tokens Consumidos',
        value: costReport.totalTokens,
        status: 'ok',
      },
      {
        id: 'total_cost',
        title: 'Custo Total',
        value: Number(costReport.totalCost.toFixed(4)),
        unit: 'USD',
        status: 'ok',
      },
      {
        id: 'efficiency',
        title: 'Eficiência de Orçamento',
        value: Number((costReport.efficiency || 0).toFixed(1)),
        unit: '%',
        status: (costReport.efficiency || 0) < 90 ? 'ok' : 'warning',
      },
      {
        id: 'certified_competences',
        title: 'Competências Certificadas',
        value: certified.length,
        status: 'ok',
      },
      {
        id: 'immunity_events',
        title: 'Eventos Registrados (Memória Imunológica)',
        value: immunityStats.totalEvents ?? 0,
        status: 'ok',
      },
      {
        id: 'opportunities',
        title: 'Oportunidades Novas',
        value: opportunities,
        status: 'ok',
      },
    ];

    const dashboard: Dashboard = { panels, generatedAt: new Date() };
    this.lastDashboard = dashboard;
    this.logger.debug('[MetricsDashboard] Dashboard atualizado');
    this.emit('dashboard:updated', dashboard);
    return dashboard;
  }

  /**
   * Retorna o último dashboard calculado, sem recalcular (útil para
   * consumidores que só precisam do snapshot mais recente).
   */
  getLastDashboard(): Dashboard | undefined {
    return this.lastDashboard;
  }

  generateTextReport(): string {
    const dashboard = this.getDashboard();
    const lines = [
      '=== Relatório de Métricas da Plataforma ===',
      `Gerado em: ${dashboard.generatedAt.toISOString()}`,
      '',
    ];
    for (const panel of dashboard.panels) {
      lines.push(`- ${panel.title}: ${panel.value}${panel.unit ? ' ' + panel.unit : ''} [${panel.status}]`);
    }
    return lines.join('\n');
  }

  stop(): void {
    if (this.refreshInterval) {
      clearInterval(this.refreshInterval);
      this.refreshInterval = undefined;
    }
  }
}
