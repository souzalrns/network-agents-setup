import { EventEmitter } from 'events';
import { getGlobalLogger } from '@network-agents/observability';

// P-046 a P-051: Gestão de Infraestrutura — rastreia componentes de
// infraestrutura (banco de dados, cache, computação, LLM) com custo,
// recomendações por fase (evitando Kubernetes/Kafka/Neo4j/Qdrant na
// Fase 1, conforme P-047), dimensionamento de VPS e cálculo do custo de
// evolução em 3 anos.

export interface InfrastructureComponent {
  id: string;
  name: string;
  type: 'database' | 'cache' | 'compute' | 'llm' | 'storage' | 'queue';
  monthlyCost: number;
  phase: 1 | 2 | 3;
  registeredAt: Date;
}

export interface InfrastructurePlan {
  phase: 1 | 2 | 3;
  recommendedComponents: string[];
  avoidComponents: string[];
  estimatedMonthlyCost: number;
  performance: 'low' | 'medium' | 'high' | 'very_high';
  reasoning: string;
}

const PHASE_1_AVOID = ['kubernetes', 'kafka', 'neo4j', 'qdrant'];

export class InfrastructureManager extends EventEmitter {
  private components: Map<string, InfrastructureComponent> = new Map();
  private logger = getGlobalLogger();

  registerComponent(params: {
    name: string;
    type: InfrastructureComponent['type'];
    monthlyCost: number;
    phase: 1 | 2 | 3;
  }): InfrastructureComponent {
    const component: InfrastructureComponent = {
      id: `infra_${Date.now()}_${Math.random().toString(36).slice(2, 6)}`,
      ...params,
      registeredAt: new Date(),
    };
    this.components.set(component.id, component);
    this.logger.info(`[InfrastructureManager] Componente registrado: ${component.name} (fase ${component.phase})`);
    this.emit('component:registered', component);
    return component;
  }

  /**
   * Gera uma recomendação de infraestrutura para a fase informada,
   * evitando tecnologias de complexidade prematura na Fase 1 (P-047).
   */
  getInfrastructureRecommendation(phase: 1 | 2 | 3, expectedLoad: 'low' | 'medium' | 'high'): InfrastructurePlan {
    if (phase === 1) {
      return {
        phase,
        recommendedComponents: ['PostgreSQL (VPS único)', 'Redis (cache simples)', 'Node.js monolito'],
        avoidComponents: PHASE_1_AVOID,
        estimatedMonthlyCost: expectedLoad === 'low' ? 40 : expectedLoad === 'medium' ? 80 : 150,
        performance: 'medium',
        reasoning: 'Fase 1 prioriza simplicidade operacional e baixo custo — evitar Kubernetes/Kafka/Neo4j/Qdrant até que a escala justifique a complexidade.',
      };
    }
    if (phase === 2) {
      return {
        phase,
        recommendedComponents: ['PostgreSQL gerenciado', 'Redis Cluster', 'Filas leves (BullMQ)'],
        avoidComponents: ['kubernetes'],
        estimatedMonthlyCost: expectedLoad === 'low' ? 150 : expectedLoad === 'medium' ? 400 : 800,
        performance: 'high',
        reasoning: 'Fase 2 introduz componentes gerenciados e filas para suportar crescimento moderado.',
      };
    }
    return {
      phase,
      recommendedComponents: ['Kubernetes', 'Kafka', 'Bancos vetoriais dedicados (Qdrant)', 'Multi-região'],
      avoidComponents: [],
      estimatedMonthlyCost: expectedLoad === 'low' ? 800 : expectedLoad === 'medium' ? 2000 : 5000,
      performance: 'very_high',
      reasoning: 'Fase 3 justifica a complexidade adicional para escala e resiliência de alto nível.',
    };
  }

  /**
   * Sugere dimensionamento de VPS para a Fase 1, com base na carga esperada.
   */
  sizeVPS(expectedLoad: 'low' | 'medium' | 'high'): { vcpus: number; ramGb: number; estimatedMonthlyCost: number } {
    const sizing = {
      low: { vcpus: 2, ramGb: 4, estimatedMonthlyCost: 20 },
      medium: { vcpus: 4, ramGb: 8, estimatedMonthlyCost: 40 },
      high: { vcpus: 8, ramGb: 16, estimatedMonthlyCost: 80 },
    };
    return sizing[expectedLoad];
  }

  /**
   * Calcula o custo total estimado de evolução da infraestrutura ao
   * longo de 3 anos, considerando a transição entre fases.
   */
  calculateThreeYearCost(startPhase: 1 | 2 | 3 = 1): {
    totalCost: number;
    byYear: Array<{ year: number; phase: number; cost: number }>;
  } {
    const byYear: Array<{ year: number; phase: number; cost: number }> = [];
    let phase = startPhase;
    let totalCost = 0;
    for (let year = 1; year <= 3; year++) {
      const plan = this.getInfrastructureRecommendation(phase as 1 | 2 | 3, 'medium');
      const yearCost = plan.estimatedMonthlyCost * 12;
      byYear.push({ year, phase, cost: yearCost });
      totalCost += yearCost;
      if (phase < 3) phase = (phase + 1) as 1 | 2 | 3;
    }
    return { totalCost, byYear };
  }

  getComponents(phase?: 1 | 2 | 3): InfrastructureComponent[] {
    const all = Array.from(this.components.values());
    return phase ? all.filter((c) => c.phase === phase) : all;
  }

  getTotalMonthlyCost(): number {
    return Array.from(this.components.values()).reduce((sum, c) => sum + c.monthlyCost, 0);
  }
}
