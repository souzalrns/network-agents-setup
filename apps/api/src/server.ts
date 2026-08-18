import express from 'express';
import cors from 'cors';
import helmet from 'helmet';
import { createChatRoutes } from './routes/chat';
import { createExecutionRoutes } from './routes/executions';
import { createAgentRoutes } from './routes/agents';
import { createHitlRoutes } from './routes/hitl';
import { createMetricsRoutes } from './routes/metrics';
import { createHealthRoutes } from './routes/health';
import { errorHandler } from './middleware/errorHandler';
import { loggingMiddleware, tracingMiddleware } from '@network-agents/observability';
import { authMiddleware } from './middleware/auth';
import { Orchestrator } from '@network-agents/core';
import { HitlManager } from '@network-agents/core';
import { AgentFactory } from '@network-agents/core';
import { ExecutionService } from './services/ExecutionService';
export function createServer(
  orchestrator: Orchestrator,
  agentFactory: AgentFactory,
  hitlManager: HitlManager,
  executionService: ExecutionService
) {
  const app = express();
  app.use(helmet());
  app.use(cors());
  app.use(express.json({ limit: '10mb' }));
  app.use(loggingMiddleware);
  app.use(tracingMiddleware);
  app.use(authMiddleware);
  app.use('/chat', createChatRoutes(orchestrator, executionService));
  app.use('/executions', createExecutionRoutes(executionService));
  app.use('/agents', createAgentRoutes(agentFactory));
  app.use('/hitl', createHitlRoutes(hitlManager));
  app.use('/metrics', createMetricsRoutes(executionService));
  app.use('/health', createHealthRoutes());
  app.use(errorHandler);
  return app;
}
