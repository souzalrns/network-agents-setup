import { EventEmitter } from 'events';
import { getGlobalLogger } from '@network-agents/observability';
import { SelfAwareness } from '../observability/SelfAwareness';
import { ImmunologicalMemory } from '../immunity/ImmunologicalMemory';
import { TokenEconomy } from '../economy/TokenEconomy';
import { ReflectionEngine } from '../orchestrator/ReflectionEngine';

export interface AccumulationStep {
  id: string;
  type: 'observation' | 'analysis' | 'solution' | 'validation' | 'generalization' | 'capability' | 'reuse' | 'patrimony';
  description: string;
  timestamp: Date;
  metadata: Record<string, any>;
}

// Nota de fidelidade: no material original este tipo tinha o mesmo nome da
// classe (`AccumulationCycle`), causando um conflito de "declaration merging"
// do TypeScript (a interface e a classe compartilhavam o identificador e os
// campos da interface não correspondiam aos campos privados reais da classe).
// Renomeado para `AccumulationCycleState` para eliminar a colisão, mantendo
// o mesmo formato de dados.
export interface AccumulationCycleState {
  id: string;
  steps: AccumulationStep[];
  completed: boolean;
  startedAt: Date;
  completedAt?: Date;
  result: {
    newCapability?: string;
    improvedCapability?: string;
    knowledgeAdded?: string[];
    reusabilityScore: number;
  };
}

export class AccumulationCycle extends EventEmitter {
  private logger = getGlobalLogger();
  private cycles: Map<string, AccumulationCycleState> = new Map();
  private currentCycle: AccumulationCycleState | null = null;

  constructor(
    private selfAwareness: SelfAwareness,
    private immunologicalMemory: ImmunologicalMemory,
    _tokenEconomy: TokenEconomy,
    _reflectionEngine: ReflectionEngine
  ) {
    super();
    this.logger.info('[AccumulationCycle] Initialized');
  }

  /**
   * Inicia um novo ciclo de acumulação
   */
  startCycle(initialObservation: string): AccumulationCycleState {
    const id = `cycle_${Date.now()}_${Math.random().toString(36).slice(2, 6)}`;

    const cycle: AccumulationCycleState = {
      id,
      steps: [
        {
          id: `step_${Date.now()}_1`,
          type: 'observation',
          description: initialObservation,
          timestamp: new Date(),
          metadata: {},
        },
      ],
      completed: false,
      startedAt: new Date(),
      result: {
        reusabilityScore: 0,
      },
    };

    this.cycles.set(id, cycle);
    this.currentCycle = cycle;

    this.logger.info(`[AccumulationCycle] Cycle started: ${id}`);
    this.emit('cycle:started', cycle);

    return cycle;
  }

  /**
   * Adiciona um passo ao ciclo
   */
  addStep(cycleId: string, type: AccumulationStep['type'], description: string, metadata: Record<string, any> = {}): void {
    const cycle = this.cycles.get(cycleId);
    if (!cycle) {
      throw new Error(`Cycle ${cycleId} not found`);
    }

    const step: AccumulationStep = {
      id: `step_${Date.now()}_${cycle.steps.length + 1}`,
      type,
      description,
      timestamp: new Date(),
      metadata,
    };

    cycle.steps.push(step);
    this.cycles.set(cycleId, cycle);

    this.logger.debug(`[AccumulationCycle] Step added: ${step.type} - ${step.description}`);
    this.emit('cycle:step', { cycleId, step });
  }

