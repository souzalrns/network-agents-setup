import { AgentFactory } from '../agents/AgentFactory';
import { LLMService } from '../llm/LLMService';
import { MemoryManager } from '@network-agents/memory';
import { HitlManager } from '../hitl/HitlManager';
import { Plan, PlanStep, ExecutionResult } from '@network-agents/shared';
import { HitlCategory, HitlPriority } from '@network-agents/shared';
import { getGlobalLogger } from '@network-agents/observability';
import { getGlobalMetrics } from '@network-agents/observability';
import { getGlobalTracer } from '@network-agents/observability';
export class Executor {
  private logger = getGlobalLogger();
  private metrics = getGlobalMetrics();
  private tracer = getGlobalTracer();
  constructor(
    private agentFactory: AgentFactory,
    private memory: MemoryManager,
    private llm: LLMService,
    private hitlManager: HitlManager
  ) {}
  async execute(plan: Plan, executionId: string): Promise<ExecutionResult> {
    const logger = this.logger.child('Executor');
    logger.setExecutionId(executionId);
    const traceSpanId = this.tracer.startSpan(`Execute Plan: ${plan.intent}`);
    this.tracer.setAttribute(traceSpanId, 'execution_id', executionId);
    this.tracer.setAttribute(traceSpanId, 'domain', plan.domain);
    this.tracer.setAttribute(traceSpanId, 'steps', plan.steps.length);
    logger.info('Starting execution', {
      planId: plan.id,
      domain: plan.domain,
      steps: plan.steps.length,
    });
    const results: ExecutionResult = {
      success: true,
      steps: [],
      finalOutput: '',
      errors: [],
      metadata: {
        totalSteps: plan.steps.length,
        completedSteps: 0,
        failedSteps: 0,
        startTime: new Date(),
      },
    };
    const sharedContext: Record<string, any> = {};
    await this.memory.executions.update(executionId, {
      status: 'running',
      intent: plan.intent,
    });
    for (let i = 0; i < plan.steps.length; i++) {
      const step = plan.steps[i];
      try {
        if (step.requiresApproval) {
          const approved = await this.requestHumanApproval(
            step,
            plan,
            i,
            sharedContext,
            executionId
          );
          if (!approved) {
            results.metadata.failedSteps++;
            results.errors.push(`Step ${step.id} was rejected by human`);
            results.success = false;
            await this.memory.executions.update(executionId, {
              status: 'failed',
              errors: JSON.stringify(results.errors),
            });
            break;
          }
        }
        const stepResult = await this.executeStep(step, sharedContext, executionId);
        results.steps.push(stepResult);
        results.metadata.completedSteps++;
        if (stepResult.output) {
          sharedContext[`step_${step.id}`] = stepResult.output;
        }
        if (plan.conversationId) {
          await this.memory.addMessage(
            plan.conversationId,
            'assistant',
            stepResult.output || `Step ${step.id} completed`,
            { agentId: step.agentId }
          );
        }
        await this.memory.executions.update(executionId, {
          steps: results.steps,
          updatedAt: new Date(),
        });
        // Métricas de passo
        this.metrics.counter('steps_completed', { agent: step.agentId });
        this.metrics.counter('tokens_used', { agent: step.agentId }, stepResult.tokens || 0);
      } catch (error: any) {
        results.steps.push({
          id: step.id,
          agentId: step.agentId,
          success: false,
          output: null,
          error: error.message,
          timestamp: new Date(),
        });
        results.metadata.failedSteps++;
        results.errors.push(error.message);
        results.success = false;
        this.metrics.counter('steps_failed', { agent: step.agentId });
        this.logger.error(`Step failed`, {
          stepId: step.id,
          agentId: step.agentId,
          error: error.message,
        });
        await this.memory.executions.update(executionId, {
          status: 'failed',
          errors: JSON.stringify(results.errors),
          updatedAt: new Date(),
        });
        if (step.critical) break;
      }
    }
    results.metadata.endTime = new Date();
    results.metadata.durationMs = results.metadata.endTime.getTime() - results.metadata.startTime.getTime();
    // Atualiza execução no banco
    await this.memory.executions.update(executionId, {
      status: results.success ? 'completed' : 'failed',
      result: results.finalOutput,
      steps: results.steps,
      durationMs: results.metadata.durationMs,
      totalTokens: results.metadata.totalTokens || 0,
      totalCost: results.metadata.totalCost || 0,
      completedAt: new Date(),
      updatedAt: new Date(),
    });
    // Métricas finais
    this.metrics.counter('executions_total', { status: results.success ? 'success' : 'failed' });
    this.metrics.histogram('execution_duration_ms', {}, results.metadata.durationMs);
    if (results.metadata.totalTokens) {
      this.metrics.counter('tokens_total', {}, results.metadata.totalTokens);
    }
    this.tracer.endSpan(traceSpanId, results.success ? 'ok' : 'error');
    await this.tracer.exportTrace(traceSpanId);
    return results;
  }
  private async executeStep(
    step: PlanStep,
    context: Record<string, any>,
    _executionId: string
  ): Promise<{
    id: string;
    agentId: string;
    success: boolean;
    output: any;
    error?: string;
    tokens?: number;
    timestamp: Date;
  }> {
    const agent = this.agentFactory.getAgent(step.agentId);
    if (!agent) {
      throw new Error(`Agent ${step.agentId} not found`);
    }
    const systemPrompt = agent.systemPrompt || `You are ${agent.id}, a specialist in ${agent.description}.`;
    const userPrompt = step.prompt || step.description;
    const contextPrompt = this.buildContextPrompt(step, context);
    const response = await this.llm.chat({
      system: systemPrompt,
      messages: [
        {
          role: 'user',
          content: `${contextPrompt}\n\nTarefa: ${userPrompt}`,
        },
      ],
      temperature: step.temperature || 0.3,
      maxTokens: step.maxTokens || 2000,
    });
    return {
      id: step.id,
      agentId: step.agentId,
      success: true,
      output: response.content,
      tokens: response.usage?.tokens || 0,
      timestamp: new Date(),
    };
  }
  private buildContextPrompt(step: PlanStep, context: Record<string, any>): string {
    let ctx = 'Contexto disponível:\n';
    for (const key of step.contextKeys || []) {
      if (context[key]) {
        ctx += `- ${key}: ${JSON.stringify(context[key])}\n`;
      }
    }
    return ctx;
  }
  private async requestHumanApproval(
    step: PlanStep,
    plan: Plan,
    stepIndex: number,
    context: Record<string, any>,
    executionId: string
  ): Promise<boolean> {
    const hitlRequest = await this.hitlManager.requestApproval({
      agentId: step.agentId,
      domain: plan.domain,
      category: (step.approvalCategory as HitlCategory) || HitlCategory.APPROVAL,
      priority: (step.approvalPriority as HitlPriority) || HitlPriority.MEDIUM,
      title: step.approvalTitle || `Aprovação necessária: ${step.description}`,
      description: step.approvalDescription || step.description,
      context: {
        planId: plan.id,
        stepIndex,
        executionId,
        ...context,
      },
      proposedAction: step.prompt || step.description,
      alternatives: step.alternatives,
      risks: step.risks,
      impacts: step.impacts,
      expiresInMinutes: step.approvalExpiresIn || 60,
      metadata: step.approvalMetadata,
    });
    await this.memory.checkpoints.create({
      executionId,
      hitlRequestId: hitlRequest.id,
      stepIndex,
      state: context,
      memorySnapshot: this.memory.snapshot(),
    });
    await this.memory.executions.update(executionId, {
      status: 'waiting_hitl',
    });
    const response = await this.waitForHumanResponse(hitlRequest.id);
    await this.memory.checkpoints.deleteByHitlRequest(hitlRequest.id);
    await this.memory.executions.update(executionId, { status: 'running' });
    return response === 'approved';
  }
  private async waitForHumanResponse(
    requestId: string,
    timeoutMs: number = 5 * 60 * 1000
  ): Promise<'approved' | 'rejected'> {
    const startTime = Date.now();
    const pollInterval = 1000;
    return new Promise((resolve, reject) => {
      const interval = setInterval(() => {
        const request = this.hitlManager.getRequest(requestId);
        if (!request) {
          clearInterval(interval);
          reject(new Error('Solicitação não encontrada'));
          return;
        }
        if (request.status === 'approved') {
          clearInterval(interval);
          resolve('approved');
        } else if (request.status === 'rejected') {
          clearInterval(interval);
          resolve('rejected');
        } else if (request.status === 'expired') {
          clearInterval(interval);
          reject(new Error('Solicitação expirada'));
        }
        if (Date.now() - startTime > timeoutMs) {
          clearInterval(interval);
          reject(new Error('Timeout aguardando resposta humana'));
        }
      }, pollInterval);
    });
  }
}
