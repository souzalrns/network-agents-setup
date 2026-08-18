import { AgentFactory } from '../agents/AgentFactory';
import { Router } from './Router';
import { Planner } from './Planner';
import { Executor } from './Executor';
import { MemoryManager } from '@network-agents/memory';
import { AgentResponse } from '@network-agents/shared';
import { getGlobalLogger } from '@network-agents/observability';
import { HitlManager } from '../hitl/HitlManager';

// Segurança, economia e governança básica (Fase 1 do projeto)
import { SecurityManager } from '../security/SecurityManager';
import { TokenEconomy } from '../economy/TokenEconomy';
import { TrustManager } from '../governance/TrustManager';
import { ArchitectureCouncil } from '../governance/ArchitectureCouncil';
import { SelfAwareness } from '../observability/SelfAwareness';
import { ImmunologicalMemory } from '../immunity/ImmunologicalMemory';
import { CompletenessValidator } from '../governance/CompletenessValidator';
import { DeliberationEngine } from '../governance/DeliberationEngine';
import { OpportunityRadar } from '../opportunity/OpportunityRadar';
import { OrganizationalSimulator } from '../simulation/OrganizationalSimulator';

// Complemento do projeto — providências P-004 a P-082
import { ReflectionEngine } from '../cognitive/ReflectionEngine';
import { DeliberationOrchestrator } from '../governance/DeliberationOrchestrator';
import { CouncilsOrchestrator } from '../governance/Councils';
import { TrustOrchestrator } from '../governance/TrustOrchestrator';
import { IngestionOrchestrator } from '../knowledge/IngestionOrchestrator';
import { CognitiveRepository } from '../knowledge/CognitiveRepository';
import { WorkerSupervisor } from '../operations/WorkerSupervisor';
import { AttentionEconomy } from '../ux/AttentionEconomy';
import { AdaptiveInterface } from '../ux/AdaptiveInterface';
import { AccumulationCycle } from '../evolution/AccumulationCycle';
import { VersionManager } from '../evolution/VersionManager';
import { DataGovernance } from '../data/DataGovernance';
import { HorizontalAgents } from '../agents/HorizontalAgents';
import { MetricsDashboard } from '../observability/MetricsDashboard';
import { InfrastructureManager } from '../infrastructure/InfrastructureManager';
import { RepositoryManager } from '../development/RepositoryManager';
import { SpecialtyManager } from '../domains/SpecialtyManager';
import { ProductManager } from '../products/ProductManager';
import { DocumentationGovernance } from '../governance/DocumentationGovernance';
import { AIVisibilityEngine } from '../search/AIVisibilityEngine';
import { ComplianceManager } from '../compliance/ComplianceManager';

export class Orchestrator {
  private logger = getGlobalLogger();

  // Fase 1
  public security: SecurityManager;
  public tokenEconomy: TokenEconomy;
  public trustManager: TrustManager;
  public architectureCouncil: ArchitectureCouncil;
  public selfAwareness: SelfAwareness;
  public immunologicalMemory: ImmunologicalMemory;
  public completenessValidator: CompletenessValidator;
  public deliberationEngine: DeliberationEngine;
  public opportunityRadar: OpportunityRadar;
  public simulator: OrganizationalSimulator;

  // Complemento do projeto
  public reflectionEngine: ReflectionEngine;
  public deliberationOrchestrator: DeliberationOrchestrator;
  public councils: CouncilsOrchestrator;
  public trustOrchestrator: TrustOrchestrator;
  public cognitiveRepository: CognitiveRepository;
  public ingestionOrchestrator: IngestionOrchestrator;
  public workerSupervisor: WorkerSupervisor;
  public attentionEconomy: AttentionEconomy;
  public adaptiveInterface: AdaptiveInterface;
  public accumulationCycle: AccumulationCycle;
  public versionManager: VersionManager;
  public dataGovernance: DataGovernance;
  public horizontalAgents: HorizontalAgents;
  public metricsDashboard: MetricsDashboard;
  public infrastructureManager: InfrastructureManager;
  public repositoryManager: RepositoryManager;
  public specialtyManager: SpecialtyManager;
  public productManager: ProductManager;
  public documentationGovernance: DocumentationGovernance;
  public aiVisibilityEngine: AIVisibilityEngine;
  public complianceManager: ComplianceManager;

