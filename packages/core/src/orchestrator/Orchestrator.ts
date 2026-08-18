import { AgentFactory } from '../agents/AgentFactory';
import { Router } from './Router';
import { Planner } from './Planner';
import { Executor } from './Executor';
import { MemoryManager } from '@network-agents/memory';
import { AgentResponse } from '@network-agents/shared';
import { getGlobalLogger } from '@network-agents/observability';
import { SecurityManager } from '../security/SecurityManager';
import { TokenEconomy } from '../economy/TokenEconomy';
import { TrustManager } from '../governance/TrustManager';
import { ArchitectureCouncil } from '../governance/ArchitectureCouncil';
import { SelfAwareness } from '../observability/SelfAwareness';
import { ImmunologicalMemory } from '../immunity/ImmunologicalMemory';
import { CompletenessValidator } from '../governance/CompletenessValidator';
import { OpportunityRadar } from '../opportunity/OpportunityRadar';
import { OrganizationalSimulator } from '../simulation/OrganizationalSimulator';

export class Orchestrator {
  private logger = getGlobalLogger();
  private opportunityRadar: OpportunityRadar;
  private simulator: OrganizationalSimulator;

  constructor(
    private agentFactory: AgentFactory,
    private router: Router,
    private planner: Planner,
    private executor: Executor,
    private memory: MemoryManager,
    private security: SecurityManager,
    private tokenEconomy: TokenEconomy,
    private trustManager: TrustManager,
    private architectureCouncil: ArchitectureCouncil,
    private selfAwareness: SelfAwareness,
    private immunologicalMemory: ImmunologicalMemory,
    private completenessValidator: CompletenessValidator,
    private deliberationEngine: any
  ) {
    // Inicializa dependências circulares
    this.opportunityRadar = new OpportunityRadar(selfAwareness, {
      scanInterval: 60 * 60 * 1000,
      minPotential: 50,
      maxDistance: 70,
    });

    this.simulator = new OrganizationalSimulator(selfAwareness, {
      maxConcurrentSimulations: 5,
      defaultSteps: 100,
    });
  }

