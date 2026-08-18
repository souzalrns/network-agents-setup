import { EventEmitter } from 'events';
import { getGlobalLogger } from '@network-agents/observability';
import { SelfAwareness, OrganizationalState } from '../observability/SelfAwareness';
export interface SimulationScenario {
  id: string;
  name: string;
  description: string;
  type: 'architectural' | 'economic' | 'operational' | 'evolutionary' | 'constitutional';
  parameters: Record<string, any>;
  initialState: OrganizationalState;
  duration: number; // em dias simulados
  steps: number;
  status: 'draft' | 'running' | 'completed' | 'failed';
  createdAt: Date;
  completedAt?: Date;
  results?: SimulationResult;
}
export interface SimulationResult {
  success: boolean;
  metrics: {
    finalState: OrganizationalState;
    delta: Record<string, number>;
    roi: number;
    risk: number;
    stability: number;
  };
  events: SimulationEvent[];
  recommendations: string[];
  warnings: string[];
}
export interface SimulationEvent {
  id: string;
  timestamp: Date;
  type: 'change' | 'alert' | 'decision' | 'error';
  description: string;
  impact: number;
  affectedComponents: string[];
}
export interface SimulationAgent {
  id: string;
  name: string;
  role: string;
  decisions: SimulationDecision[];
  performance: number;
}
export interface SimulationDecision {
  id: string;
  agentId: string;
  timestamp: Date;
  decision: string;
  rationale: string;
  alternatives: string[];
  outcome: string;
}
export class OrganizationalSimulator extends EventEmitter {
  private scenarios: Map<string, SimulationScenario> = new Map();
  private runningScenarios: Map<string, { scenario: SimulationScenario; currentStep: number; state: OrganizationalState; events: SimulationEvent[] }> = new Map();
  private logger = getGlobalLogger();
  constructor(
    private selfAwareness: SelfAwareness,
    private config: {
      maxConcurrentSimulations?: number;
      defaultSteps?: number;
    } = {}
  ) {
    super();
    this.config.maxConcurrentSimulations = config.maxConcurrentSimulations || 5;
    this.config.defaultSteps = config.defaultSteps || 100;
    this.logger.info('[OrganizationalSimulator] Initialized');
  }
  /**
   * Cria um novo cenário de simulação
   */
  createScenario(params: {
    name: string;
    description: string;
    type: SimulationScenario['type'];
    parameters: Record<string, any>;
    duration?: number;
    steps?: number;
  }): SimulationScenario {
    const id = `sim_${Date.now()}_${Math.random().toString(36).slice(2, 6)}`;
    
    const initialState = this.selfAwareness.getState();
    if (!initialState) {
      throw new Error('Cannot create simulation without initial state');
    }
    const scenario: SimulationScenario = {
      id,
      name: params.name,
      description: params.description,
      type: params.type,
      parameters: params.parameters,
      initialState: JSON.parse(JSON.stringify(initialState)),
      duration: params.duration || 30, // 30 dias padrão
      steps: params.steps || this.config.defaultSteps || 100,
      status: 'draft',
      createdAt: new Date(),
    };
    this.scenarios.set(id, scenario);
    this.logger.info(`[OrganizationalSimulator] Scenario created: ${id} - ${params.name}`);
    this.emit('scenario:created', scenario);
    return scenario;
  }
  /**
   * Executa uma simulação
   */
  async runSimulation(scenarioId: string): Promise<SimulationResult> {
    const scenario = this.scenarios.get(scenarioId);
    if (!scenario) {
      throw new Error(`Scenario ${scenarioId} not found`);
    }
    if (scenario.status === 'running') {
      throw new Error(`Scenario ${scenarioId} is already running`);
    }
    // Verifica limite de simulações simultâneas
    const running = Array.from(this.runningScenarios.keys());
    if (running.length >= (this.config.maxConcurrentSimulations || 5)) {
      throw new Error(`Maximum concurrent simulations reached (${this.config.maxConcurrentSimulations})`);
    }
    scenario.status = 'running';
    this.scenarios.set(scenarioId, scenario);
    this.logger.info(`[OrganizationalSimulator] Starting simulation: ${scenarioId}`);
    const result = await this.executeSimulation(scenario);
    scenario.status = 'completed';
    scenario.completedAt = new Date();
    scenario.results = result;
    this.scenarios.set(scenarioId, scenario);
    this.logger.info(`[OrganizationalSimulator] Simulation completed: ${scenarioId}`);
    this.emit('simulation:completed', { scenarioId, result });
    return result;
  }
  /**
   * Executa a simulação propriamente dita
   */
  private async executeSimulation(scenario: SimulationScenario): Promise<SimulationResult> {
    const state = JSON.parse(JSON.stringify(scenario.initialState));
    const events: SimulationEvent[] = [];
    const decisions: SimulationDecision[] = [];
    const agents: SimulationAgent[] = this.createSimulationAgents(scenario);
    const totalSteps = scenario.steps;
    this.logger.info(`[OrganizationalSimulator] Executing ${totalSteps} steps for ${scenario.id}`);
    // Simula evolução passo a passo
    for (let step = 0; step < totalSteps; step++) {
      // Atualiza estado
      this.updateState(state, scenario, step);
      // Processa decisões dos agentes
      for (const agent of agents) {
        const decision = await this.agentDecision(agent, state, scenario, step);
        if (decision) {
          decisions.push(decision);
          
          // Aplica impacto da decisão
          this.applyDecision(state, decision, scenario);
          
          // Registra evento
          events.push({
            id: `evt_${Date.now()}_${step}_${agent.id}`,
            timestamp: new Date(),
            type: 'decision',
            description: `${agent.name} decidiu: ${decision.decision}`,
            impact: this.calculateDecisionImpact(decision),
            affectedComponents: [agent.role],
          });
        }
      }
      // Verifica eventos críticos
      const criticalEvents = this.detectCriticalEvents(state, scenario);
      for (const event of criticalEvents) {
        events.push(event);
        this.emit('simulation:event', { scenarioId: scenario.id, step, event });
      }
      // Progresso (para feedback)
      if (step % 10 === 0) {
        this.emit('simulation:progress', {
          scenarioId: scenario.id,
          step,
          totalSteps,
          progress: (step / totalSteps) * 100,
        });
      }
    }
    // Calcula métricas finais
    const finalState = this.selfAwareness.getState();
    if (!finalState) {
      throw new Error('Failed to get final state');
    }
    const metrics = this.calculateMetrics(scenario.initialState, state, events, decisions);
    return {
      success: metrics.stability > 0.5,
      metrics: {
        finalState: state as OrganizationalState,
        delta: this.calculateDelta(scenario.initialState, state),
        roi: metrics.roi,
        risk: metrics.risk,
        stability: metrics.stability,
      },
      events,
      recommendations: this.generateRecommendations(metrics, events),
      warnings: this.generateWarnings(events, metrics),
    };
  }
  /**
   * Cria agentes de simulação
   */
  private createSimulationAgents(_scenario: SimulationScenario): SimulationAgent[] {
    const agentRoles = ['CEO', 'CTO', 'CFO', 'COO', 'CMO', 'CLO'];
    
    return agentRoles.map((role, index) => ({
      id: `sim_agent_${index}`,
      name: `Agente ${role}`,
      role,
      decisions: [],
      performance: 70 + Math.random() * 20,
    }));
  }
  /**
   * Atualiza estado da simulação
   */
  private updateState(state: any, _scenario: SimulationScenario, step: number): void {
    // Simula evolução natural do estado
    // Em produção, implementaria modelos mais complexos
    // Flutuação aleatória controlada
    const noise = (Math.random() - 0.5) * 5;
    // Ajusta saúde baseado no cenário
    const healthDeltas: Record<string, number> = {};
    const dimensions = ['operational', 'architectural', 'cognitive', 'economic', 'governance', 'evolutionary'];
    for (const dim of dimensions) {
      const current = state.health[dim] || 50;
      const delta = (Math.random() - 0.5) * 3;
      healthDeltas[dim] = Math.max(0, Math.min(100, current + delta + noise));
    }
    // Atualiza saúde geral
    const overall = Object.values(healthDeltas).reduce((a: number, b: number) => a + b, 0) / dimensions.length;
    healthDeltas.overall = overall;
    // Aplica com base no cenário
    const factor = 0.1; // taxa de atualização
    for (const dim of dimensions) {
      state.health[dim] = state.health[dim] * (1 - factor) + healthDeltas[dim] * factor;
    }
    state.health.overall = (Object.values(state.health) as number[]).reduce((a: number, b: number) => a + b, 0) / dimensions.length;
    // Atualiza timestamp
    state.timestamp = new Date();
    // Atualiza capacidades
    if (step % 10 === 0) {
      const change = Math.random() - 0.5;
      state.capabilities.total = Math.max(10, state.capabilities.total + Math.round(change * 5));
    }
  }
  /**
   * Decisão de um agente da simulação
   */
  private async agentDecision(
    agent: SimulationAgent,
    _state: any,
    _scenario: SimulationScenario,
    step: number
  ): Promise<SimulationDecision | null> {
    // Simula decisões baseadas no tipo de agente e estado atual
    const decisionChance = 0.3 + (agent.performance / 100) * 0.3;
    
    if (Math.random() > decisionChance) {
      return null;
    }
    const decisions: Record<string, string[]> = {
      CEO: [
        'Expandir para novo domínio',
        'Reduzir custos operacionais',
        'Aumentar investimento em inovação',
        'Reorganizar estrutura organizacional',
      ],
      CTO: [
        'Atualizar arquitetura para nova tecnologia',
        'Implementar nova capacidade de IA',
        'Melhorar observabilidade',
        'Refatorar módulo crítico',
      ],
      CFO: [
        'Otimizar consumo de tokens',
        'Reduzir custos de infraestrutura',
        'Investir em novas ferramentas',
        'Revisar contratos com fornecedores',
      ],
      COO: [
        'Automatizar processo operacional',
        'Melhorar gestão de workers',
        'Implementar nova política de SLAs',
        'Otimizar fluxo de trabalho',
      ],
      CMO: [
        'Lançar campanha de marketing',
        'Criar novo conteúdo estratégico',
        'Expandir presença em redes sociais',
        'Melhorar posicionamento SEO',
      ],
      CLO: [
        'Revisar política de compliance',
        'Atualizar contratos e termos',
        'Implementar novas medidas de LGPD/GDPR',
        'Auditar processos legais',
      ],
    };
    const options = decisions[agent.role] || ['Manter estratégia atual'];
    const decision = options[Math.floor(Math.random() * options.length)];
    const alternatives = options.filter((d) => d !== decision);
    return {
      id: `dec_${Date.now()}_${step}_${agent.id}`,
      agentId: agent.id,
      timestamp: new Date(),
      decision,
      rationale: `Baseado no estado atual e nas tendências observadas.`,
      alternatives,
      outcome: 'pending',
    };
  }
  /**
   * Aplica decisão ao estado
   */
  private applyDecision(state: any, decision: SimulationDecision, _scenario: SimulationScenario): void {
    // Aplica impacto da decisão ao estado simulado
    const impact = 0.1; // impacto percentual
    // Diferentes decisões afetam diferentes métricas
    if (decision.decision.includes('expandir')) {
      state.health.operational *= (1 + impact);
      state.health.cognitive *= (1 + impact * 0.5);
    } else if (decision.decision.includes('reduzir custos')) {
      state.health.economic *= (1 + impact * 0.8);
      state.health.operational *= (1 - impact * 0.3);
    } else if (decision.decision.includes('arquitetura')) {
      state.health.architectural *= (1 + impact * 0.7);
      state.health.cognitive *= (1 + impact * 0.5);
    } else if (decision.decision.includes('otimizar')) {
      state.health.economic *= (1 + impact * 0.6);
      state.health.operational *= (1 + impact * 0.4);
    } else if (decision.decision.includes('automatizar')) {
      state.health.operational *= (1 + impact * 0.9);
      state.health.economic *= (1 + impact * 0.3);
    }
    // Limita valores entre 0 e 100
    for (const key of ['operational', 'architectural', 'cognitive', 'economic', 'governance', 'evolutionary', 'overall']) {
      if (state.health[key]) {
        state.health[key] = Math.max(0, Math.min(100, state.health[key]));
      }
    }
  }
  /**
   * Calcula impacto de uma decisão
   */
  private calculateDecisionImpact(_decision: SimulationDecision): number {
    return 0.5 + Math.random() * 0.5;
  }
  /**
   * Detecta eventos críticos
   */
  private detectCriticalEvents(state: any, _scenario: SimulationScenario): SimulationEvent[] {
    const events: SimulationEvent[] = [];
    // Detecta degradação crítica
    if (state.health.overall < 30) {
      events.push({
        id: `evt_${Date.now()}_critical_degradation`,
        timestamp: new Date(),
        type: 'alert',
        description: 'Degradação crítica da saúde organizacional detectada',
        impact: 1.0,
        affectedComponents: ['all'],
      });
    }
    // Detecta melhora significativa
    if (state.health.overall > 80) {
      events.push({
        id: `evt_${Date.now()}_significant_improvement`,
        timestamp: new Date(),
        type: 'change',
        description: 'Melhora significativa na saúde organizacional',
        impact: 0.5,
        affectedComponents: ['all'],
      });
    }
    return events;
  }
  /**
   * Calcula métricas finais
   */
  private calculateMetrics(
    initialState: OrganizationalState,
    finalState: any,
    events: SimulationEvent[],
    _decisions: SimulationDecision[]
  ): {
    roi: number;
    risk: number;
    stability: number;
  } {
    const initialHealth = initialState.health.overall || 50;
    const finalHealth = finalState.health?.overall || 50;
    const improvement = finalHealth - initialHealth;
    const roi = Math.max(0, improvement / 10); // ROI simplificado
    const risk = Math.min(1, events.filter((e) => e.type === 'alert').length / 20);
    const stability = Math.max(0, 1 - (events.length / 100));
    return { roi, risk, stability };
  }
  /**
   * Calcula delta entre estados
   */
  private calculateDelta(initial: OrganizationalState, final: any): Record<string, number> {
    const delta: Record<string, number> = {};
    // Saúde
    if (initial.health && final.health) {
      for (const key of ['operational', 'architectural', 'cognitive', 'economic', 'governance', 'evolutionary', 'overall']) {
        const initialValue = initial.health[key as keyof typeof initial.health] || 0;
        const finalValue = final.health[key] || 0;
        delta[`health_${key}`] = finalValue - initialValue;
      }
    }
    // Capacidades
    if (initial.capabilities && final.capabilities) {
      for (const key of ['total', 'operational', 'empty', 'partiallyFilled', 'learning', 'specialist', 'legacy']) {
        const initialValue = initial.capabilities[key as keyof typeof initial.capabilities] || 0;
        const finalValue = final.capabilities[key] || 0;
        if (typeof initialValue === 'number' && typeof finalValue === 'number') {
          delta[`capabilities_${key}`] = finalValue - initialValue;
        }
      }
    }
    return delta;
  }
  /**
   * Gera recomendações
   */
  private generateRecommendations(metrics: any, events: SimulationEvent[]): string[] {
    const recommendations: string[] = [];
    if (metrics.roi < 0.5) {
      recommendations.push('Baixo ROI detectado. Considere revisar investimentos e prioridades.');
    }
    if (metrics.risk > 0.6) {
      recommendations.push('Alto risco identificado. Considere implementar medidas de mitigação.');
    }
    if (metrics.stability < 0.5) {
      recommendations.push('Baixa estabilidade organizacional. Considere revisar processos e governança.');
    }
    const alertCount = events.filter((e) => e.type === 'alert').length;
    if (alertCount > 5) {
      recommendations.push(`Muitos alertas (${alertCount}). Considere revisar monitoramento e resiliência.`);
    }
    if (recommendations.length === 0) {
      recommendations.push('Simulação estável. Continue monitorando e ajustando conforme necessário.');
    }
    return recommendations;
  }
  /**
   * Gera avisos
   */
  private generateWarnings(events: SimulationEvent[], metrics: any): string[] {
    const warnings: string[] = [];
    const criticalEvents = events.filter((e) => e.type === 'alert');
    if (criticalEvents.length > 0) {
      for (const event of criticalEvents) {
        warnings.push(`Evento crítico: ${event.description}`);
      }
    }
    if (metrics.stability < 0.3) {
      warnings.push('Estabilidade crítica - sistema pode estar próximo de falha.');
    }
    return warnings;
  }
  /**
   * Obtém cenário por ID
   */
  getScenario(id: string): SimulationScenario | undefined {
    return this.scenarios.get(id);
  }
  /**
   * Obtém todos os cenários
   */
  getScenarios(): SimulationScenario[] {
    return Array.from(this.scenarios.values());
  }
  /**
   * Obtém cenários em execução
   */
  getRunningScenarios(): string[] {
    return Array.from(this.runningScenarios.keys());
  }
  /**
   * Cancela uma simulação em execução
   */
  cancelSimulation(scenarioId: string): void {
    if (!this.runningScenarios.has(scenarioId)) {
      throw new Error(`Scenario ${scenarioId} is not running`);
    }
    this.runningScenarios.delete(scenarioId);
    const scenario = this.scenarios.get(scenarioId);
    if (scenario) {
      scenario.status = 'failed';
      this.scenarios.set(scenarioId, scenario);
      this.logger.info(`[OrganizationalSimulator] Simulation cancelled: ${scenarioId}`);
      this.emit('simulation:cancelled', { scenarioId });
    }
  }
  /**
   * Gera relatório de simulação
   */
  generateReport(scenarioId: string): string {
    const scenario = this.scenarios.get(scenarioId);
    if (!scenario) {
      return `Scenario ${scenarioId} not found`;
    }
    const lines: string[] = [];
    lines.push('='.repeat(60));
    lines.push('📊 RELATÓRIO DE SIMULAÇÃO ORGANIZACIONAL');
    lines.push(`Simulação: ${scenario.name}`);
    lines.push(`ID: ${scenario.id}`);
    lines.push(`Tipo: ${scenario.type}`);
    lines.push(`Status: ${scenario.status}`);
    lines.push(`Duração: ${scenario.duration} dias`);
    lines.push(`Passos: ${scenario.steps}`);
    lines.push(`Criada: ${scenario.createdAt.toISOString()}`);
    if (scenario.completedAt) {
      lines.push(`Concluída: ${scenario.completedAt.toISOString()}`);
    }
    lines.push('='.repeat(60));
    lines.push('');
    if (scenario.results) {
      const result = scenario.results;
      lines.push('📈 RESULTADOS');
      lines.push(`  Sucesso: ${result.success ? '✅ Sim' : '❌ Não'}`);
      lines.push(`  ROI: ${(result.metrics.roi * 100).toFixed(1)}%`);
      lines.push(`  Risco: ${(result.metrics.risk * 100).toFixed(1)}%`);
      lines.push(`  Estabilidade: ${(result.metrics.stability * 100).toFixed(1)}%`);
      lines.push('');
      lines.push('📊 MUDANÇAS');
      for (const [key, value] of Object.entries(result.metrics.delta)) {
        lines.push(`  ${key}: ${value > 0 ? '+' : ''}${value.toFixed(2)}`);
      }
      lines.push('');
      if (result.recommendations.length > 0) {
        lines.push('💡 RECOMENDAÇÕES');
        for (const rec of result.recommendations) {
          lines.push(`  • ${rec}`);
        }
        lines.push('');
      }
      if (result.warnings.length > 0) {
        lines.push('⚠️ AVISOS');
        for (const warn of result.warnings) {
          lines.push(`  • ${warn}`);
        }
        lines.push('');
      }
      if (result.events.length > 0) {
        lines.push(`📋 EVENTOS (${result.events.length})`);
        const topEvents = result.events.slice(-10);
        for (const event of topEvents) {
          lines.push(`  [${event.type}] ${event.description}`);
        }
        if (result.events.length > 10) {
          lines.push(`  ... e mais ${result.events.length - 10} eventos`);
        }
        lines.push('');
      }
    }
    lines.push('='.repeat(60));
    lines.push('FIM DO RELATÓRIO');
    return lines.join('\n');
  }
}