  constructor(
    private agentFactory: AgentFactory,
    private router: Router,
    private planner: Planner,
    private executor: Executor,
    _memory: MemoryManager,
    private hitlManager: HitlManager
  ) {
    // ===== Fase 1: segurança, economia e governança básica =====
    this.security = new SecurityManager({
      sessionTimeout: 24 * 60 * 60 * 1000,
      maxLoginAttempts: 5,
      rateLimitMax: 100,
    });
    this.tokenEconomy = new TokenEconomy({
      defaultBudget: 1000000,
      cacheTTL: 3600,
      minSavingsForOptimization: 1000,
    });
    this.trustManager = new TrustManager();
    this.architectureCouncil = new ArchitectureCouncil({
      autoApproveThreshold: 80,
      requireReviewForTypes: ['architecture_change', 'constitutional_change'],
    });
    this.completenessValidator = new CompletenessValidator({
      minCompletenessForOperational: 80,
      autoIngestEnabled: true,
    });
    this.selfAwareness = new SelfAwareness({
      updateInterval: 60 * 1000,
      historySize: 100,
    });
    this.immunologicalMemory = new ImmunologicalMemory({
      maxEvents: 10000,
      autoArchiveAfter: 90,
      entropyThreshold: 50,
    });
    this.deliberationEngine = new DeliberationEngine({
      operationalThreshold: 20,
      tacticalThreshold: 50,
      strategicThreshold: 75,
    });
    this.opportunityRadar = new OpportunityRadar(this.selfAwareness, {
      scanInterval: 60 * 60 * 1000,
      minPotential: 50,
      maxDistance: 70,
    });
    this.simulator = new OrganizationalSimulator(this.selfAwareness, {
      maxConcurrentSimulations: 5,
      defaultSteps: 100,
    });

    // ===== Complemento do projeto: providências P-004 a P-082 =====
    this.reflectionEngine = new ReflectionEngine();
    this.deliberationOrchestrator = new DeliberationOrchestrator(
      this.deliberationEngine,
      this.architectureCouncil,
      this.security,
      this.tokenEconomy,
      this.hitlManager
    );
    this.councils = new CouncilsOrchestrator(
      this.architectureCouncil,
      this.opportunityRadar,
      this.tokenEconomy,
      this.trustManager
    );
    this.trustOrchestrator = new TrustOrchestrator(this.trustManager, this.security, this.selfAwareness);
    this.cognitiveRepository = new CognitiveRepository();
    this.ingestionOrchestrator = new IngestionOrchestrator(this.completenessValidator, this.security);
    this.workerSupervisor = new WorkerSupervisor();
    this.attentionEconomy = new AttentionEconomy();
    this.adaptiveInterface = new AdaptiveInterface();
    this.accumulationCycle = new AccumulationCycle();
    this.versionManager = new VersionManager();
    this.dataGovernance = new DataGovernance(this.security);
    this.horizontalAgents = new HorizontalAgents(this.tokenEconomy, this.cognitiveRepository);
    this.metricsDashboard = new MetricsDashboard(
      this.selfAwareness,
      this.tokenEconomy,
      this.trustManager,
      this.immunologicalMemory,
      this.opportunityRadar
    );
    this.infrastructureManager = new InfrastructureManager();
    this.repositoryManager = new RepositoryManager(this.completenessValidator);
    this.specialtyManager = new SpecialtyManager(this.agentFactory);
    this.productManager = new ProductManager(this.specialtyManager);
    this.documentationGovernance = new DocumentationGovernance();
    this.aiVisibilityEngine = new AIVisibilityEngine();
    this.complianceManager = new ComplianceManager(this.dataGovernance, this.security);
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

    // 5b. Inicia ciclo de acumulação cognitiva para a execução (P-040)
    this.accumulationCycle.startCycle(executionId);
    this.accumulationCycle.observe(executionId, input);

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

    // 9b. Reflexão sobre o resultado da execução (P-004)
    this.reflectionEngine.reflect({
      executionId,
      input,
      output: result.finalOutput,
      success: result.success,
      errors: result.errors,
      durationMs: result.metadata.durationMs,
    });

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
    // Implementação com streaming (callbacks reservados para uso futuro:
    // hoje delega ao fluxo síncrono de processRequest).
    void callbacks;
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

  async getMetricsReport(): Promise<string> {
    return this.metricsDashboard.generateTextReport();
  }

  async getSystemStatus(): Promise<any> {
    return {
      security: this.security.getSecurityStatus(),
      trust: this.trustManager.getCertifiedCompetences(),
      health: this.selfAwareness.getState()?.health,
      entropy: this.immunologicalMemory.getStats(),
      opportunities: this.opportunityRadar.getOpportunities({ status: 'new' }).length,
      dashboard: this.metricsDashboard.getDashboard(),
      workers: this.workerSupervisor.getStats(),
      productsInProduction: this.productManager.getProductsInProduction().length,
      compliance: this.complianceManager.checkCompliance(),
    };
  }
}
