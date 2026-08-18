// packages/core/src/orchestrator/Orchestrator.ts
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
import { DeliberationEngine } from '../governance/DeliberationEngine';
import { HitlManager } from '../hitl/HitlManager';
import { ReflectionEngine } from './ReflectionEngine';
import { DeliberationOrchestrator } from './DeliberationOrchestrator';
import { CouncilsOrchestrator } from '../governance/Councils';
import { TrustOrchestrator } from '../governance/TrustOrchestrator';
import { IngestionOrchestrator } from '../governance/IngestionOrchestrator';
import { WorkerSupervisor } from '../operations/WorkerSupervisor';
import { AttentionEconomy } from '../ux/AttentionEconomy';
import { AccumulationCycle } from '../evolution/AccumulationCycle';
import { VersionManager } from '../evolution/VersionManager';
import { CognitiveRepository } from '../knowledge/CognitiveRepository';
import { HorizontalAgents } from '../agents/HorizontalAgents';
import { DataGovernance } from '../data/DataGovernance';
import { AdaptiveInterface } from '../ux/AdaptiveInterface';
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

  // Todos os módulos da plataforma
  public security: SecurityManager;
  public tokenEconomy: TokenEconomy;
  public trustManager: TrustManager;
  public architectureCouncil: ArchitectureCouncil;
  public selfAwareness: SelfAwareness;
  public immunologicalMemory: ImmunologicalMemory;
  public completenessValidator: CompletenessValidator;
  public opportunityRadar: OpportunityRadar;
  public simulator: OrganizationalSimulator;
  public deliberationEngine: DeliberationEngine;
  public reflectionEngine: ReflectionEngine;
  public deliberationOrchestrator: DeliberationOrchestrator;
  public councilsOrchestrator: CouncilsOrchestrator;
  public trustOrchestrator: TrustOrchestrator;
  public ingestionOrchestrator: IngestionOrchestrator;
  public workerSupervisor: WorkerSupervisor;
  public attentionEconomy: AttentionEconomy;
  public accumulationCycle: AccumulationCycle;
  public versionManager: VersionManager;
  public cognitiveRepository: CognitiveRepository;
  public horizontalAgents: HorizontalAgents;
  public dataGovernance: DataGovernance;
  public adaptiveInterface: AdaptiveInterface;
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
    // Inicializa todos os módulos
    this.security = new SecurityManager();
    this.tokenEconomy = new TokenEconomy();
    this.trustManager = new TrustManager();
    this.architectureCouncil = new ArchitectureCouncil();
    this.selfAwareness = new SelfAwareness();
    this.immunologicalMemory = new ImmunologicalMemory();
    this.completenessValidator = new CompletenessValidator();
    this.opportunityRadar = new OpportunityRadar(this.selfAwareness);
    this.simulator = new OrganizationalSimulator(this.selfAwareness);
    this.deliberationEngine = new DeliberationEngine();
    this.reflectionEngine = new ReflectionEngine(
      this.immunologicalMemory,
      this.selfAwareness,
      this.tokenEconomy
    );
    this.deliberationOrchestrator = new DeliberationOrchestrator(
      this.deliberationEngine,
      this.architectureCouncil,
      this.security,
      this.tokenEconomy,
      this.hitlManager
    );
    this.councilsOrchestrator = new CouncilsOrchestrator(
      this.architectureCouncil,
      this.tokenEconomy,
      this.selfAwareness,
      this.opportunityRadar,
      this.security
    );
    this.trustOrchestrator = new TrustOrchestrator(
      this.trustManager,
      this.selfAwareness,
      this.immunologicalMemory,
      this.security
    );
    this.ingestionOrchestrator = new IngestionOrchestrator(
      this.completenessValidator,
      this.immunologicalMemory,
      this.selfAwareness,
      this.security
    );
    this.workerSupervisor = new WorkerSupervisor(this.immunologicalMemory);
    this.attentionEconomy = new AttentionEconomy(this.hitlManager);
    this.accumulationCycle = new AccumulationCycle(
      this.selfAwareness,
      this.immunologicalMemory,
      this.tokenEconomy,
      this.reflectionEngine
    );
    this.versionManager = new VersionManager();
    this.cognitiveRepository = new CognitiveRepository(
      this.versionManager,
      this.selfAwareness
    );
    this.horizontalAgents = new HorizontalAgents(
      this.tokenEconomy,
      this.selfAwareness,
      this.immunologicalMemory,
      this.security,
      this.cognitiveRepository
    );
    this.dataGovernance = new DataGovernance(
      this.security,
      this.immunologicalMemory
    );
    this.adaptiveInterface = new AdaptiveInterface(this.selfAwareness);
    this.metricsDashboard = new MetricsDashboard(
      this.selfAwareness,
      this.tokenEconomy,
      this.immunologicalMemory,
      this.cognitiveRepository
    );
    this.infrastructureManager = new InfrastructureManager(
      this.tokenEconomy,
      this.selfAwareness
    );
    this.repositoryManager = new RepositoryManager(this.security);
    this.specialtyManager = new SpecialtyManager(
      this.cognitiveRepository,
      this.versionManager,
      this.agentFactory,
      this.tokenEconomy
    );
    this.productManager = new ProductManager(
      this.specialtyManager,
      this.cognitiveRepository,
      this.tokenEconomy,
      this.selfAwareness
    );
    this.documentationGovernance = new DocumentationGovernance(
      this.versionManager,
      this.cognitiveRepository,
      this.selfAwareness
    );
    this.aiVisibilityEngine = new AIVisibilityEngine(
      this.cognitiveRepository,
      this.tokenEconomy
    );
    this.complianceManager = new ComplianceManager(
      this.security,
      this.cognitiveRepository,
      this.dataGovernance
    );

    this.logger.info('[Orchestrator] All modules initialized');
  }

  async processRequest(
    input: string,
    context?: Record<string, any>
  ): Promise<AgentResponse> {
    const logger = this.logger.child('Orchestrator');
    const executionId = context?.executionId || `exec_${Date.now()}`;
    logger.setExecutionId(executionId);

    logger.info('Processing request', {
      input: input.slice(0, 100),
      domain: context?.domain,
    });

    // 1. Verifica segurança (P-075, P-076)
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

    // 4. Deliberação (P-008, P-009)
    const deliberationRequest = {
      id: `delib_${Date.now()}`,
      intent: input,
      domain,
      input,
      context: context || {},
      criteria: {
        impact: this.estimateImpact(input),
        uncertainty: 0.5,
        risk: 0.3,
        reversibility: 0.7,
        cost: 0.4,
        dependencies: 0,
      },
    };

    const deliberation = await this.deliberationOrchestrator.deliberate(deliberationRequest);
    if (!deliberation.approved) {
      return {
        agentId: 'deliberation',
        content: `Deliberation rejected: ${deliberation.reasoning}`,
        metadata: { blocked: true, deliberation },
        timestamp: new Date(),
      };
    }

    // 5. Aloca orçamento de tokens (P-050)
    const budget = this.tokenEconomy.allocateBudget(executionId, 10000);
    logger.info(`Budget allocated: ${budget.allocated} tokens`);

    // 6. Verifica completude de capacidades (P-018, P-019)
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

    // 7. Executa o request
    const domainAgents = this.agentFactory.getAgentsByDomain(domain);
    if (domainAgents.length === 0) {
      throw new Error(`No agents found for domain: ${domain}`);
    }

    const plan = await this.planner.plan(input, domainAgents, { ...context, domain });
    const result = await this.executor.execute(plan, executionId);

    // 8. Registra uso de tokens (P-050)
    const cost = this.tokenEconomy.estimateCost(
      'gpt-4-turbo',
      result.metadata.totalTokens || 0,
      result.metadata.totalTokens || 0
    );
    this.tokenEconomy.recordUsage(executionId, cost);

    // 9. Reflexão (P-004)
    const reflection = await this.reflectionEngine.reflect(executionId, result);
    result.metadata.reflection = reflection;

    // 10. Ciclo de acumulação (P-040)
    if (result.success) {
      const cycle = this.accumulationCycle.startCycle(input);
      this.accumulationCycle.addStep(cycle.id, 'analysis', `Execução bem-sucedida: ${input.slice(0, 50)}`);
      this.accumulationCycle.addStep(cycle.id, 'validation', 'Resultado validado');
      this.accumulationCycle.addStep(cycle.id, 'generalization', 'Conhecimento generalizado');
      await this.accumulationCycle.completeCycle(cycle.id);
    }

    // 11. Registra evento na memória imunológica (P-020)
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

    // 12. Atualiza autopercepção (P-081)
    await this.selfAwareness.updateState();

    // 13. Atualiza dashboard (P-082)
    await this.metricsDashboard.updateMetrics();

    // 14. Registra auditoria (P-078)
    this.complianceManager.logAudit({
      userId: context?.userId || 'anonymous',
      action: 'process_request',
      resource: executionId,
      details: { domain, success: result.success, tokens: result.metadata.totalTokens },
      status: result.success ? 'success' : 'failure',
    });

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
        reflection: reflection.id,
        searchResult,
        deliberation,
      },
      timestamp: new Date(),
    };
  }

  /**
   * Nota de fidelidade: método ausente no material original enviado pelo
   * usuário (bloco "ARQUIVOS RESTANTES"), mas ainda referenciado pelo
   * scaffolding pré-existente da API (ChatController.processChatStream e
   * websocket.ts, do commit inicial). Reintroduzido aqui — mesma assinatura
   * e mesmo comportamento simplificado (delega para processRequest) que
   * existia no Orchestrator original do scaffolding — para não quebrar o
   * streaming de chat via SSE/WebSocket.
   */
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
    try {
      const result = await this.processRequest(input, context);
      callbacks.onComplete?.(result);
      return result;
    } catch (error: any) {
      callbacks.onError?.(error);
      throw error;
    }
  }

  private estimateImpact(input: string): number {
    const length = input.length;
    if (length > 500) return 7;
    if (length > 200) return 5;
    return 3;
  }

  // ===== Métodos de utilidade =====

  async getHealthReport(): Promise<string> {
    return this.selfAwareness.generateReport();
  }

  async getImmunologicalReport(): Promise<string> {
    return this.immunologicalMemory.generateReport();
  }

  async getOpportunityReport(): Promise<string> {
    return this.opportunityRadar.generateReport();
  }

  async getDashboardReport(): Promise<string> {
    return this.metricsDashboard.generateReport();
  }

  async getComplianceReport(): Promise<{
    passed: boolean;
    issues: string[];
    recommendations: string[];
    score: number;
  }> {
    return this.complianceManager.continuousSecurityAudit();
  }

  async getInfrastructureRecommendation(phase: 1 | 2 | 3): Promise<any> {
    return this.infrastructureManager.getInfrastructureRecommendation(phase);
  }

  async createSpecialty(data: any): Promise<any> {
    return this.specialtyManager.createSpecialty(data);
  }

  async createProduct(data: any): Promise<any> {
    return this.productManager.createProduct(data);
  }

  async submitAmendment(data: any): Promise<any> {
    return this.documentationGovernance.submitAmendment(data);
  }

  async registerDigitalAsset(data: any): Promise<any> {
    return this.aiVisibilityEngine.registerDigitalAsset(data);
  }

  async getSystemStatus(): Promise<any> {
    return {
      security: this.security.getSecurityStatus(),
      trust: this.trustManager.getCertifiedCompetences(),
      health: this.selfAwareness.getState()?.health,
      entropy: this.immunologicalMemory.getStats(),
      opportunities: this.opportunityRadar.getOpportunities({ status: 'new' }).length,
      workers: this.workerSupervisor.getStats(),
      attention: this.attentionEconomy.getStats(),
      compliance: await this.complianceManager.continuousSecurityAudit(),
      infrastructure: this.infrastructureManager.getStats(),
      repositories: this.repositoryManager.getStats(),
      specialties: this.specialtyManager.getStats(),
      products: this.productManager.getStats(),
      documents: this.documentationGovernance.getStats(),
      assets: this.aiVisibilityEngine.getStats(),
    };
  }
}
