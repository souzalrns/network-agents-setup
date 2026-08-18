import { EventEmitter } from 'events';
import { getGlobalLogger } from '@network-agents/observability';
import { SelfAwareness } from '../observability/SelfAwareness';
export interface Opportunity {
  id: string;
  title: string;
  description: string;
  source: 'github' | 'scientific' | 'market' | 'legal' | 'internal' | 'patent';
  category: string;
  potential: number; // 0-100
  distance: number; // 0-100 (distância cognitiva)
  priority: 'low' | 'medium' | 'high' | 'critical';
  roi: number; // estimativa de retorno
  effort: number; // estimativa de esforço
  tags: string[];
  technologies: string[];
  relatedCapabilities: string[];
  createdAt: Date;
  expiresAt?: Date;
  status: 'new' | 'analyzing' | 'validated' | 'pending' | 'implemented' | 'rejected';
  metadata: Record<string, any>;
}
export interface RadarSource {
  id: string;
  name: string;
  type: 'github' | 'arxiv' | 'patent' | 'market_trend' | 'legislation' | 'internal';
  enabled: boolean;
  lastScan: Date;
  config: Record<string, any>;
}
export class OpportunityRadar extends EventEmitter {
  private opportunities: Map<string, Opportunity> = new Map();
  // Público (em vez de privado) para permitir inspeção direta em testes unitários
  // (ex.: tests/unit/OpportunityRadar.test.ts faz `radar.sources.size`).
  public sources: Map<string, RadarSource> = new Map();
  private logger = getGlobalLogger();
  private scanInterval: NodeJS.Timeout | null = null;
  constructor(
    private selfAwareness: SelfAwareness,
    private config: {
      scanInterval?: number;
      minPotential?: number;
      maxDistance?: number;
    } = {}
  ) {
    super();
    this.config.scanInterval = config.scanInterval || 60 * 60 * 1000; // 1 hora
    this.config.minPotential = config.minPotential || 50;
    this.config.maxDistance = config.maxDistance || 70;
    // Registra fontes padrão
    this.registerDefaultSources();
    // Inicia escaneamento automático
    if (this.config.scanInterval > 0) {
      this.scanInterval = setInterval(() => this.scanAll(), this.config.scanInterval);
      // Primeiro scan imediato
      setTimeout(() => this.scanAll(), 5000);
    }
    this.logger.info('[OpportunityRadar] Initialized');
  }
  /**
   * Registra fontes padrão de oportunidades
   */
  private registerDefaultSources(): void {
    const sources: RadarSource[] = [
      {
        id: 'github_trending',
        name: 'GitHub Trending',
        type: 'github',
        enabled: true,
        lastScan: new Date(0),
        config: { topics: ['ai', 'ml', 'agents', 'automation', 'open-source'] },
      },
      {
        id: 'arxiv_papers',
        name: 'ArXiv Papers',
        type: 'arxiv',
        enabled: true,
        lastScan: new Date(0),
        config: { categories: ['cs.AI', 'cs.LG', 'cs.CL', 'cs.MA'] },
      },
      {
        id: 'market_trends',
        name: 'Market Trends',
        type: 'market_trend',
        enabled: true,
        lastScan: new Date(0),
        config: { sources: ['trends', 'reports'] },
      },
      {
        id: 'legislation',
        name: 'Legislation Changes',
        type: 'legislation',
        enabled: true,
        lastScan: new Date(0),
        config: { regions: ['BR', 'PT', 'EU'] },
      },
      {
        id: 'internal_gaps',
        name: 'Internal Gaps',
        type: 'internal',
        enabled: true,
        lastScan: new Date(0),
        config: { categories: ['capability_gaps', 'agent_needs'] },
      },
    ];
    for (const source of sources) {
      this.sources.set(source.id, source);
    }
  }
  /**
   * Escaneia todas as fontes em busca de oportunidades
   */
  async scanAll(): Promise<Opportunity[]> {
    this.logger.info('[OpportunityRadar] Scanning all sources...');
    const allOpportunities: Opportunity[] = [];
    for (const [id, source] of this.sources) {
      if (!source.enabled) continue;
      try {
        const opportunities = await this.scanSource(source);
        for (const opp of opportunities) {
          // Verifica se já existe oportunidade similar
          const existing = this.findSimilar(opp);
          if (existing) {
            // Atualiza potencial e prioridade
            existing.potential = Math.max(existing.potential, opp.potential);
            existing.priority = this.calculatePriority(existing);
            this.opportunities.set(existing.id, existing);
          } else {
            // Calcula prioridade
            opp.priority = this.calculatePriority(opp);
            this.opportunities.set(opp.id, opp);
            allOpportunities.push(opp);
          }
        }
        // Atualiza último scan
        source.lastScan = new Date();
        this.sources.set(id, source);
      } catch (error: any) {
        this.logger.error(`[OpportunityRadar] Error scanning ${source.name}: ${error.message}`);
      }
    }
    // Filtra oportunidades relevantes
    const relevant = this.filterRelevant(allOpportunities);
    this.logger.info(`[OpportunityRadar] Found ${allOpportunities.length} opportunities (${relevant.length} relevant)`);
    this.emit('scan:completed', { opportunities: allOpportunities, relevant });
    return relevant;
  }
  /**
   * Escaneia uma fonte específica
   */
  private async scanSource(source: RadarSource): Promise<Opportunity[]> {
    // Simula escaneamento de diferentes fontes
    // Em produção, implementaria integração real com cada fonte
    const opportunities: Opportunity[] = [];
    switch (source.type) {
      case 'github':
        opportunities.push(...(await this.scanGitHub(source)));
        break;
      case 'arxiv':
        opportunities.push(...(await this.scanArXiv(source)));
        break;
      case 'market_trend':
        opportunities.push(...(await this.scanMarketTrends(source)));
        break;
      case 'legislation':
        opportunities.push(...(await this.scanLegislation(source)));
        break;
      case 'internal':
        opportunities.push(...(await this.scanInternal(source)));
        break;
    }
    return opportunities;
  }
  /**
   * Escaneia GitHub
   */
  private async scanGitHub(_source: RadarSource): Promise<Opportunity[]> {
    // Simulação - em produção, usaria API do GitHub
    return [
      {
        id: `opp_github_${Date.now()}_1`,
        title: 'Novo framework de agentes com MCP',
        description: 'Framework open-source com suporte a Model Context Protocol está ganhando tração',
        source: 'github',
        category: 'technology',
        potential: 85,
        distance: 35,
        priority: 'high',
        roi: 80,
        effort: 60,
        tags: ['mcp', 'agents', 'framework'],
        technologies: ['MCP', 'TypeScript', 'LangGraph'],
        relatedCapabilities: ['agent_orchestration', 'tool_integration'],
        createdAt: new Date(),
        status: 'new',
        metadata: { stars: 2400, forks: 350, lastUpdate: '2026-08-15' },
      },
      {
        id: `opp_github_${Date.now()}_2`,
        title: 'Biblioteca de visão computacional para documentos',
        description: 'Nova biblioteca para extração de dados de documentos com alta precisão',
        source: 'github',
        category: 'technology',
        potential: 70,
        distance: 50,
        priority: 'medium',
        roi: 65,
        effort: 70,
        tags: ['ocr', 'document_processing', 'vision'],
        technologies: ['Python', 'PyTorch', 'DocumentAI'],
        relatedCapabilities: ['ocr', 'document_parsing'],
        createdAt: new Date(),
        status: 'new',
        metadata: { stars: 1800, forks: 120, lastUpdate: '2026-08-10' },
      },
    ];
  }
  /**
   * Escaneia ArXiv
   */
  private async scanArXiv(_source: RadarSource): Promise<Opportunity[]> {
    // Simulação
    return [
      {
        id: `opp_arxiv_${Date.now()}_1`,
        title: 'Agentes autônomos com planejamento hierárquico',
        description: 'Novo paper sobre planejamento hierárquico para agentes autônomos',
        source: 'scientific',
        category: 'research',
        potential: 75,
        distance: 60,
        priority: 'medium',
        roi: 70,
        effort: 80,
        tags: ['planning', 'autonomous', 'hierarchical'],
        technologies: ['Reinforcement Learning', 'Transformers'],
        relatedCapabilities: ['planning', 'agent_autonomy'],
        createdAt: new Date(),
        status: 'new',
        metadata: { authors: ['Smith et al.'], citation: 45 },
      },
    ];
  }
  /**
   * Escaneia tendências de mercado
   */
  private async scanMarketTrends(_source: RadarSource): Promise<Opportunity[]> {
    // Simulação
    return [
      {
        id: `opp_market_${Date.now()}_1`,
        title: 'Crescimento de marketplaces de IA',
        description: 'Mercado de marketplace de agentes de IA crescendo 35% ao ano',
        source: 'market',
        category: 'business',
        potential: 90,
        distance: 45,
        priority: 'high',
        roi: 95,
        effort: 50,
        tags: ['marketplace', 'commercialization'],
        technologies: ['AI Agents', 'APIs'],
        relatedCapabilities: ['agent_registry', 'tool_catalog'],
        createdAt: new Date(),
        status: 'new',
        metadata: { growth: 35, market_size: '1.2B', source: 'Gartner' },
      },
      {
        id: `opp_market_${Date.now()}_2`,
        title: 'Demanda por automação de compliance legal',
        description: 'Empresas buscando automação para LGPD/GDPR',
        source: 'market',
        category: 'business',
        potential: 80,
        distance: 30,
        priority: 'high',
        roi: 85,
        effort: 40,
        tags: ['compliance', 'legal', 'automation'],
        technologies: ['RAG', 'AI Agents'],
        relatedCapabilities: ['legal_research', 'compliance'],
        createdAt: new Date(),
        status: 'new',
        metadata: { market_size: '800M', growth: 28 },
      },
    ];
  }
  /**
   * Escaneia mudanças legislativas
   */
  private async scanLegislation(_source: RadarSource): Promise<Opportunity[]> {
    // Simulação
    return [
      {
        id: `opp_legal_${Date.now()}_1`,
        title: 'Nova lei de proteção de dados na América Latina',
        description: 'Novas regulamentações de proteção de dados criando demanda por consultoria e automação',
        source: 'legal',
        category: 'legislation',
        potential: 75,
        distance: 25,
        priority: 'high',
        roi: 70,
        effort: 35,
        tags: ['data_protection', 'compliance', 'lgpd'],
        technologies: ['AI Agents', 'Document Processing'],
        relatedCapabilities: ['legal_research', 'data_privacy'],
        createdAt: new Date(),
        status: 'new',
        metadata: { effective_date: '2027-01-01', region: 'Latam' },
      },
    ];
  }
  /**
   * Escaneia lacunas internas
   */
  private async scanInternal(_source: RadarSource): Promise<Opportunity[]> {
    const state = this.selfAwareness.getState();
    if (!state) return [];
    const opportunities: Opportunity[] = [];
    // Identifica lacunas baseado no estado
    for (const gap of state.gaps) {
      opportunities.push({
        id: `opp_internal_${Date.now()}_${gap.id}`,
        title: `Resolver lacuna: ${gap.description}`,
        description: gap.description,
        source: 'internal',
        category: 'gap',
        potential: 70 + (gap.impact === 'high' ? 20 : 0),
        distance: 20,
        priority: gap.urgency === 'high' ? 'high' : 'medium',
        roi: 60,
        effort: 30,
        tags: ['internal', 'gap'],
        technologies: [],
        relatedCapabilities: [],
        createdAt: new Date(),
        status: 'new',
        metadata: { gapId: gap.id },
      });
    }
    return opportunities;
  }
  /**
   * Encontra oportunidade similar
   */
  private findSimilar(opportunity: Opportunity): Opportunity | undefined {
    for (const existing of this.opportunities.values()) {
      // Verifica título similar
      const similarity = this.calculateSimilarity(opportunity.title, existing.title);
      if (similarity > 0.7) {
        return existing;
      }
      // Verifica tags similares
      const commonTags = opportunity.tags.filter((t) => existing.tags.includes(t));
      if (commonTags.length >= 2) {
        return existing;
      }
    }
    return undefined;
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
  /**
   * Calcula prioridade baseado em potencial e distância
   */
  private calculatePriority(opportunity: Opportunity): 'low' | 'medium' | 'high' | 'critical' {
    const score = opportunity.potential - opportunity.distance;
    if (score > 60) return 'critical';
    if (score > 40) return 'high';
    if (score > 20) return 'medium';
    return 'low';
  }
  /**
   * Filtra oportunidades relevantes
   */
  private filterRelevant(opportunities: Opportunity[]): Opportunity[] {
    const minPotential = this.config.minPotential || 50;
    const maxDistance = this.config.maxDistance || 70;
    return opportunities.filter(
      (o) => o.potential >= minPotential && o.distance <= maxDistance && o.status === 'new'
    );
  }
  /**
   * Obtém todas as oportunidades
   */
  getOpportunities(filters?: {
    status?: string;
    priority?: string;
    source?: string;
    category?: string;
  }): Opportunity[] {
    let opportunities = Array.from(this.opportunities.values());
    if (filters) {
      if (filters.status) {
        opportunities = opportunities.filter((o) => o.status === filters.status);
      }
      if (filters.priority) {
        opportunities = opportunities.filter((o) => o.priority === filters.priority);
      }
      if (filters.source) {
        opportunities = opportunities.filter((o) => o.source === filters.source);
      }
      if (filters.category) {
        opportunities = opportunities.filter((o) => o.category === filters.category);
      }
    }
    return opportunities.sort((a, b) => b.potential - a.potential);
  }
  /**
   * Obtém oportunidade por ID
   */
  getOpportunity(id: string): Opportunity | undefined {
    return this.opportunities.get(id);
  }
  /**
   * Atualiza status de uma oportunidade
   */
  updateOpportunityStatus(id: string, status: Opportunity['status']): Opportunity {
    const opportunity = this.opportunities.get(id);
    if (!opportunity) {
      throw new Error(`Opportunity ${id} not found`);
    }
    opportunity.status = status;
    this.opportunities.set(id, opportunity);
    this.logger.info(`[OpportunityRadar] Opportunity ${id} status updated to ${status}`);
    this.emit('opportunity:status_changed', { opportunityId: id, status });
    return opportunity;
  }
  /**
   * Adiciona oportunidade manual
   */
  addOpportunity(data: Omit<Opportunity, 'id' | 'priority' | 'status' | 'createdAt'>): Opportunity {
    const id = `opp_manual_${Date.now()}_${Math.random().toString(36).slice(2, 6)}`;
    const opportunity: Opportunity = {
      ...data,
      id,
      priority: this.calculatePriority(data as Opportunity),
      status: 'new',
      createdAt: new Date(),
    };
    this.opportunities.set(id, opportunity);
    this.logger.info(`[OpportunityRadar] Manual opportunity added: ${id}`);
    this.emit('opportunity:added', opportunity);
    return opportunity;
  }
  /**
   * Gera relatório de oportunidades
   */
  generateReport(): string {
    const opportunities = this.getOpportunities();
    const byPriority = {
      critical: opportunities.filter((o) => o.priority === 'critical'),
      high: opportunities.filter((o) => o.priority === 'high'),
      medium: opportunities.filter((o) => o.priority === 'medium'),
      low: opportunities.filter((o) => o.priority === 'low'),
    };
    const byStatus = {
      new: opportunities.filter((o) => o.status === 'new'),
      analyzing: opportunities.filter((o) => o.status === 'analyzing'),
      validated: opportunities.filter((o) => o.status === 'validated'),
      pending: opportunities.filter((o) => o.status === 'pending'),
      implemented: opportunities.filter((o) => o.status === 'implemented'),
      rejected: opportunities.filter((o) => o.status === 'rejected'),
    };
    const lines: string[] = [];
    lines.push('='.repeat(60));
    lines.push('📡 RELATÓRIO DO RADAR DE OPORTUNIDADES');
    lines.push(`Data: ${new Date().toISOString()}`);
    lines.push('='.repeat(60));
    lines.push('');
    lines.push(`Total de oportunidades: ${opportunities.length}`);
    lines.push('');
    lines.push('📊 POR PRIORIDADE');
    lines.push(`  Críticas: ${byPriority.critical.length}`);
    lines.push(`  Alta: ${byPriority.high.length}`);
    lines.push(`  Média: ${byPriority.medium.length}`);
    lines.push(`  Baixa: ${byPriority.low.length}`);
    lines.push('');
    lines.push('📋 POR STATUS');
    lines.push(`  Nova: ${byStatus.new.length}`);
    lines.push(`  Analisando: ${byStatus.analyzing.length}`);
    lines.push(`  Validada: ${byStatus.validated.length}`);
    lines.push(`  Pendente: ${byStatus.pending.length}`);
    lines.push(`  Implementada: ${byStatus.implemented.length}`);
    lines.push(`  Rejeitada: ${byStatus.rejected.length}`);
    lines.push('');
    if (byPriority.critical.length > 0 || byPriority.high.length > 0) {
      lines.push('🎯 PRINCIPAIS OPORTUNIDADES');
      const top = [...byPriority.critical, ...byPriority.high].slice(0, 5);
      for (const opp of top) {
        lines.push(`  [${opp.priority}] ${opp.title}`);
        lines.push(`    Potencial: ${opp.potential}% | Distância: ${opp.distance}% | ROI: ${opp.roi}%`);
        lines.push(`    ${opp.description}`);
        lines.push('');
      }
    }
    lines.push('='.repeat(60));
    lines.push('FIM DO RELATÓRIO');
    return lines.join('\n');
  }
  /**
   * Para o escaneamento automático
   */
  stop(): void {
    if (this.scanInterval) {
      clearInterval(this.scanInterval);
      this.scanInterval = null;
    }
    this.logger.info('[OpportunityRadar] Stopped');
  }
}