  /**
   * Completa o ciclo de acumulação
   */
  async completeCycle(cycleId: string): Promise<AccumulationCycleState> {
    const cycle = this.cycles.get(cycleId);
    if (!cycle) {
      throw new Error(`Cycle ${cycleId} not found`);
    }

    this.logger.info(`[AccumulationCycle] Completing cycle: ${cycleId}`);

    // 1. Validação
    this.addStep(cycleId, 'validation', 'Validando resultado do ciclo');

    // 2. Generalização
    this.addStep(cycleId, 'generalization', 'Generalizando conhecimento');

    // 3. Avalia reutilização
    const reusabilityScore = this.calculateReusability(cycle);
    cycle.result.reusabilityScore = reusabilityScore;

    // 4. Identifica novo conhecimento
    const knowledgeAdded = this.extractKnowledge(cycle);
    cycle.result.knowledgeAdded = knowledgeAdded;

    // 5. Verifica se nova capacidade foi criada
    if (reusabilityScore > 70) {
      cycle.result.newCapability = this.createCapability(cycle);
      this.addStep(cycleId, 'capability', `Nova capacidade criada: ${cycle.result.newCapability}`);
    }

    // 6. Completa
    cycle.completed = true;
    cycle.completedAt = new Date();
    this.cycles.set(cycleId, cycle);
    this.currentCycle = null;

    // 7. Registra na memória imunológica
    if (reusabilityScore > 70) {
      this.immunologicalMemory.registerEvent({
        type: 'recovery',
        severity: 'low',
        description: `Ciclo de acumulação completado: ${cycleId}`,
        rootCause: 'accumulation_success',
        impact: {
          components: ['evolution'],
          durationMs: 0,
          dataLoss: false,
          serviceDegradation: false,
        },
        response: {
          action: 'cycle_completed',
          executedBy: 'AccumulationCycle',
          durationMs: 0,
          success: true,
        },
        learnings: knowledgeAdded,
        recommendations: [`Nova capacidade: ${cycle.result.newCapability || 'Nenhuma'}`],
        status: 'resolved',
        metadata: { cycleId, reusabilityScore },
      });
    }

    // 8. Atualiza autopercepção
    await this.selfAwareness.updateState();

    this.emit('cycle:completed', cycle);
    this.logger.info(`[AccumulationCycle] Cycle completed: ${cycleId} (reusability: ${reusabilityScore}%)`);

    return cycle;
  }

  /**
   * Calcula índice de reutilização
   */
  private calculateReusability(cycle: AccumulationCycleState): number {
    let score = 50;

    // Mais passos = mais reutilização
    if (cycle.steps.length > 5) score += 10;
    if (cycle.steps.length > 10) score += 10;

    // Passos de generalização e validação aumentam reutilização
    const hasValidation = cycle.steps.some((s) => s.type === 'validation');
    const hasGeneralization = cycle.steps.some((s) => s.type === 'generalization');
    if (hasValidation) score += 10;
    if (hasGeneralization) score += 10;

    // Conhecimento adicionado aumenta reutilização
    const knowledgeCount = this.extractKnowledge(cycle).length;
    if (knowledgeCount > 0) score += Math.min(knowledgeCount * 5, 20);

    return Math.min(score, 100);
  }

  /**
   * Extrai conhecimento do ciclo
   */
  private extractKnowledge(cycle: AccumulationCycleState): string[] {
    const knowledge: string[] = [];

    for (const step of cycle.steps) {
      if (step.type === 'analysis' || step.type === 'validation') {
        knowledge.push(step.description);
      }
    }

    return knowledge;
  }

  /**
   * Cria uma nova capacidade
   */
  private createCapability(_cycle: AccumulationCycleState): string {
    const name = `cap_${Date.now()}_${Math.random().toString(36).slice(2, 6)}`;
    this.logger.info(`[AccumulationCycle] Creating capability: ${name}`);
    return name;
  }

  /**
   * Obtém ciclo por ID
   */
  getCycle(id: string): AccumulationCycleState | undefined {
    return this.cycles.get(id);
  }

  /**
   * Obtém ciclo atual
   */
  getCurrentCycle(): AccumulationCycleState | null {
    return this.currentCycle;
  }

  /**
   * Obtém todos os ciclos
   */
  getCycles(): AccumulationCycleState[] {
    return Array.from(this.cycles.values());
  }

  /**
   * Obtém estatísticas
   */
  getStats(): {
    totalCycles: number;
    completedCycles: number;
    avgReusability: number;
    avgSteps: number;
  } {
    const cycles = Array.from(this.cycles.values());
    const completed = cycles.filter((c) => c.completed);
    const totalCycles = cycles.length;
    const completedCycles = completed.length;

    const avgReusability = completed.length > 0
      ? completed.reduce((sum, c) => sum + c.result.reusabilityScore, 0) / completed.length
      : 0;

    const avgSteps = cycles.length > 0
      ? cycles.reduce((sum, c) => sum + c.steps.length, 0) / cycles.length
      : 0;

    return { totalCycles, completedCycles, avgReusability, avgSteps };
  }
}
