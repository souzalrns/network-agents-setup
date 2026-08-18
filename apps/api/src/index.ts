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
  // 6. Hitl Manager (deve ser criado antes do Executor/Orchestrator, que dependem dele)
  const hitlManager = new HitlManager({
    autoExpireMinutes: parseInt(process.env.HITL_EXPIRE_MINUTES || '60'),
  });
  // 7. Core Components
  const router = new Router();
  const planner = new Planner(agentFactory, llm);
  const executor = new Executor(agentFactory, memory, llm, hitlManager);

  // 8. Orchestrator (instancia internamente todos os módulos de governança,
  // economia, segurança, observabilidade, produtos e conformidade)
  const orchestrator = new Orchestrator(
    agentFactory,
    router,
    planner,
    executor,
    memory,
    hitlManager
  );
  // 9. Execution Service
  const executionService = new ExecutionService(memory);
  // 10. Server
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
  // 11. WebSocket
  setupWebSocket(server, orchestrator, hitlManager, agentFactory, executionService);
  // 12. Primeiro scan do radar e primeira atualização de autopercepção
  orchestrator.opportunityRadar.scanAll().catch((error: any) => {
    logger.error('Initial opportunity scan failed', { error: error.message });
  });
  orchestrator.selfAwareness.updateState().catch((error: any) => {
    logger.error('Initial self-awareness update failed', { error: error.message });
  });
  // 13. Atualiza dashboard
  orchestrator.metricsDashboard.updateMetrics().catch((error: any) => {
    logger.error('Initial metrics update failed', { error: error.message });
  });
  // 14. Graceful shutdown
  const shutdown = async () => {
    logger.info('Shutting down...');
    orchestrator.opportunityRadar.stop();
    orchestrator.workerSupervisor.stop();
    orchestrator.metricsDashboard.stop();
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
