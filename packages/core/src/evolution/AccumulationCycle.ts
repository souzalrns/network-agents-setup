import { EventEmitter } from 'events';
import { getGlobalLogger } from '@network-agents/observability';

// P-040: Ciclo de Acumulação Cognitiva — observação -> análise ->
// validação -> generalização -> capacidade, rastreado por execução,
// podendo eventualmente gerar novas "capacidades" candidatas.
//
// Nota: o estado por execução é modelado pela interface
// `AccumulationCycleState` (renomeada para evitar colisão de nome com a
// classe `AccumulationCycle`, que orquestra o ciclo).

export type AccumulationStep = 'observation' | 'analysis' | 'validation' | 'generalization' | 'capability';

export interface AccumulationCycleState {
  executionId: string;
  step: AccumulationStep;
  observations: string[];
  analysis?: string;
  validated: boolean;
  generalization?: string;
  spawnedCapabilityId?: string;
  startedAt: Date;
  updatedAt: Date;
}

const STEP_ORDER: AccumulationStep[] = ['observation', 'analysis', 'validation', 'generalization', 'capability'];

export class AccumulationCycle extends EventEmitter {
  private cycles: Map<string, AccumulationCycleState> = new Map();
  private logger = getGlobalLogger();

  constructor(
    private config: {
      minObservationsForAnalysis?: number;
    } = {}
  ) {
    super();
    this.config.minObservationsForAnalysis = config.minObservationsForAnalysis ?? 3;
  }

  startCycle(executionId: string): AccumulationCycleState {
    const state: AccumulationCycleState = {
      executionId,
      step: 'observation',
      observations: [],
      validated: false,
      startedAt: new Date(),
      updatedAt: new Date(),
    };
    this.cycles.set(executionId, state);
    this.logger.info(`[AccumulationCycle] Ciclo iniciado para execução ${executionId}`);
    this.emit('cycle:started', state);
    return state;
  }

  observe(executionId: string, observation: string): AccumulationCycleState {
    const state = this.cycles.get(executionId) || this.startCycle(executionId);
    state.observations.push(observation);
    state.updatedAt = new Date();

    if (
      state.step === 'observation' &&
      state.observations.length >= (this.config.minObservationsForAnalysis || 3)
    ) {
      this.advance(state, 'analysis');
    }
    this.cycles.set(executionId, state);
    return state;
  }

  analyze(executionId: string, analysis: string): AccumulationCycleState {
    const state = this.requireCycle(executionId);
    state.analysis = analysis;
    this.advance(state, 'validation');
    return state;
  }

  validate(executionId: string, validated: boolean): AccumulationCycleState {
    const state = this.requireCycle(executionId);
    state.validated = validated;
    if (validated) {
      this.advance(state, 'generalization');
    } else {
      this.logger.warn(`[AccumulationCycle] Validação falhou para execução ${executionId}`);
      this.emit('cycle:validation-failed', state);
    }
    return state;
  }

  generalize(executionId: string, generalization: string): AccumulationCycleState {
    const state = this.requireCycle(executionId);
    state.generalization = generalization;
    this.advance(state, 'capability');
    return state;
  }

  /**
   * Marca o ciclo como concluído, opcionalmente gerando uma nova
   * capacidade candidata a partir da generalização obtida.
   */
  spawnCapability(executionId: string, capabilityId: string): AccumulationCycleState {
    const state = this.requireCycle(executionId);
    state.spawnedCapabilityId = capabilityId;
    state.updatedAt = new Date();
    this.cycles.set(executionId, state);
    this.logger.info(`[AccumulationCycle] Nova capacidade gerada a partir do ciclo ${executionId}: ${capabilityId}`);
    this.emit('capability:spawned', state);
    return state;
  }

  private advance(state: AccumulationCycleState, next: AccumulationStep): void {
    state.step = next;
    state.updatedAt = new Date();
    this.cycles.set(state.executionId, state);
    this.logger.info(`[AccumulationCycle] Execução ${state.executionId} avançou para "${next}"`);
    this.emit('cycle:advanced', state);
  }

  private requireCycle(executionId: string): AccumulationCycleState {
    const state = this.cycles.get(executionId);
    if (!state) {
      throw new Error(`Ciclo de acumulação não encontrado para execução ${executionId}`);
    }
    return state;
  }

  getCycle(executionId: string): AccumulationCycleState | undefined {
    return this.cycles.get(executionId);
  }

  getStepIndex(step: AccumulationStep): number {
    return STEP_ORDER.indexOf(step);
  }

  getActiveCycles(): AccumulationCycleState[] {
    return Array.from(this.cycles.values()).filter((c) => c.step !== 'capability' || !c.spawnedCapabilityId);
  }
}
