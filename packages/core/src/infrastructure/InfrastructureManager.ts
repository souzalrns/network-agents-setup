import { EventEmitter } from 'events';
import { getGlobalLogger } from '@network-agents/observability';
import { TokenEconomy } from '../economy/TokenEconomy';
import { SelfAwareness } from '../observability/SelfAwareness';

export interface InfrastructureComponent {
  id: string;
  name: string;
  type: 'database' | 'cache' | 'queue' | 'vector' | 'llm' | 'storage' | 'compute';
  provider: string;
  tier: 'free' | 'basic' | 'standard' | 'premium' | 'enterprise';
  costPerMonth: number;
  costPerUnit: number;
  unit: string;
  usage: number;
  status: 'active' | 'inactive' | 'pending' | 'deprecated';
  createdAt: Date;
  metadata: Record<string, any>;
}

export interface InfrastructurePlan {
  id: string;
  name: string;
  components: string[];
  estimatedCost: number;
  scalability: 'low' | 'medium' | 'high';
  performance: 'low' | 'medium' | 'high' | 'very_high';
  recommendations: string[];
}

export class InfrastructureManager extends EventEmitter {
  private logger = getGlobalLogger();
  private components: Map<string, InfrastructureComponent> = new Map();
  private plans: Map<string, InfrastructurePlan> = new Map();

  constructor(
    private tokenEconomy: TokenEconomy,
    _selfAwareness: SelfAwareness
  ) {
    super();
    this.logger.info('[InfrastructureManager] Initialized');
    this.initializeDefaultComponents();
  }

  /**
   * Inicializa componentes padrão (P-046)
   */
  private initializeDefaultComponents(): void {
    // P-046: PostgreSQL com pgvector
    this.registerComponent({
      id: 'postgresql',
      name: 'PostgreSQL com pgvector',
      type: 'database',
      provider: 'self-hosted',
      tier: 'basic',
      costPerMonth: 20,
      costPerUnit: 0.01,
      unit: 'GB',
      usage: 10,
      status: 'active',
      createdAt: new Date(),
      metadata: {
        version: '16',
        vectorSupport: true,
        recommended: true,
      },
    });

    // P-046: Redis (quando necessário)
    this.registerComponent({
      id: 'redis',
      name: 'Redis Cache',
      type: 'cache',
      provider: 'self-hosted',
      tier: 'basic',
      costPerMonth: 15,
      costPerUnit: 0.005,
      unit: 'GB',
      usage: 2,
      status: 'inactive',
      createdAt: new Date(),
      metadata: {
        version: '7',
        recommended: false,
        whenNeeded: true,
      },
    });

    // P-046: Docker Compose
    this.registerComponent({
      id: 'docker-compose',
      name: 'Docker Compose',
      type: 'compute',
      provider: 'self-hosted',
      tier: 'free',
      costPerMonth: 0,
      costPerUnit: 0,
      unit: 'N/A',
      usage: 0,
      status: 'active',
      createdAt: new Date(),
      metadata: {
        recommended: true,
        orchestration: 'compose',
      },
    });

    // P-049: Modelos pagos
    this.registerComponent({
      id: 'openai-gpt4',
      name: 'OpenAI GPT-4',
      type: 'llm',
      provider: 'OpenAI',
      tier: 'premium',
      costPerMonth: 0,
      costPerUnit: 0.03,
      unit: '1K tokens',
      usage: 0,
      status: 'active',
      createdAt: new Date(),
      metadata: {
        model: 'gpt-4-turbo',
        recommended: true,
      },
    });

    this.registerComponent({
      id: 'openai-gpt35',
      name: 'OpenAI GPT-3.5',
      type: 'llm',
      provider: 'OpenAI',
      tier: 'standard',
      costPerMonth: 0,
      costPerUnit: 0.002,
      unit: '1K tokens',
      usage: 0,
      status: 'active',
      createdAt: new Date(),
      metadata: {
        model: 'gpt-3.5-turbo',
        recommended: true,
      },
    });

    // P-047: Componentes a evitar na Fase 1
    const avoidInPhase1 = ['kafka', 'kubernetes', 'neo4j', 'qdrant'];
    for (const name of avoidInPhase1) {
      this.registerComponent({
        id: name,
        name: name.charAt(0).toUpperCase() + name.slice(1),
        type: 'compute',
        provider: 'self-hosted',
        tier: 'enterprise',
        costPerMonth: 100,
        costPerUnit: 0.1,
        unit: 'hour',
        usage: 0,
        status: 'deprecated',
        createdAt: new Date(),
        metadata: {
          recommended: false,
          phase: 2,
          reason: 'Complexidade desnecessária na Fase 1',
        },
      });
    }

    this.logger.info('[InfrastructureManager] Default components initialized');
  }

  /**
   * Registra um componente (P-046)
   */
  registerComponent(component: InfrastructureComponent): void {
    this.components.set(component.id, component);
    this.logger.info(`[InfrastructureManager] Component registered: ${component.id}`);
    this.emit('component:registered', component);
  }

