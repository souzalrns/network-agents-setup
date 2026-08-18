import { getGlobalLogger } from '@network-agents/observability';
import { ArchitectureCouncil, ArchitectureProposal } from './ArchitectureCouncil';
import { OpportunityRadar } from '../opportunity/OpportunityRadar';
import { TokenEconomy } from '../economy/TokenEconomy';
import { TrustManager } from './TrustManager';

// P-010/011/012: Conselhos especializados — Arquitetura (submissão),
// Evolução Tecnológica (análise de tendências a partir do Radar de
// Oportunidades) e Eficiência Cognitiva (score de token/custo/reuso/
// autonomia).

export interface TechnologyTrendReport {
  trends: Array<{ source: string; potential: number; distance: number; recommendation: string }>;
  summary: string;
  generatedAt: Date;
}

export interface CognitiveEfficiencyReport {
  tokenEfficiency: number;
  costEfficiency: number;
  reuseScore: number;
  autonomyScore: number;
  overall: number;
  recommendations: string[];
  generatedAt: Date;
}

export class CouncilsOrchestrator {
  private logger = getGlobalLogger();

  constructor(
    private architectureCouncil: ArchitectureCouncil,
    private opportunityRadar: OpportunityRadar,
    private tokenEconomy: TokenEconomy,
    private trustManager: TrustManager
  ) {}

  // ===== Conselho de Arquitetura =====

  submitToArchitectureCouncil(
    proposal: Omit<ArchitectureProposal, 'id' | 'status' | 'createdAt'>
  ): ArchitectureProposal {
    this.logger.info(`[CouncilsOrchestrator] Submetendo proposta ao Conselho de Arquitetura: ${proposal.title}`);
    return this.architectureCouncil.submitProposal(proposal);
  }

  // ===== Conselho de Evolução Tecnológica (P-011) =====

  async analyzeTechnologyTrends(): Promise<TechnologyTrendReport> {
    const opportunities = this.opportunityRadar.getOpportunities({ status: 'new' });
    const trends = opportunities.slice(0, 10).map((o: any) => ({
      source: o.source || o.title || 'unknown',
      potential: o.potential ?? 0,
      distance: o.distance ?? 0,
      recommendation:
        (o.potential ?? 0) > 70 && (o.distance ?? 100) < 40
          ? 'Avaliar adoção prioritária'
          : 'Monitorar evolução',
    }));

    const summary =
      trends.length > 0
        ? `${trends.length} tendência(s) tecnológica(s) identificada(s), sendo ${
            trends.filter((t) => t.recommendation.includes('prioritária')).length
          } de alta prioridade.`
        : 'Nenhuma tendência tecnológica relevante identificada no momento.';

    return { trends, summary, generatedAt: new Date() };
  }

  // ===== Conselho de Eficiência Cognitiva (P-012) =====

  async analyzeCognitiveEfficiency(): Promise<CognitiveEfficiencyReport> {
    const costReport = this.tokenEconomy.getCostReport();
    const tokenEfficiency = Math.max(0, 100 - (costReport.efficiency || 0));
    const costEfficiency = costReport.totalCost > 0 ? Math.min(100, (1 / costReport.totalCost) * 1000) : 100;

    const certified = this.trustManager.getCertifiedCompetences();
    const autonomyScore = certified.length > 0
      ? certified.reduce((sum, c) => sum + this.trustLevelScore(c.trustLevel), 0) / certified.length
      : 0;

    // Reuso é aproximado pela proporção de economia (savings) já obtida via reuso
    const reuseScore = costReport.totalTokens > 0 ? Math.min(100, (costReport.savings || 0) > 0 ? 70 : 40) : 50;

    const overall = tokenEfficiency * 0.3 + costEfficiency * 0.25 + reuseScore * 0.2 + autonomyScore * 0.25;

    const recommendations: string[] = [];
    if (tokenEfficiency < 50) recommendations.push('Consumo de tokens acima do ideal — considerar otimizações de cache/compressão.');
    if (autonomyScore < 40) recommendations.push('Poucas competências certificadas em níveis avançados de autonomia.');
    if (reuseScore < 50) recommendations.push('Baixo reuso de capacidades existentes — reforçar pesquisa antes da construção (P-056).');

    return {
      tokenEfficiency,
      costEfficiency,
      reuseScore,
      autonomyScore,
      overall,
      recommendations,
      generatedAt: new Date(),
    };
  }

  private trustLevelScore(level: string): number {
    const map: Record<string, number> = {
      level_0: 0,
      level_1: 20,
      level_2: 40,
      level_3: 60,
      level_4: 80,
      level_5: 100,
    };
    return map[level] ?? 0;
  }
}
