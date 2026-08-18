import { Server } from 'http';
import { WebSocketServer } from '@network-agents/websocket';
import { Orchestrator } from '@network-agents/core';
import { HitlManager } from '@network-agents/core';
import { AgentFactory } from '@network-agents/core';
import { ExecutionService } from './services/ExecutionService';
import { getGlobalLogger } from '@network-agents/observability';
import { randomUUID } from 'crypto';
export function setupWebSocket(
  server: Server,
  orchestrator: Orchestrator,
  hitlManager: HitlManager,
  agentFactory: AgentFactory,
  executionService: ExecutionService
): WebSocketServer {
  const logger = getGlobalLogger();
  const wsServer = new WebSocketServer(server, { path: '/ws' });
  // Chat
  wsServer.on('chat:send', async (data: any, callback: any) => {
    try {
      const result = await orchestrator.processRequest(data.message, {
        domain: data.domain,
        userId: data.userId,
        conversationId: data.conversationId,
      });
      callback(result);
    } catch (error: any) {
      callback(null, { error: error.message });
    }
  });
  wsServer.on('chat:stream', async (data: any) => {
    const executionId = data.executionId || `exec_${Date.now()}`;
    try {
      wsServer.broadcast(`user:${data.userId}`, {
        id: randomUUID(),
        type: 'event',
        action: 'chat:stream:start',
        payload: { executionId },
        timestamp: new Date(),
      });
      await orchestrator.processRequestWithProgress(
        data.message,
        { domain: data.domain, userId: data.userId, conversationId: data.conversationId },
        {
          onStepStart: (step) => {
            wsServer.broadcast(`user:${data.userId}`, {
              id: randomUUID(),
              type: 'event',
              action: 'execution:step:start',
              payload: { executionId, step },
              timestamp: new Date(),
            });
          },
          onStepComplete: (step, result) => {
            wsServer.broadcast(`user:${data.userId}`, {
              id: randomUUID(),
              type: 'event',
              action: 'execution:step:complete',
              payload: { executionId, step, result },
              timestamp: new Date(),
            });
          },
          onComplete: (result) => {
            wsServer.broadcast(`user:${data.userId}`, {
              id: randomUUID(),
              type: 'event',
              action: 'execution:complete',
              payload: { executionId, result },
              timestamp: new Date(),
            });
          },
          onError: (error) => {
            wsServer.broadcast(`user:${data.userId}`, {
              id: randomUUID(),
              type: 'event',
              action: 'execution:error',
              payload: { executionId, error: error.message },
              timestamp: new Date(),
            });
          },
        }
      );
    } catch (error: any) {
      wsServer.broadcast(`user:${data.userId}`, {
        id: randomUUID(),
        type: 'event',
        action: 'execution:error',
        payload: { executionId, error: error.message },
        timestamp: new Date(),
      });
    }
  });
  // Execution
  wsServer.on('execution:start', async (data: any, callback: any) => {
    try {
      const executionId = randomUUID();
      orchestrator.processRequest(data.message, {
        domain: data.domain,
        userId: data.userId,
        conversationId: data.conversationId,
        executionId,
      }).then((result) => {
        wsServer.broadcast(`user:${data.userId}`, {
          id: randomUUID(),
          type: 'event',
          action: 'execution:completed',
          payload: { executionId, result },
          timestamp: new Date(),
        });
      }).catch((error) => {
        wsServer.broadcast(`user:${data.userId}`, {
          id: randomUUID(),
          type: 'event',
          action: 'execution:failed',
          payload: { executionId, error: error.message },
          timestamp: new Date(),
        });
      });
      callback({ executionId });
    } catch (error: any) {
      callback(null, { error: error.message });
    }
  });
  // HITL
  wsServer.on('hitl:list', async (data: any, callback: any) => {
    try {
      const pending = hitlManager.getPendingRequests(data.domain);
      callback(pending);
    } catch (error: any) {
      callback(null, { error: error.message });
    }
  });
  wsServer.on('hitl:approve', async (data: any, callback: any) => {
    try {
      const request = await hitlManager.approveRequest(data.hitlId, data.responderId, data.comment);
      wsServer.broadcast(`hitl:${request.domain}`, {
        id: randomUUID(),
        type: 'event',
        action: 'hitl:approved',
        payload: request,
        timestamp: new Date(),
      });
      callback(request);
    } catch (error: any) {
      callback(null, { error: error.message });
    }
  });
  wsServer.on('hitl:reject', async (data: any, callback: any) => {
    try {
      const request = await hitlManager.rejectRequest(data.hitlId, data.responderId, data.comment);
      wsServer.broadcast(`hitl:${request.domain}`, {
        id: randomUUID(),
        type: 'event',
        action: 'hitl:rejected',
        payload: request,
        timestamp: new Date(),
      });
      callback(request);
    } catch (error: any) {
      callback(null, { error: error.message });
    }
  });
  // Agent
  wsServer.on('agent:list', async (data: any, callback: any) => {
    try {
      let agents = agentFactory.getAllAgents();
      if (data.domain) {
        agents = agents.filter((a) => a.domain === data.domain);
      }
      callback(agents);
    } catch (error: any) {
      callback(null, { error: error.message });
    }
  });
  // System
  wsServer.on('system:status', (_data: any, callback: any) => {
    callback({
      status: 'healthy',
      connections: wsServer.getActiveConnections(),
      rooms: wsServer.getConnectionStats(),
      uptime: process.uptime(),
      timestamp: new Date(),
    });
  });
  wsServer.on('system:metrics', async (data: any, callback: any) => {
    try {
      const metrics = await executionService.getDetailedMetrics({
        domain: data.domain,
        startDate: data.startDate,
        endDate: data.endDate,
      });
      callback(metrics);
    } catch (error: any) {
      callback(null, { error: error.message });
    }
  });
  logger.info('WebSocket handlers registered');
  return wsServer;
}