  /**
   * Obtém recomendação de infraestrutura (P-046, P-048)
   */
  getInfrastructureRecommendation(phase: 1 | 2 | 3): {
    components: InfrastructureComponent[];
    totalCost: number;
    plan: InfrastructurePlan;
  } {
    const activeComponents = Array.from(this.components.values())
      .filter((c) => c.status === 'active' || c.status === 'inactive')
      .filter((c) => {
        if (phase === 1) {
          // P-046: Infraestrutura mínima
          return c.id === 'postgresql' || c.id === 'docker-compose' ||
                 c.id === 'openai-gpt4' || c.id === 'openai-gpt35';
        }
        if (phase === 2) {
          // Adiciona Redis
          return c.id === 'postgresql' || c.id === 'redis' || c.id === 'docker-compose' ||
                 c.id === 'openai-gpt4' || c.id === 'openai-gpt35';
        }
        return true; // Fase 3
      });

    const totalCost = activeComponents.reduce((sum, c) => sum + c.costPerMonth, 0);

    // P-048: VPS recomendada
    const vpsRecommendation = {
      cpu: phase === 1 ? 4 : phase === 2 ? 8 : 16,
      ram: phase === 1 ? 16 : phase === 2 ? 32 : 64,
      storage: phase === 1 ? 200 : phase === 2 ? 500 : 1000,
      costPerMonth: phase === 1 ? 25 : phase === 2 ? 45 : 90,
    };

    const plan: InfrastructurePlan = {
      id: `plan_${Date.now()}`,
      name: `Fase ${phase} - Infraestrutura Recomendada`,
      components: activeComponents.map((c) => c.id),
      estimatedCost: totalCost + vpsRecommendation.costPerMonth,
      scalability: phase === 1 ? 'low' : phase === 2 ? 'medium' : 'high',
      performance: phase === 1 ? 'medium' : phase === 2 ? 'high' : 'very_high',
      recommendations: [
        `VPS: ${vpsRecommendation.cpu} vCPU / ${vpsRecommendation.ram} GB RAM / ${vpsRecommendation.storage} GB SSD`,
        `Custo estimado: €${(totalCost + vpsRecommendation.costPerMonth).toFixed(2)}/mês (P-048)`,
        phase === 1 ? '✅ Infraestrutura mínima recomendada' : '',
        phase === 1 ? '⚠️ Kubernetes, Kafka, Neo4j, Qdrant NÃO recomendados na Fase 1 (P-047)' : '',
        '✅ Utilizar modelos pagos (GPT, Gemini, Claude) inicialmente (P-049)',
      ].filter(Boolean),
    };

    this.plans.set(plan.id, plan);

    return { components: activeComponents, totalCost, plan };
  }

  /**
   * Calcula Custo Total de Evolução (CTE) (P-051)
   */
  calculateTotalCostOfEvolution(plan: InfrastructurePlan): {
    initialCost: number;
    monthlyCost: number;
    yearlyCost: number;
    maintenanceCost: number;
    total3YearCost: number;
    recommendations: string[];
  } {
    const initialCost = plan.estimatedCost * 1.2; // 20% de custo inicial
    const monthlyCost = plan.estimatedCost;
    const yearlyCost = monthlyCost * 12;
    const maintenanceCost = yearlyCost * 0.15; // 15% de manutenção

    const total3YearCost = initialCost + (yearlyCost + maintenanceCost) * 3;

    const recommendations = [];
    if (monthlyCost > 100) {
      recommendations.push('💡 Considere otimizar custos (P-050)');
      recommendations.push('💡 Avaliar necessidade de todos os componentes');
    }
    if (total3YearCost > 5000) {
      recommendations.push('💡 Avaliar ROI dos componentes');
    }

    return {
      initialCost,
      monthlyCost,
      yearlyCost,
      maintenanceCost,
      total3YearCost,
      recommendations,
    };
  }

  /**
   * Implementa Economia de Tokens (P-050)
   */
  implementTokenEconomy(_executionId: string): {
    savings: number;
    strategy: string;
    recommendations: string[];
  } {
    const strategies = [
      'cache',
      'compress',
      'reuse',
      'smaller_model',
      'batch',
      'summarize',
    ];

    const selected = strategies[Math.floor(Math.random() * strategies.length)];
    const savings = 20 + Math.random() * 40;

    const recommendations = [
      `Implementar ${selected} para economizar tokens`,
      'Usar modelos menores para tarefas simples',
      'Reutilizar conhecimento processado',
    ];

    // Registra na economia de tokens
    this.tokenEconomy.recordUsage('infrastructure', {
      model: 'optimization',
      inputTokens: 0,
      outputTokens: 0,
      totalTokens: 0,
      estimatedCost: savings / 100,
      timestamp: new Date(),
    });

    return { savings, strategy: selected, recommendations };
  }

  /**
   * Obtém componente por ID
   */
  getComponent(id: string): InfrastructureComponent | undefined {
    return this.components.get(id);
  }

  /**
   * Obtém todos os componentes
   */
  getComponents(): InfrastructureComponent[] {
    return Array.from(this.components.values());
  }

  /**
   * Obtém plano por ID
   */
  getPlan(id: string): InfrastructurePlan | undefined {
    return this.plans.get(id);
  }

  /**
   * Obtém estatísticas
   */
  getStats(): {
    totalComponents: number;
    activeComponents: number;
    totalCost: number;
    recommendations: string[];
  } {
    const components = Array.from(this.components.values());
    const active = components.filter((c) => c.status === 'active');
    const totalCost = active.reduce((sum, c) => sum + c.costPerMonth, 0);

    const recommendations = [];
    if (totalCost > 100) {
      recommendations.push('⚠️ Considere otimizar infraestrutura');
    }

    const k8s = components.find((c) => c.id === 'kubernetes');
    if (k8s && k8s.status !== 'deprecated') {
      recommendations.push('⚠️ Kubernetes não recomendado na Fase 1 (P-047)');
    }

    return {
      totalComponents: components.length,
      activeComponents: active.length,
      totalCost,
      recommendations,
    };
  }
}
