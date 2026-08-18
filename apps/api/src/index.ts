import { createServer } from './server';
import { setupWebSocket } from './websocket';
import { 
  AgentFactory, 
  Orchestrator, 
  Router, 
  Planner, 
  Executor,
  LLMService, 
  OpenAIProvider,
  HitlManager,
  SecurityManager,
  TokenEconomy,
  TrustManager,
  ArchitectureCouncil,
  SelfAwareness,
  OpportunityRadar,
  OrganizationalSimulator,
  ImmunologicalMemory,
  CompletenessValidator,
  DeliberationEngine
} from '@network-agents/core';
import { MemoryManager } from '@network-agents/memory';
import { ExecutionService } from './services/ExecutionService';
import { ToolRegistry } from '@network-agents/mcp';
import { createDatabaseTools, createFilesystemTools, createWebTools } from '@network-agents/mcp';
import { getGlobalLogger } from '@network-agents/observability';
import { Pool } from 'pg';
import { AGENT_CONFIGS } from '../../../config/agents.config';
async function main() {
  const logger = getGlobalLogger();
  const publicMode = process.env.PUBLIC_MODE === 'true';
  logger.info('Starting Network Agents API', {
    version: '1.0.0',
    environment: process.env.NODE_ENV || 'development',
  });
  // 1. Database Pool
  const dbPool = new Pool({
    connectionString: process.env.DATABASE_URL,
  });
  // 2. MCP Tool Registry
  const toolRegistry = new ToolRegistry([
    ...createDatabaseTools(dbPool),
    ...createFilesystemTools(process.env.FILESYSTEM_BASE || './data'),
    ...createWebTools(),
  ]);
  logger.info(`MCP Tools loaded: ${toolRegistry.listTools().length}`);
  // 3. LLM Provider
  const llmProvider = new OpenAIProvider(
    process.env.OPENAI_API_KEY!,
    process.env.DEFAULT_MODEL || 'gpt-4-turbo'
  );
  const llm = new LLMService(llmProvider);
  // 4. Agent Factory
  const agentFactory = new AgentFactory({ publicMode });
  AGENT_CONFIGS.forEach((config) => agentFactory.registerAgent(config));
  logger.info(`Agents loaded: ${agentFactory.getAllAgents().length}`);
  // 5. Memory Manager
  const memory = new MemoryManager({
    redisUrl: process.env.REDIS_URL,
    cacheTTL: 3600,
  });
  // 6. Security Manager
  const security = new SecurityManager({
    sessionTimeout: 24 * 60 * 60 * 1000,
    maxLoginAttempts: 5,
    rateLimitMax: 100,
  });
  // 7. Token Economy
  const tokenEconomy = new TokenEconomy({
    defaultBudget: 1000000,
    cacheTTL: 3600,
    minSavingsForOptimization: 1000,
  });
  // 8. Trust Manager
  const trustManager = new TrustManager();
  // 9. Architecture Council
  const architectureCouncil = new ArchitectureCouncil({
    autoApproveThreshold: 80,
    requireReviewForTypes: ['architecture_change', 'constitutional_change'],
  });
  // 10. Completeness Validator
  const completenessValidator = new CompletenessValidator({
    minCompletenessForOperational: 80,
    autoIngestEnabled: true,
  });
  // 11. Self Awareness
  const selfAwareness = new SelfAwareness({
    updateInterval: 60 * 1000,
    historySize: 100,
  });
  // 12. Immunological Memory
  const immunologicalMemory = new ImmunologicalMemory({
    maxEvents: 10000,
    autoArchiveAfter: 90,
    entropyThreshold: 50,
  });
  // 13. Opportunity Radar
  const opportunityRadar = new OpportunityRadar(selfAwareness, {
    scanInterval: 60 * 60 * 1000,
    minPotential: 50,
    maxDistance: 70,
  });
  // 14. Organizational Simulator
  const simulator = new OrganizationalSimulator(selfAwareness, {
    maxConcurrentSimulations: 5,
    defaultSteps: 100,
  });
  // 15. Deliberation Engine
  const deliberationEngine = new DeliberationEngine({
    operationalThreshold: 20,
    tacticalThreshold: 50,
    strategicThreshold: 75,
  });
  // 16. Hitl Manager (deve ser criado antes do Executor/Orchestrator, que dependem dele)
  const hitlManager = new HitlManager({
    autoExpireMinutes: parseInt(process.env.HITL_EXPIRE_MINUTES || '60'),
  });
  // 17. Core Components
  const router = new Router();
  const planner = new Planner(agentFactory, llm);
  const executor = new Executor(agentFactory, memory, llm, hitlManager);

  // 18. Orchestrator (com todos os módulos)
  const orchestrator = new Orchestrator(
    agentFactory,
    router,
    planner,
    executor,
    memory,
    security,
    tokenEconomy,
    trustManager,
    architectureCouncil,
    selfAwareness,
    immunologicalMemory,
    completenessValidator,
    deliberationEngine
  );
  // 19. Execution Service
  const executionService = new ExecutionService(memory);
  // 20. Server
  const app = createServer(
    orchestrator,
    agentFactory,
    hitlManager,
    executionService
  );
  const port = parseInt(process.env.PORT || '3000');
  const server = app.listen(port, () => {
    logger.info(`Server started on port ${port}`, {
      port,
      env: process.env.NODE_ENV,
      agents: agentFactory.getAllAgents().length,
    });
  });
  // 21. WebSocket
  setupWebSocket(server, orchestrator, hitlManager, agentFactory, executionService);
  // 22. Primeiro scan do radar
  opportunityRadar.scanAll().catch((error) => {
    logger.error('Initial opportunity scan failed', { error: error.message });
  });
  // 23. Primeira atualização da autopercepção
  selfAwareness.updateState().catch((error) => {
    logger.error('Initial self-awareness update failed', { error: error.message });
  });
  // 24. Graceful shutdown
  const shutdown = async () => {
    logger.info('Shutting down...');
    opportunityRadar.stop();
    await memory.disconnect();
    await dbPool.end();
    server.close(() => process.exit(0));
  };
  process.on('SIGTERM', shutdown);
  process.on('SIGINT', shutdown);
}
main().catch((error) => {
  console.error('Fatal error:', error);
  process.exit(1);
});