  async processRequest(
    input: string,
    context?: Record<string, any>
  ): Promise<AgentResponse> {
    const logger = this.logger.child('Orchestrator');
    logger.setExecutionId(context?.executionId);
    logger.info('Processing request', {
      input: input.slice(0, 100),
      domain: context?.domain,
    });

    // 1. Verifica segurança (detecta ataques)
    const injectionCheck = this.security.detectPromptInjection(input);
    if (!injectionCheck.safe) {
      logger.warn('Prompt injection detected', { reason: injectionCheck.reason });
      this.immunologicalMemory.registerEvent({
        type: 'attack',
        severity: 'critical',
        description: `Prompt injection attempt: ${injectionCheck.reason}`,
        rootCause: 'malicious_input',
        impact: { components: ['orchestrator'], durationMs: 0, dataLoss: false, serviceDegradation: true },
        response: { action: 'blocked', executedBy: 'security', durationMs: 0, success: true },
        learnings: ['Prompt injection pattern detected'],
        recommendations: ['Block and log source'],
        status: 'resolved',
        resolvedAt: new Date(),
        recurrenceCount: 0,
        similarEvents: [],
        metadata: { input: input.slice(0, 200) },
      });
      return {
        agentId: 'security',
        content: 'Request blocked due to security policy violation.',
        metadata: { blocked: true, reason: injectionCheck.reason },
        timestamp: new Date(),
      };
    }

    // 2. Pesquisa antes da construção (P-056)
    const searchResult = await this.tokenEconomy.searchBeforeBuild({
      type: 'request',
      description: input,
      domain: context?.domain,
    });
    if (searchResult.exists && searchResult.recommendation === 'reuse') {
      logger.info('Capability reuse recommended', { alternatives: searchResult.alternatives });
    }

    // 3. Determina domínio
    const domain = context?.domain || this.router.route(input);
    logger.info(`Routed to domain: ${domain}`);

    // 4. Verifica confiança para o domínio
    const trustCheck = this.trustManager.checkAutonomy(domain, {
      type: 'process_request',
      scope: domain,
    });
    if (!trustCheck.allowed) {
      logger.warn('Autonomy check failed', { domain, reason: trustCheck.reason });
      return {
        agentId: 'trust',
        content: `Request not allowed: ${trustCheck.reason}`,
        metadata: { blocked: true, reason: trustCheck.reason },
        timestamp: new Date(),
      };
    }

    // 5. Aloca orçamento de tokens
    const executionId = context?.executionId || `exec_${Date.now()}`;
    const budget = this.tokenEconomy.allocateBudget(executionId, 10000);
    logger.info(`Budget allocated: ${budget.allocated} tokens`);

    // 6. Verifica completude de capacidades
    const emptyCapabilities = this.completenessValidator.getEmptyCapabilities();
    if (emptyCapabilities.length > 0) {
      logger.warn(`Empty capabilities detected: ${emptyCapabilities.length}`);
      for (const cap of emptyCapabilities) {
        this.immunologicalMemory.registerEvent({
          type: 'vulnerability',
          severity: 'medium',
          description: `Capability ${cap.name} (${cap.id}) is empty`,
          rootCause: 'missing_content',
          impact: { components: [cap.id], durationMs: 0, dataLoss: false, serviceDegradation: true },
          response: { action: 'pending', executedBy: 'system', durationMs: 0, success: false },
          learnings: ['Capabilities need immediate ingestion'],
          recommendations: ['Alimentar capacidade com conteúdo'],
          status: 'open',
          recurrenceCount: 0,
          similarEvents: [],
          metadata: { capabilityId: cap.id },
        });
      }
    }

    // 7. Executa o request (via executor existente)
    const domainAgents = this.agentFactory.getAgentsByDomain(domain);
    if (domainAgents.length === 0) {
      throw new Error(`No agents found for domain: ${domain}`);
    }
    const plan = await this.planner.plan(input, domainAgents, {
      ...context,
      domain,
    });
    const result = await this.executor.execute(plan, executionId);

    // 8. Registra uso de tokens
    const cost = this.tokenEconomy.estimateCost(
      'gpt-4-turbo',
      result.metadata.totalTokens || 0,
      result.metadata.totalTokens || 0
    );
    this.tokenEconomy.recordUsage(executionId, cost);

    // 9. Atualiza autopercepção
    await this.selfAwareness.updateState();

    // 10. Registra evento na memória imunológica se houve erro
    if (!result.success) {
      this.immunologicalMemory.registerEvent({
        type: 'failure',
        severity: result.errors.length > 3 ? 'high' : 'medium',
        description: `Execution failed: ${result.errors.join(', ')}`,
        rootCause: result.errors[0] || 'unknown',
        impact: { components: ['executor'], durationMs: result.metadata.durationMs || 0, dataLoss: false, serviceDegradation: true },
        response: { action: 'logged', executedBy: 'orchestrator', durationMs: 0, success: false },
        learnings: ['Execution failures detected'],
        recommendations: ['Investigate root cause and implement prevention'],
        status: 'open',
        recurrenceCount: 0,
        similarEvents: [],
        metadata: { executionId, errors: result.errors },
      });
    }

    return {
      agentId: 'orchestrator',
      content: result.finalOutput,
      metadata: {
        executionId,
        domain,
        steps: result.steps,
        durationMs: result.metadata.durationMs,
        totalTokens: result.metadata.totalTokens,
        totalCost: result.metadata.totalCost,
        budgetUsed: budget.used,
        searchResult,
      },
      timestamp: new Date(),
    };
  }

  async processRequestWithProgress(
    input: string,
    context: Record<string, any> | undefined,
    callbacks: {
      onStepStart?: (step: any) => void;
      onStepComplete?: (step: any, result: any) => void;
      onStepError?: (error: any) => void;
      onHitlRequest?: (hitl: any) => void;
      onChunk?: (chunk: string) => void;
      onComplete?: (result: any) => void;
      onError?: (error: any) => void;
    }
  ): Promise<AgentResponse> {
    // Implementação com streaming
    // Similar ao processRequest mas com callbacks
    return this.processRequest(input, context);
  }

  // ===== Métodos adicionais para integração =====

  async getSelfAwarenessReport(): Promise<string> {
    return this.selfAwareness.generateReport();
  }

  async getImmunologicalReport(): Promise<string> {
    return this.immunologicalMemory.generateReport();
  }

  async getOpportunityReport(): Promise<string> {
    return this.opportunityRadar.generateReport();
  }

  async runSimulation(scenarioId: string): Promise<any> {
    return this.simulator.runSimulation(scenarioId);
  }

  async getSystemStatus(): Promise<any> {
    return {
      security: this.security.getSecurityStatus(),
      trust: this.trustManager.getCompetences(),
      health: this.selfAwareness.getState()?.health,
      entropy: this.immunologicalMemory.getStats(),
      opportunities: this.opportunityRadar.getOpportunities({ status: 'new' }).length,
    };
  }
}
