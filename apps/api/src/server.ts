import express from 'express';
import cors from 'cors';
import helmet from 'helmet';
import rateLimit from 'express-rate-limit';
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
  const apiRateLimiter = rateLimit({
    windowMs: 60_000,
    limit: 60,
    standardHeaders: true,
    legacyHeaders: false,
  });
  // crossOriginResourcePolicy: 'same-origin' (omissão do helmet) contradiz o
  // cors() aberto logo a seguir -- browsers bloqueiam a leitura cross-origin
  // mesmo com CORS a permitir, silenciosamente. Ver EXECUTION-PROMPTS.md A20/S13.
  app.use(helmet({ crossOriginResourcePolicy: { policy: 'cross-origin' } }));
  app.use(cors());
  app.use(express.json({ limit: '10mb' }));
  app.use(loggingMiddleware);
  app.use(tracingMiddleware);
  app.use(authMiddleware);
  // A16: espelha o rate_limit(caller, limit=60, window=60.0) do lado Python
  // (mcp/plan_runner/mcp_plan_runner/policy.py:129) -- 60 pedidos/60s. Nao e
  // equivalente 1:1: o Python tem um "caller" (identidade explicita do
  // cliente MCP); esta API usa um API_KEY unico partilhado por todos os
  // clientes (auth.ts), sem conceito de identidade por chamador -- por IP
  // e o unico eixo disponivel. Nao aplicado a /health (checks de infra).
  app.use((req, res, next) => {
    if (req.path === '/health') return next();
    return apiRateLimiter(req, res, next);
  });
  app.use('/chat', createChatRoutes(orchestrator, executionService));
  app.use('/executions', createExecutionRoutes(executionService));
  app.use('/agents', createAgentRoutes(agentFactory));
  app.use('/hitl', createHitlRoutes(hitlManager));
  app.use('/metrics', createMetricsRoutes(executionService));
  app.use('/health', createHealthRoutes());
  app.use(errorHandler);
  return app;
}
