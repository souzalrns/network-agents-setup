import { StateGraph } from '../base/StateGraph';
import { GraphState } from '../../state/StateManager';
import { Orchestrator, Planner, Executor } from '@network-agents/core';
import { getGlobalLogger } from '@network-agents/observability';
export class ExecutionGraph extends StateGraph {
  private logger = getGlobalLogger();
  constructor(
    private orchestrator: Orchestrator,
    private planner: Planner,
    private executor: Executor
  ) {
    super();
    this.addNode('perception', this.perceptionNode.bind(this));
    this.addNode('planning', this.planningNode.bind(this));
    this.addNode('execution', this.executionNode.bind(this));
    this.addNode('validation', this.validationNode.bind(this));
    this.addNode('learning', this.learningNode.bind(this));
    this.addEdge('perception', this.perceptionEdge.bind(this));
    this.addEdge('planning', this.planningEdge.bind(this));
    this.addEdge('execution', this.executionEdge.bind(this));
    this.addEdge('validation', this.validationEdge.bind(this));
    this.setEntryPoint('perception');
    this.logger.info('ExecutionGraph initialized');
  }
  private async perceptionNode(state: GraphState): Promise<Partial<GraphState>> {
    this.logger.debug('Perception node', { input: state.input });
    const context = {
      ...state.context,
      input: state.input,
      domain: state.domain,
      userId: state.userId,
      timestamp: new Date(),
    };
    return { status: 'idle', context };
  }
  private async planningNode(state: GraphState): Promise<Partial<GraphState>> {
    this.logger.debug('Planning node', { intent: state.intent });
    const domainAgents = []; // Será preenchido pelo orchestrator
    const plan = await this.planner.plan(state.input, domainAgents, state.context);
    return { plan, status: 'planning', intent: plan.intent };
  }
  private async executionNode(state: GraphState): Promise<Partial<GraphState>> {
    this.logger.debug('Execution node', { planSteps: state.plan?.steps.length });
    if (!state.plan) {
      throw new Error('No plan to execute');
    }
    const executionId = state.executionId || `exec_${Date.now()}`;
    const result = await this.executor.execute(state.plan, executionId);
    for (const step of result.steps) {
      state.results.set(step.id, step.output);
    }
    return {
      executionId,
      results: state.results,
      status: result.success ? 'executing' : 'failed',
      metadata: { ...state.metadata, executionResult: result },
    };
  }
  private async validationNode(state: GraphState): Promise<Partial<GraphState>> {
    this.logger.debug('Validation node', { hasErrors: state.hasErrors() });
    if (state.hasErrors()) {
      return { status: 'failed', errors: state.errors };
    }
    const validationResult = await this.validateResults(state);
    if (!validationResult.success) {
      state.addError(`Validation failed: ${validationResult.message}`);
      return { status: 'failed', errors: state.errors };
    }
    return {
      status: 'completed',
      metadata: { ...state.metadata, validation: validationResult },
    };
  }
  private async learningNode(state: GraphState): Promise<Partial<GraphState>> {
    this.logger.debug('Learning node');
    const learning = {
      input: state.input,
      intent: state.intent,
      results: Array.from(state.results.entries()),
      errors: state.errors,
      duration: state.endTime
        ? state.endTime.getTime() - state.startTime.getTime()
        : 0,
    };
    return { metadata: { ...state.metadata, learning } };
  }
  private async perceptionEdge(state: GraphState): Promise<string> {
    return 'planning';
  }
  private async planningEdge(state: GraphState): Promise<string> {
    if (state.plan && state.plan.steps.length > 0) {
      return 'execution';
    }
    return 'failed';
  }
  private async executionEdge(state: GraphState): Promise<string> {
    if (state.status === 'completed' || state.status === 'executing') {
      return 'validation';
    }
    return 'failed';
  }
  private async validationEdge(state: GraphState): Promise<string> {
    if (state.status === 'completed') {
      return 'learning';
    }
    return 'failed';
  }
  private async validateResults(state: GraphState): Promise<{ success: boolean; message?: string }> {
    if (!state.plan) {
      return { success: false, message: 'No plan' };
    }
    const missingSteps = state.plan.steps.filter(
      (step: any) => !state.results.has(step.id)
    );
    if (missingSteps.length > 0) {
      return {
        success: false,
        message: `Missing results for steps: ${missingSteps.map((s: any) => s.id).join(', ')}`,
      };
    }
    return { success: true };
  }
}
